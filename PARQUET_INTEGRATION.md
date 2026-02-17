# Parquet Data Integration Guide

## Overview

All agents in this project have been updated to support loading raw data from Parquet files. This enables efficient handling of large datasets while maintaining backward compatibility with mock data and external APIs.

## Available Parquet Files

The `/data` folder contains the following Parquet datasets:

| File | Purpose | Rows |
|------|---------|------|
| `bronze_customers_raw.parquet` | Customer profiles and demographics | ~10K |
| `bronze_policies_raw.parquet` | Insurance policies and coverage details | ~50K |
| `bronze_claims_raw.parquet` | Historical claim records | ~5K |
| `bronze_customer_features_raw.parquet` | Computed features for machine learning | ~10K |
| `bronze_external_signals_raw.parquet` | Environmental and external data signals | ~1K |
| `bronze_producers_raw.parquet` | Producer/agent information | ~100 |
| `bronze_producer_activity_raw.parquet` | Producer activity logs | ~2K |

## Using Parquet Data

### 1. Basic Loading with `parquet_loader`

```python
from utils.parquet_loader import (
    get_customers,
    get_policies,
    get_claims,
    get_customer_features,
    get_external_signals,
    get_producers,
    get_producer_activity
)

# Load data
customers_df = get_customers()
policies_df = get_policies()
claims_df = get_claims()

# Access data
print(f"Loaded {len(customers_df)} customers")
print(customers_df.columns)
```

### 2. Query by Customer ID

```python
from utils.parquet_loader import query_by_customer_id

# Get customer data
result = query_by_customer_id('customer_123', 'customers')
if result:
    print(result[0])  # Returns dict with customer data
```

### 3. Memory Management

```python
from utils.parquet_loader import get_cache_info, clear_cache

# Check cache usage
cache_info = get_cache_info()
for filename, info in cache_info.items():
    print(f"{filename}: {info['memory_usage_mb']:.2f} MB")

# Clear cache if needed
clear_cache()
```

## Updated Agents

### Customer Profile Agent

**Usage:**
```python
from agents.customer_profile_agent import CustomerProfileAgent

# Initialize with Parquet (default)
agent = CustomerProfileAgent(use_parquet=True)

# Access Parquet data
if agent.parquet_data:
    customers_df = agent.parquet_data['customers_df']
    policies_df = agent.parquet_data['policies_df']
    claims_df = agent.parquet_data['claims_df']
```

**Features:**
- Loads customer, policy, and claims data from Parquet
- Falls back to Cosmos DB if Parquet unavailable
- Falls back to mock data if both unavailable

### Sales Intelligence Agent

**Usage:**
```python
from agents.sales_intelligence_agent import SalesIntelligenceAgent

# Initialize with Parquet (default)
agent = SalesIntelligenceAgent(use_parquet=True)

# Access Parquet data
if agent.parquet_data:
    customers_df = agent.parquet_data['customers_df']
    policies_df = agent.parquet_data['policies_df']
    activity_df = agent.parquet_data['activity_df']
```

**Features:**
- Loads customer, policy, and producer activity data
- Uses for generating cross-sell and upsell recommendations

### Retention Insights Agent

**Usage:**
```python
from agents.retention_insights_agent import RetentionInsightsAgent

# Initialize with Parquet (default)
agent = RetentionInsightsAgent(use_parquet=True)

# Access Parquet data
if agent.parquet_data:
    customers_df = agent.parquet_data['customers_df']
    policies_df = agent.parquet_data['policies_df']
    claims_df = agent.parquet_data['claims_df']
    features_df = agent.parquet_data['features_df']
```

**Features:**
- Loads customer retention and feature data
- Analyzes trends and provides retention insights

### Environmental Agent

**Usage:**
```python
from agents.environmental_agent import EnvironmentalAgent

# Initialize with Parquet (default)
agent = EnvironmentalAgent(use_parquet=True)

# Access external signals
if agent.external_signals_df is not None:
    signals_df = agent.external_signals_df
```

**Features:**
- Loads external environmental signals from Parquet
- Falls back to mock data if unavailable

### Weather Agent

**Usage:**
```python
from agents.weather_agent import WeatherAgent

# Initialize with Parquet (default)
agent = WeatherAgent(use_parquet=True)

# Access external signals
if agent.external_signals_df is not None:
    signals_df = agent.external_signals_df
```

**Features:**
- Loads weather and disaster risk signals from Parquet
- Integrates with OpenWeatherMap API

### Hazard Risk Agent

**Usage:**
```python
from agents.hazard_risk_agent import HazardRiskAgent

# Initialize with Parquet (default)
agent = HazardRiskAgent(use_parquet=True)

# Access external signals
if agent.external_signals_df is not None:
    signals_df = agent.external_signals_df
```

**Features:**
- Loads hazard risk signals from Parquet
- Assesses flood, wildfire, and earthquake risks

## Examples

### Example 1: Load and Inspect Parquet Data

```bash
cd examples
python parquet_example.py
```

### Example 2: Initialize All Agents with Parquet Data

```bash
cd examples
python all_agents_parquet_example.py
```

## Performance Considerations

### Caching

All Parquet files are cached in memory after first load. This provides:
- **Faster access**: Subsequent reads use cached data
- **Efficient memory**: One copy per dataframe in the process

### Cache Management

```python
# Get cache information
from utils.parquet_loader import get_cache_info
info = get_cache_info()

# Clear cache if memory is tight
from utils.parquet_loader import clear_cache
clear_cache()
```

### Memory Usage

Total Parquet dataset size: ~5.5 MB
Approximate in-memory usage after loading all files: ~20-30 MB (depending on pandas overhead)

## Backward Compatibility

All agents maintain backward compatibility:

1. **Parquet First** (default): Attempts to load Parquet data
2. **Cosmos DB Second**: Falls back to Cosmos DB if configured
3. **Mock Data Last**: Uses built-in mock data as final fallback

This ensures agents work even if Parquet files are unavailable.

## Adding New Parquet Data

To add new Parquet files:

1. Place the `.parquet` file in the `/data` folder
2. Add a helper function to `src/utils/parquet_loader.py`:

```python
def get_my_data() -> pd.DataFrame:
    """Load my data from bronze_my_data_raw.parquet"""
    return load_parquet('bronze_my_data_raw.parquet')
```

3. Import and use in your agent:

```python
from utils.parquet_loader import get_my_data

df = get_my_data()
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pyarrow'"

Install required dependencies:
```bash
pip install pyarrow pandas
```

### "Parquet file not found"

Ensure:
1. The `.parquet` file is in the `/data` folder
2. The filename matches exactly (case-sensitive)
3. The file is a valid Parquet file

### High Memory Usage

If memory usage is high:
```python
from utils.parquet_loader import clear_cache

# Clear unused cached data
clear_cache()

# Or disable caching for specific loads
load_parquet('bronze_customers_raw.parquet', use_cache=False)
```

## API Reference

### `load_parquet(filename, use_cache=True)`

Load a Parquet file with optional caching.

**Parameters:**
- `filename` (str): Name of the Parquet file
- `use_cache` (bool): Whether to use in-memory cache

**Returns:** `pd.DataFrame`

### `query_by_customer_id(customer_id, table='customers')`

Query a customer by ID across different tables.

**Parameters:**
- `customer_id` (str): The customer ID
- `table` (str): Which table to query ('customers', 'policies', 'claims', 'features')

**Returns:** List of dict records or None

### `get_cache_info()`

Get information about cached Parquet files.

**Returns:** Dict with cache statistics

### `clear_cache()`

Clear all cached Parquet data.

**Returns:** None
