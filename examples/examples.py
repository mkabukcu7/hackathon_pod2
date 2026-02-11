"""
Example usage of the Multi-Agent System
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from orchestrator import AgentOrchestrator
from agents import WeatherAgent, EnvironmentalAgent, AzureAgent


def example_weather_queries():
    """Example weather agent queries"""
    print("\n" + "="*60)
    print("Weather Agent Examples")
    print("="*60)
    
    weather_agent = WeatherAgent()
    
    # Get current weather
    print("\n1. Current weather in London:")
    result = weather_agent.get_current_weather("London")
    print(json.dumps(result, indent=2))
    
    # Get weather forecast
    print("\n2. Weather forecast for New York:")
    result = weather_agent.get_forecast("New York", days=3)
    print(json.dumps(result, indent=2))


def example_environmental_queries():
    """Example environmental agent queries"""
    print("\n" + "="*60)
    print("Environmental Agent Examples")
    print("="*60)
    
    env_agent = EnvironmentalAgent()
    
    # Get pollution data
    print("\n1. Pollution data for Paris:")
    result = env_agent.get_pollution_data("Paris")
    print(json.dumps(result, indent=2))
    
    # Get climate data
    print("\n2. Climate data for Europe:")
    result = env_agent.get_climate_data("Europe")
    print(json.dumps(result, indent=2))
    
    # Get ecosystem health
    print("\n3. Forest ecosystem health in Amazon:")
    result = env_agent.get_ecosystem_health("forest", "Amazon")
    print(json.dumps(result, indent=2))


def example_azure_queries():
    """Example Azure agent queries"""
    print("\n" + "="*60)
    print("Azure Agent Examples")
    print("="*60)
    
    azure_agent = AzureAgent()
    
    # Get service health
    print("\n1. Azure service health:")
    result = azure_agent.get_service_health()
    print(json.dumps(result, indent=2))
    
    # Get cost analysis
    print("\n2. Cost analysis:")
    result = azure_agent.get_cost_analysis()
    print(json.dumps(result, indent=2))
    
    # Get security recommendations
    print("\n3. Security recommendations:")
    result = azure_agent.get_security_recommendations()
    print(json.dumps(result, indent=2))


def example_orchestrator_queries():
    """Example orchestrator queries"""
    print("\n" + "="*60)
    print("Orchestrator Examples")
    print("="*60)
    
    orchestrator = AgentOrchestrator()
    
    # Process natural language queries
    queries = [
        "What's the weather in Seattle?",
        "Show me pollution levels in Tokyo",
        "What are my Azure costs?",
        "Get me a weather forecast for London and environmental data"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: '{query}'")
        result = orchestrator.process_query(query, {"location": "Seattle"})
        print(json.dumps(result, indent=2))
        print()


def example_comprehensive_report():
    """Example comprehensive report"""
    print("\n" + "="*60)
    print("Comprehensive Report Example")
    print("="*60)
    
    orchestrator = AgentOrchestrator()
    
    print("\nGenerating comprehensive report for London...")
    result = orchestrator.get_comprehensive_report("London")
    print(json.dumps(result, indent=2))


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Multi-Agent System - Examples")
    print("="*60)
    
    print("\nNote: Some features require API keys to be configured in .env file")
    print("Weather API: OpenWeatherMap API key")
    print("Azure: Azure credentials")
    
    # Run examples
    try:
        example_weather_queries()
    except Exception as e:
        print(f"Weather examples error: {e}")
    
    try:
        example_environmental_queries()
    except Exception as e:
        print(f"Environmental examples error: {e}")
    
    try:
        example_azure_queries()
    except Exception as e:
        print(f"Azure examples error: {e}")
    
    try:
        example_orchestrator_queries()
    except Exception as e:
        print(f"Orchestrator examples error: {e}")
    
    try:
        example_comprehensive_report()
    except Exception as e:
        print(f"Comprehensive report error: {e}")
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
