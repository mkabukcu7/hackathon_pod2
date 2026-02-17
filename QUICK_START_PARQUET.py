"""
Quick Start: Using Agents with Parquet Data

This guide shows how to integrate the agents with Parquet data
for the original tasks (customer lookup, recommendations, retention analysis, etc.)
"""

# Example 1: Customer Profile Lookup
# ===================================

from src.agents.customer_profile_agent import CustomerProfileAgent

# Initialize agent with Parquet data (default)
agent = CustomerProfileAgent(use_parquet=True)

# Access customer data
if agent.parquet_data:
    customers_df = agent.parquet_data['customers_df']
    policies_df = agent.parquet_data['policies_df']
    
    # Quick lookup by index
    customer = customers_df.iloc[0]
    print(f"Customer ID: {customer['CustomerId']}")
    print(f"Region: {customer['Region']}")
    print(f"Age: {customer['Age']}")


# Example 2: Sales Recommendations
# ==================================

from src.agents.sales_intelligence_agent import SalesIntelligenceAgent

# Initialize agent with Parquet data
sales_agent = SalesIntelligenceAgent(use_parquet=True)

# Access customer and policy data
if sales_agent.parquet_data:
    customers = sales_agent.parquet_data['customers_df']
    policies = sales_agent.parquet_data['policies_df']
    
    # Analyze customer 0
    customer_data = customers.iloc[0].to_dict()
    customer_policies = policies[policies['CustomerId'] == customer_data['CustomerId']]
    
    print(f"Found {len(customer_policies)} policies for {customer_data['CustomerId']}")
    
    # Generate recommendations (existing method can be used)
    # recommendations = sales_agent.get_cross_sell_recommendations(...)


# Example 3: Retention Analysis
# ===============================

from src.agents.retention_insights_agent import RetentionInsightsAgent

# Initialize agent with Parquet data
retention_agent = RetentionInsightsAgent(use_parquet=True)

# Access all retention data
if retention_agent.parquet_data:
    customers = retention_agent.parquet_data['customers_df']
    policies = retention_agent.parquet_data['policies_df']
    claims = retention_agent.parquet_data['claims_df']
    features = retention_agent.parquet_data['features_df']
    
    print(f"Analyzing {len(customers)} customers")
    print(f"With {len(policies)} policies")
    print(f"And {len(claims)} claims")
    print(f"Using {len(features)} feature vectors")


# Example 4: Environmental & Weather Risk
# =========================================

from src.agents.environmental_agent import EnvironmentalAgent
from src.agents.weather_agent import WeatherAgent
from src.agents.hazard_risk_agent import HazardRiskAgent

# Initialize agents with Parquet data
env_agent = EnvironmentalAgent(use_parquet=True)
weather_agent = WeatherAgent(use_parquet=True)
hazard_agent = HazardRiskAgent(use_parquet=True)

# All agents have external signals data
if env_agent.external_signals_df is not None:
    signals = env_agent.external_signals_df
    
    # Analyze by signal type
    print(f"Total signals: {len(signals)}")
    print(f"Signal types: {signals['SignalType'].unique()}")
    
    # Get signals by confidence
    high_confidence = signals[signals['Confidence'] > 0.8]
    print(f"High confidence signals: {len(high_confidence)}")


# Example 5: Direct Parquet Loading
# ===================================

from src.utils.parquet_loader import (
    get_customers,
    get_policies,
    get_claims,
    get_customer_features,
    get_external_signals
)

# Load any data directly
customers_df = get_customers()  # 60,000 customers
policies_df = get_policies()    # 90,000 policies
claims_df = get_claims()        # 19,946 claims
features_df = get_customer_features()  # 60,000 features
signals_df = get_external_signals()    # 30,000 signals

print(f"Loaded {len(customers_df)} customers from Parquet")


# Example 6: Integration with FastAPI
# =====================================

# Update src/api.py to use Parquet data:

# from agents.customer_profile_agent import CustomerProfileAgent
# from agents.sales_intelligence_agent import SalesIntelligenceAgent

# # Initialize agents with Parquet (default)
# customer_agent = CustomerProfileAgent(use_parquet=True)
# sales_agent = SalesIntelligenceAgent(use_parquet=True)

# @app.get("/api/customers/search/{customer_id}")
# async def search_customer(customer_id: str):
#     """Search customer by ID using Parquet data"""
#     if customer_agent.parquet_data:
#         customers_df = customer_agent.parquet_data['customers_df']
#         result = customers_df[customers_df['CustomerId'] == customer_id]
#         if len(result) > 0:
#             return result.iloc[0].to_dict()
#     return {"error": "Customer not found"}

# @app.get("/api/recommendations/{customer_id}")
# async def get_recommendations(customer_id: str):
#     """Get sales recommendations using Parquet data"""
#     if sales_agent.parquet_data:
#         # Access policies and generate recommendations
#         # ...
#         pass


# Example 7: Performance Monitoring
# ==================================

from src.utils.parquet_loader import get_cache_info, clear_cache

# Check cache usage
cache_info = get_cache_info()
for filename, info in cache_info.items():
    print(f"{filename}: {info['memory_usage_mb']:.2f} MB")

# Clear cache if needed
clear_cache()


# Summary
# =======
# 
# All agents now support Parquet data with:
# - Automatic loading on initialization
# - In-memory caching for fast access
# - Fallback to Cosmos DB/mock data if unavailable
# - Easy DataFrame access for custom analysis
#
# Total data available:
# - 60,000 customers
# - 90,000 policies
# - 19,946 claims
# - 60,000 ML features
# - 30,000 external signals
# - ~200K total records
#
# This enables:
# ✓ Rapid customer lookup
# ✓ Cross-sell/up-sell recommendations
# ✓ Retention & churn analysis
# ✓ Environmental & weather risk assessment
# ✓ Natural disaster risk scoring
