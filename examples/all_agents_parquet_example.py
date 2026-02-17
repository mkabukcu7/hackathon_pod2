"""
Example: Using all agents with Parquet data
Demonstrates how each agent loads and uses raw Parquet data
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.customer_profile_agent import CustomerProfileAgent
from agents.sales_intelligence_agent import SalesIntelligenceAgent
from agents.retention_insights_agent import RetentionInsightsAgent
from agents.environmental_agent import EnvironmentalAgent
from agents.weather_agent import WeatherAgent
from agents.hazard_risk_agent import HazardRiskAgent


def main():
    """Demonstrate all agents using Parquet data"""
    
    print("=" * 70)
    print("AGENT PARQUET DATA INTEGRATION EXAMPLE")
    print("=" * 70)
    
    # Initialize all agents with Parquet data
    print("\n1. Initializing Customer Profile Agent with Parquet data...")
    customer_agent = CustomerProfileAgent(use_parquet=True)
    if customer_agent.parquet_data:
        print(f"   [OK] Loaded {len(customer_agent.parquet_data['customers_df'])} customers")
        print(f"   [OK] Loaded {len(customer_agent.parquet_data['policies_df'])} policies")
        print(f"   [OK] Loaded {len(customer_agent.parquet_data['claims_df'])} claims")
    
    print("\n2. Initializing Sales Intelligence Agent with Parquet data...")
    sales_agent = SalesIntelligenceAgent(use_parquet=True)
    if sales_agent.parquet_data:
        print(f"   [OK] Loaded {len(sales_agent.parquet_data['customers_df'])} customers")
        print(f"   [OK] Loaded {len(sales_agent.parquet_data['policies_df'])} policies")
        print(f"   [OK] Loaded {len(sales_agent.parquet_data['activity_df'])} activity records")
    
    print("\n3. Initializing Retention Insights Agent with Parquet data...")
    retention_agent = RetentionInsightsAgent(use_parquet=True)
    if retention_agent.parquet_data:
        print(f"   [OK] Loaded {len(retention_agent.parquet_data['customers_df'])} customers")
        print(f"   [OK] Loaded {len(retention_agent.parquet_data['features_df'])} feature records")
    
    print("\n4. Initializing Environmental Agent with Parquet data...")
    env_agent = EnvironmentalAgent(use_parquet=True)
    if env_agent.external_signals_df is not None:
        print(f"   [OK] Loaded {len(env_agent.external_signals_df)} external signal records")
    
    print("\n5. Initializing Weather Agent with Parquet data...")
    weather_agent = WeatherAgent(use_parquet=True)
    if weather_agent.external_signals_df is not None:
        print(f"   [OK] Loaded {len(weather_agent.external_signals_df)} external signal records")
    
    print("\n6. Initializing Hazard Risk Agent with Parquet data...")
    hazard_agent = HazardRiskAgent(use_parquet=True)
    if hazard_agent.external_signals_df is not None:
        print(f"   [OK] Loaded {len(hazard_agent.external_signals_df)} external signal records")
    
    print("\n" + "=" * 70)
    print("AGENT STATUS SUMMARY")
    print("=" * 70)
    
    agents_status = [
        ("Customer Profile Agent", customer_agent.use_parquet),
        ("Sales Intelligence Agent", sales_agent.use_parquet),
        ("Retention Insights Agent", retention_agent.use_parquet),
        ("Environmental Agent", env_agent.use_parquet),
        ("Weather Agent", weather_agent.use_parquet),
        ("Hazard Risk Agent", hazard_agent.use_parquet),
    ]
    
    for agent_name, using_parquet in agents_status:
        status = "[YES] Using Parquet" if using_parquet else "[NO] Fallback Mode"
        print(f"{agent_name:.<50} {status}")
    
    print("\n" + "=" * 70)
    print("All agents successfully initialized with Parquet data!")
    print("=" * 70)


if __name__ == '__main__':
    main()
