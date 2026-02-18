"""
Parquet Data Loader - Utilities for loading and caching Parquet files
Provides efficient access to raw data in Parquet format
"""
import os
from typing import Dict, Optional, Any
import pandas as pd
from functools import lru_cache

# Cache for loaded Parquet files
_parquet_cache: Dict[str, pd.DataFrame] = {}

# Correct US state → region mapping (US Census Bureau regions)
_STATE_TO_REGION: Dict[str, str] = {
    # Northeast
    'CT': 'Northeast', 'ME': 'Northeast', 'MA': 'Northeast', 'NH': 'Northeast',
    'NJ': 'Northeast', 'NY': 'Northeast', 'PA': 'Northeast', 'RI': 'Northeast',
    'VT': 'Northeast',
    # Midwest
    'IL': 'Midwest', 'IN': 'Midwest', 'IA': 'Midwest', 'KS': 'Midwest',
    'MI': 'Midwest', 'MN': 'Midwest', 'MO': 'Midwest', 'NE': 'Midwest',
    'ND': 'Midwest', 'OH': 'Midwest', 'SD': 'Midwest', 'WI': 'Midwest',
    # Southeast
    'AL': 'Southeast', 'AR': 'Southeast', 'DE': 'Southeast', 'FL': 'Southeast',
    'GA': 'Southeast', 'KY': 'Southeast', 'LA': 'Southeast', 'MD': 'Southeast',
    'MS': 'Southeast', 'NC': 'Southeast', 'SC': 'Southeast', 'TN': 'Southeast',
    'VA': 'Southeast', 'WV': 'Southeast', 'DC': 'Southeast',
    # Southwest
    'AZ': 'Southwest', 'NM': 'Southwest', 'OK': 'Southwest', 'TX': 'Southwest',
    # West
    'AK': 'West', 'CA': 'West', 'CO': 'West', 'HI': 'West', 'ID': 'West',
    'MT': 'West', 'NV': 'West', 'OR': 'West', 'UT': 'West', 'WA': 'West',
    'WY': 'West',
}


def _get_data_path(filename: str) -> str:
    """Get the absolute path to a data file in the data folder"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, 'data', filename)


def load_parquet(filename: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Load a Parquet file from the data folder
    
    Args:
        filename: Name of the Parquet file (e.g., 'bronze_customers_raw.parquet')
        use_cache: Whether to cache the loaded data in memory
        
    Returns:
        DataFrame containing the Parquet data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid Parquet file
    """
    # Check cache first
    if use_cache and filename in _parquet_cache:
        return _parquet_cache[filename]
    
    file_path = _get_data_path(filename)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Parquet file not found at {file_path}")
    
    if not filename.endswith('.parquet'):
        raise ValueError(f"File must be a Parquet file, got: {filename}")
    
    try:
        df = pd.read_parquet(file_path)
        if use_cache:
            _parquet_cache[filename] = df
        return df
    except Exception as e:
        raise ValueError(f"Failed to load Parquet file {filename}: {str(e)}")


def get_customers() -> pd.DataFrame:
    """Load customer data from bronze_customers_raw.parquet.
    
    Corrects the Region column to match each customer's State
    using standard US Census Bureau region definitions.
    """
    df = load_parquet('bronze_customers_raw.parquet')
    # Fix region based on state (source data has random region assignment)
    if 'State' in df.columns and 'Region' in df.columns:
        df = df.copy()
        df['Region'] = df['State'].map(_STATE_TO_REGION).fillna(df['Region'])
        # Update the cache with the corrected data
        _parquet_cache['bronze_customers_raw.parquet'] = df
    return df


def get_policies() -> pd.DataFrame:
    """Load policy data from bronze_policies_raw.parquet"""
    return load_parquet('bronze_policies_raw.parquet')


def get_claims() -> pd.DataFrame:
    """Load claims data from bronze_claims_raw.parquet"""
    return load_parquet('bronze_claims_raw.parquet')


def get_customer_features() -> pd.DataFrame:
    """Load customer features data from bronze_customer_features_raw.parquet"""
    return load_parquet('bronze_customer_features_raw.parquet')


def get_external_signals() -> pd.DataFrame:
    """Load external signals data from bronze_external_signals_raw.parquet"""
    return load_parquet('bronze_external_signals_raw.parquet')


def get_producers() -> pd.DataFrame:
    """Load producer data from bronze_producers_raw.parquet"""
    return load_parquet('bronze_producers_raw.parquet')


def get_producer_activity() -> pd.DataFrame:
    """Load producer activity data from bronze_producer_activity_raw.parquet"""
    return load_parquet('bronze_producer_activity_raw.parquet')


def clear_cache() -> None:
    """Clear the Parquet cache to free memory"""
    global _parquet_cache
    _parquet_cache.clear()


def get_cache_info() -> Dict[str, Any]:
    """Get information about cached Parquet files"""
    info = {}
    for filename, df in _parquet_cache.items():
        info[filename] = {
            'shape': df.shape,
            'columns': list(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        }
    return info


def query_by_customer_id(customer_id: str, table: str = 'customers') -> Optional[Dict[str, Any]]:
    """
    Query a record by customer ID
    
    Args:
        customer_id: The customer ID to search for
        table: Which table to query ('customers', 'policies', 'claims', 'features')
        
    Returns:
        Dictionary with the matching row(s), or None if not found
    """
    try:
        if table == 'customers':
            df = get_customers()
            result = df[df['customer_id'] == customer_id]
        elif table == 'policies':
            df = get_policies()
            result = df[df['customer_id'] == customer_id]
        elif table == 'claims':
            df = get_claims()
            result = df[df['customer_id'] == customer_id]
        elif table == 'features':
            df = get_customer_features()
            result = df[df['customer_id'] == customer_id]
        else:
            return None
        
        if len(result) == 0:
            return None
        
        return result.to_dict('records')
    except Exception as e:
        print(f"Error querying {table}: {str(e)}")
        return None
