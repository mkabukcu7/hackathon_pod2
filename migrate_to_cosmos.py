"""
Migrate Parquet data to Azure Cosmos DB (NoSQL API)
Uploads all 7 Parquet files into their respective containers.
Uses concurrent threads for high throughput.
"""
import os
import sys
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from datetime import datetime
from azure.cosmos import CosmosClient, exceptions
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────
ENDPOINT = os.getenv("COSMOS_DB_ENDPOINT")
DATABASE = os.getenv("COSMOS_DB_DATABASE", "insurance_data")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

MAX_WORKERS = 25        # Concurrent upload threads per table
PROGRESS_INTERVAL = 500 # Print progress every N records

# Mapping: parquet file → (container name, partition key field, id field)
TABLES = [
    ("bronze_producers_raw.parquet",          "producers",          "ProducerId",  "ProducerId"),
    ("bronze_customers_raw.parquet",          "customers",          "CustomerId",  "CustomerId"),
    ("bronze_policies_raw.parquet",           "policies",           "CustomerId",  "PolicyId"),
    ("bronze_claims_raw.parquet",             "claims",             "CustomerId",  "ClaimId"),
    ("bronze_customer_features_raw.parquet",  "customer_features",  "CustomerId",  "CustomerId"),
    ("bronze_external_signals_raw.parquet",   "external_signals",   "CustomerId",  "SignalId"),
    ("bronze_producer_activity_raw.parquet",  "producer_activity",  "CustomerId",  "ActivityId"),
]


def clean_value(val):
    """Convert pandas/numpy types to JSON-serializable Python types."""
    if pd.isna(val):
        return None
    if hasattr(val, 'isoformat'):  # datetime/Timestamp
        return val.isoformat()
    if hasattr(val, 'item'):  # numpy scalar
        return val.item()
    return val


def upsert_doc(container, doc):
    """Upsert a single document. Returns (True, None) on success or (False, error)."""
    try:
        container.upsert_item(doc)
        return True, None
    except exceptions.CosmosHttpResponseError as e:
        return False, e.message
    except Exception as e:
        return False, str(e)


def migrate_table(client, parquet_file, container_name, partition_key, id_field):
    """Upload a single Parquet file to its Cosmos DB container using concurrent threads."""
    file_path = os.path.join(DATA_DIR, parquet_file)
    if not os.path.exists(file_path):
        print(f"  ⚠ File not found: {file_path}, skipping")
        return 0

    df = pd.read_parquet(file_path)
    total = len(df)
    print(f"\n📦 {container_name}: {total:,} records from {parquet_file}")

    database = client.get_database_client(DATABASE)
    container = database.get_container_client(container_name)

    # Prepare all documents first
    docs = []
    now_str = datetime.utcnow().isoformat()
    for _, row in df.iterrows():
        doc = {k: clean_value(v) for k, v in row.items()}
        raw_id = doc.get(id_field)
        doc["id"] = str(raw_id) if raw_id else str(uuid.uuid4())
        doc["document_type"] = container_name
        doc["migrated_at"] = now_str
        docs.append(doc)

    # Upload concurrently
    success = 0
    errors = 0
    error_samples = []
    lock = threading.Lock()
    start = time.time()
    completed = 0

    def upload_one(doc):
        return upsert_doc(container, doc)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(upload_one, doc): i for i, doc in enumerate(docs)}
        for future in as_completed(futures):
            ok, err = future.result()
            with lock:
                if ok:
                    success += 1
                else:
                    errors += 1
                    if len(error_samples) < 5:
                        error_samples.append(err)
                completed += 1
                if completed % PROGRESS_INTERVAL == 0 or completed == total:
                    elapsed = time.time() - start
                    rate = completed / elapsed if elapsed > 0 else 0
                    pct = completed / total * 100
                    print(f"  ✅ {completed:,}/{total:,} ({pct:.1f}%) — {rate:.0f} docs/sec — errors: {errors}", end="\r")

    elapsed = time.time() - start
    rate = success / elapsed if elapsed > 0 else 0
    print(f"\n  ✅ Done: {success:,} uploaded, {errors} errors in {elapsed:.1f}s ({rate:.0f} docs/sec)")
    for err in error_samples:
        print(f"  ❌ Sample error: {err}")
    return success


def main():
    if not ENDPOINT:
        print("❌ COSMOS_DB_ENDPOINT must be set in .env")
        sys.exit(1)
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        print("❌ AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    print("=" * 60)
    print("🚀 Parquet → Cosmos DB Migration (Entra ID Auth)")
    print(f"   Endpoint:  {ENDPOINT}")
    print(f"   Database:  {DATABASE}")
    print(f"   Tables:    {len(TABLES)}")
    print(f"   Workers:   {MAX_WORKERS} threads per table")
    print("=" * 60)

    credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    client = CosmosClient(ENDPOINT, credential=credential)

    # Verify database exists
    try:
        client.get_database_client(DATABASE).read()
        print(f"✅ Database '{DATABASE}' found")
    except Exception as e:
        print(f"❌ Cannot access database '{DATABASE}': {e}")
        sys.exit(1)

    total_uploaded = 0
    overall_start = time.time()

    for parquet_file, container_name, partition_key, id_field in TABLES:
        uploaded = migrate_table(client, parquet_file, container_name, partition_key, id_field)
        total_uploaded += uploaded

    overall_elapsed = time.time() - overall_start
    print("\n" + "=" * 60)
    print(f"🎉 Migration complete!")
    print(f"   Total records: {total_uploaded:,}")
    print(f"   Total time:    {overall_elapsed:.1f}s ({overall_elapsed/60:.1f} min)")
    print(f"   Avg rate:      {total_uploaded/overall_elapsed:.0f} docs/sec")
    print("=" * 60)


if __name__ == "__main__":
    main()
