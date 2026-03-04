"""
Cosmos DB Data Repository — Shared data access layer for Azure Functions.

Provides a singleton CosmosDBRepository that all function endpoints use.
Mirrors the methods from the original cosmos_db_service.py but designed
for serverless (stateless per-invocation, connection reuse via singleton).
"""
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# All containers in the insurance_data database
CONTAINERS = [
    "customers", "policies", "claims", "customer_features",
    "external_signals", "producers", "producer_activity"
]

# Singleton instance
_repository_instance = None


def get_repository():
    """Get or create the singleton repository instance."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = CosmosDBRepository()
    return _repository_instance


class CosmosDBRepository:
    """Data access layer for Azure Cosmos DB — used by all Azure Function endpoints."""

    def __init__(self):
        self.endpoint = os.getenv("COSMOS_DB_ENDPOINT")
        self.database_name = os.getenv("COSMOS_DB_DATABASE", "insurance_data")
        self.client = None
        self.database = None
        self._containers: Dict[str, Any] = {}
        self._connect_error: Optional[str] = None
        self._connect()

    # ── Connection ───────────────────────────────────────────────────

    def _connect(self):
        """Establish Cosmos DB connection with 3-tier auth."""
        if not self.endpoint:
            logger.warning("COSMOS_DB_ENDPOINT not set — repository will be offline.")
            return

        try:
            from azure.cosmos import CosmosClient
            from azure.identity import ClientSecretCredential, DefaultAzureCredential

            credential = None
            cosmos_scope = "https://cosmos.azure.com/.default"

            # Priority 1: Service principal
            tenant_id = os.getenv("AZURE_TENANT_ID")
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")

            if all([tenant_id, client_id, client_secret]):
                try:
                    service_principal_credential = ClientSecretCredential(tenant_id, client_id, client_secret)
                    service_principal_credential.get_token(cosmos_scope)
                    credential = service_principal_credential
                    logger.info("Cosmos DB auth: service principal")
                except Exception as e:
                    logger.warning(f"Cosmos DB service principal auth failed: {e}")

            if credential is None:
                # Priority 2: Managed identity / az login
                try:
                    default_credential = DefaultAzureCredential()
                    default_credential.get_token(cosmos_scope)
                    credential = default_credential
                    logger.info("Cosmos DB auth: DefaultAzureCredential")
                except Exception as e:
                    logger.warning(f"Cosmos DB DefaultAzureCredential auth failed: {e}")

            if credential is None:
                # Priority 3: Key-based
                key = os.getenv("COSMOS_DB_KEY")
                if key:
                    self.client = CosmosClient(self.endpoint, key)
                    logger.info("Cosmos DB auth: key-based")

            if credential and not self.client:
                self.client = CosmosClient(self.endpoint, credential=credential)

            if self.client:
                self.database = self.client.get_database_client(self.database_name)
                for name in CONTAINERS:
                    self._containers[name] = self.database.get_container_client(name)
                logger.info(f"Connected to Cosmos DB: {len(self._containers)} containers")

        except Exception as e:
            self._connect_error = str(e)
            logger.error(f"Failed to connect to Cosmos DB: {e}")

    def is_connected(self) -> bool:
        if self.client is None or len(self._containers) == 0:
            # Retry connection if previously failed
            logger.info("Retrying Cosmos DB connection...")
            self.client = None
            self.database = None
            self._containers = {}
            self._connect_error = None
            self._connect()
        return self.client is not None and len(self._containers) > 0

    # ── Generic query ────────────────────────────────────────────────

    def query_container(
        self,
        container_name: str,
        query: str,
        parameters: Optional[List[Dict]] = None,
        max_items: int = 100,
    ) -> List[Dict[str, Any]]:
        """Run a SQL query against any container."""
        container = self._containers.get(container_name)
        if not container:
            return []
        try:
            return list(
                container.query_items(
                    query=query,
                    parameters=parameters or [],
                    enable_cross_partition_query=True,
                    max_item_count=max_items,
                )
            )
        except Exception as e:
            logger.error(f"Error querying {container_name}: {e}")
            return []

    # ── Customer operations ──────────────────────────────────────────

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        results = self.query_container(
            "customers",
            "SELECT * FROM c WHERE c.id = @cid",
            [{"name": "@cid", "value": customer_id}],
            max_items=1,
        )
        return results[0] if results else None

    def search_customers(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Flexible customer search by ID, state, region, ZIP, etc."""
        q_upper = query.strip().upper()
        q_lower = query.strip().lower()

        # Exact customer ID
        if q_upper.startswith("C") and q_upper[1:].isdigit():
            results = self.query_container(
                "customers",
                "SELECT * FROM c WHERE c.CustomerId = @q",
                [{"name": "@q", "value": q_upper}],
                max_items=limit,
            )
            return self._attach_customer_policy_aggregates(results)

        # 5-digit ZIP
        if q_upper.isdigit() and len(q_upper) == 5:
            results = self.query_container(
                "customers",
                "SELECT * FROM c WHERE c.ZipCode = @q",
                [{"name": "@q", "value": q_upper}],
                max_items=limit,
            )
            return self._attach_customer_policy_aggregates(results)

        # Free-text
        sql = (
            "SELECT * FROM c WHERE "
            "CONTAINS(LOWER(c.CustomerId), @q) OR "
            "CONTAINS(LOWER(c.State), @q) OR "
            "CONTAINS(LOWER(c.Region), @q) OR "
            "CONTAINS(LOWER(c.IncomeBand), @q) OR "
            "CONTAINS(LOWER(c.MaritalStatus), @q) OR "
            "CONTAINS(c.ZipCode, @q)"
        )
        results = self.query_container(
            "customers", sql, [{"name": "@q", "value": q_lower}], max_items=limit
        )
        return self._attach_customer_policy_aggregates(results)

    def _attach_customer_policy_aggregates(self, customer_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach policy_count and total_premium to customer search documents."""
        if not customer_docs:
            return customer_docs

        enriched_docs: List[Dict[str, Any]] = []
        for doc in customer_docs:
            customer_id = doc.get("CustomerId")
            if not customer_id:
                enriched_docs.append(doc)
                continue

            policies = self.get_customer_policies(customer_id)
            enriched_doc = dict(doc)
            enriched_doc["policy_count"] = len(policies)
            enriched_doc["total_premium"] = float(sum(float(policy.get("Premium", 0) or 0) for policy in policies))
            enriched_docs.append(enriched_doc)

        return enriched_docs

    # ── Related entities ─────────────────────────────────────────────

    def get_customer_policies(self, customer_id: str) -> List[Dict[str, Any]]:
        return self.query_container(
            "policies",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}],
        )

    def get_customer_claims(self, customer_id: str) -> List[Dict[str, Any]]:
        return self.query_container(
            "claims",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}],
        )

    def get_customer_features(self, customer_id: str) -> Optional[Dict[str, Any]]:
        results = self.query_container(
            "customer_features",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}],
            max_items=1,
        )
        return results[0] if results else None

    def get_customer_signals(self, customer_id: str) -> List[Dict[str, Any]]:
        return self.query_container(
            "external_signals",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}],
        )

    def get_producer(self, producer_id: str) -> Optional[Dict[str, Any]]:
        results = self.query_container(
            "producers",
            "SELECT * FROM c WHERE c.ProducerId = @pid",
            [{"name": "@pid", "value": producer_id}],
            max_items=1,
        )
        return results[0] if results else None

    def get_producer_activity(self, customer_id: str) -> List[Dict[str, Any]]:
        return self.query_container(
            "producer_activity",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}],
        )

    # ── Full profile (multi-container join) ──────────────────────────

    def get_full_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        customer = self.get_customer(customer_id)
        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        profile = {
            "customer": customer,
            "policies": self.get_customer_policies(customer_id),
            "claims": self.get_customer_claims(customer_id),
            "features": self.get_customer_features(customer_id),
            "signals": self.get_customer_signals(customer_id),
            "activity": self.get_producer_activity(customer_id),
        }

        producer_id = customer.get("ProducerId")
        if producer_id:
            profile["producer"] = self.get_producer(producer_id)

        return profile

    # ── Aggregations ─────────────────────────────────────────────────

    def _scalar(self, container: str, query: str, default=0):
        results = self.query_container(container, query)
        return results[0] if results and results[0] is not None else default

    def get_stats(self) -> Dict[str, Any]:
        """Return all dashboard statistics in one call."""
        return {
            "customer_count": self._scalar("customers", "SELECT VALUE COUNT(1) FROM c"),
            "policy_count": self._scalar("policies", "SELECT VALUE COUNT(1) FROM c"),
            "active_policy_count": self._scalar(
                "policies",
                "SELECT VALUE COUNT(1) FROM c WHERE c.PolicyStatus = 'Active'",
            ),
            "claim_count": self._scalar("claims", "SELECT VALUE COUNT(1) FROM c"),
            "total_premium": float(
                self._scalar("policies", "SELECT VALUE SUM(c.Premium) FROM c", 0.0)
            ),
            "avg_premium": float(
                self._scalar("policies", "SELECT VALUE AVG(c.Premium) FROM c", 0.0)
            ),
            "states": self._get_distinct("customers", "State"),
            "regions": self._get_distinct("customers", "Region"),
        }

    def _get_distinct(self, container: str, field: str) -> List[str]:
        results = self.query_container(
            container,
            f"SELECT DISTINCT VALUE c.{field} FROM c WHERE IS_DEFINED(c.{field})",
            max_items=100,
        )
        return sorted([v for v in results if v])
