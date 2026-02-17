"""
Example: Loading and using Parquet data in agents
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.parquet_loader import (
    get_customers,
    get_policies,
    get_claims,
    get_customer_features,
    get_external_signals,
    get_producers,
    get_producer_activity,
    query_by_customer_id,
    get_cache_info
)


def main():
    """Demonstrate Parquet data loading"""
    
    print("=" * 60)
    print("PARQUET DATA LOADER EXAMPLE")
    print("=" * 60)
    
    # Load customers data
    print("\n1. Loading customer data...")
    customers_df = get_customers()
    print(f"   Loaded {len(customers_df)} customers")
    print(f"   Columns: {list(customers_df.columns)[:5]}...")
    
    # Load policies data
    print("\n2. Loading policies data...")
    policies_df = get_policies()
    print(f"   Loaded {len(policies_df)} policies")
    print(f"   Columns: {list(policies_df.columns)[:5]}...")
    
    # Load claims data
    print("\n3. Loading claims data...")
    claims_df = get_claims()
    print(f"   Loaded {len(claims_df)} claims")
    print(f"   Columns: {list(claims_df.columns)[:5]}...")
    
    # Load customer features
    print("\n4. Loading customer features...")
    features_df = get_customer_features()
    print(f"   Loaded {len(features_df)} feature records")
    print(f"   Columns: {list(features_df.columns)[:5]}...")
    
    # Load external signals
    print("\n5. Loading external signals...")
    signals_df = get_external_signals()
    print(f"   Loaded {len(signals_df)} signal records")
    print(f"   Columns: {list(signals_df.columns)[:5]}...")
    
    # Load producers
    print("\n6. Loading producers...")
    producers_df = get_producers()
    print(f"   Loaded {len(producers_df)} producers")
    print(f"   Columns: {list(producers_df.columns)[:5]}...")
    
    # Load producer activity
    print("\n7. Loading producer activity...")
    activity_df = get_producer_activity()
    print(f"   Loaded {len(activity_df)} activity records")
    print(f"   Columns: {list(activity_df.columns)[:5]}...")
    
    # Show cache info
    print("\n8. Cache Information:")
    cache_info = get_cache_info()
    for filename, info in cache_info.items():
        print(f"   {filename}:")
        print(f"     - Shape: {info['shape']}")
        print(f"     - Memory: {info['memory_usage_mb']:.2f} MB")
    
    # Example query
    print("\n9. Example Query - Get first customer ID...")
    if len(customers_df) > 0:
        first_customer_id = customers_df.iloc[0]['customer_id']
        result = query_by_customer_id(first_customer_id, 'customers')
        if result:
            print(f"   Found customer: {first_customer_id}")
            print(f"   Data: {result[0]}")
    
    print("\n" + "=" * 60)
    print("All data loaded successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
