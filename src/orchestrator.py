"""
Agent Orchestrator - Manages and coordinates multiple agents
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from agents.weather_agent import WeatherAgent
from agents.environmental_agent import EnvironmentalAgent
from agents.azure_agent import AzureAgent


class AgentOrchestrator:
    """Orchestrates multiple agents to handle complex queries"""
    
    def __init__(self):
        """Initialize the agent orchestrator"""
        self.weather_agent = WeatherAgent()
        self.environmental_agent = EnvironmentalAgent()
        self.azure_agent = AzureAgent()
        
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user query by routing to appropriate agents
        
        Args:
            query: User query string
            context: Optional context dictionary with additional parameters
            
        Returns:
            Dictionary containing results from relevant agents
        """
        query_lower = query.lower()
        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "agents_used": [],
            "results": {}
        }
        
        context = context or {}
        
        # Determine which agents to invoke based on query content
        if any(keyword in query_lower for keyword in ["weather", "temperature", "forecast", "rain", "wind"]):
            results["agents_used"].append("weather")
            location = context.get("location", "London")
            
            if "forecast" in query_lower:
                results["results"]["weather_forecast"] = self.weather_agent.get_forecast(location)
            else:
                results["results"]["current_weather"] = self.weather_agent.get_current_weather(location)
                
        if any(keyword in query_lower for keyword in ["pollution", "air quality", "environmental", "ecosystem", "water quality"]):
            results["agents_used"].append("environmental")
            location = context.get("location", "London")
            
            if "pollution" in query_lower or "air quality" in query_lower:
                results["results"]["pollution"] = self.environmental_agent.get_pollution_data(location)
            if "ecosystem" in query_lower:
                ecosystem_type = context.get("ecosystem_type", "forest")
                results["results"]["ecosystem"] = self.environmental_agent.get_ecosystem_health(ecosystem_type, location)
            if "water" in query_lower:
                water_body = context.get("water_body", "River Thames")
                results["results"]["water_quality"] = self.environmental_agent.get_water_quality(water_body, location)
                
        if any(keyword in query_lower for keyword in ["azure", "resources", "cost", "security", "service health"]):
            results["agents_used"].append("azure")
            
            if "resource" in query_lower:
                results["results"]["resource_groups"] = self.azure_agent.get_resource_groups()
            if "cost" in query_lower:
                results["results"]["cost_analysis"] = self.azure_agent.get_cost_analysis()
            if "security" in query_lower:
                results["results"]["security"] = self.azure_agent.get_security_recommendations()
            if "health" in query_lower or "status" in query_lower:
                results["results"]["service_health"] = self.azure_agent.get_service_health()
                
        # If no specific agents were triggered, provide a general response
        if not results["agents_used"]:
            results["message"] = "I can help you with weather data, environmental information, and Azure resource management. Please provide more specific details."
            
        return results
        
    def get_comprehensive_report(
        self, 
        location: str,
        resource_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive report combining data from all agents
        
        Args:
            location: Location for weather and environmental data
            resource_group: Azure resource group name (optional)
            
        Returns:
            Dictionary containing comprehensive data from all agents
        """
        report = {
            "location": location,
            "report_date": datetime.now().isoformat(),
            "weather": {},
            "environmental": {},
            "azure": {}
        }
        
        # Gather weather data
        try:
            report["weather"]["current"] = self.weather_agent.get_current_weather(location)
            report["weather"]["forecast"] = self.weather_agent.get_forecast(location, days=3)
        except Exception as e:
            report["weather"]["error"] = str(e)
            
        # Gather environmental data
        try:
            report["environmental"]["pollution"] = self.environmental_agent.get_pollution_data(location)
            report["environmental"]["climate"] = self.environmental_agent.get_climate_data(location)
            report["environmental"]["alerts"] = self.environmental_agent.get_environmental_alerts(location)
        except Exception as e:
            report["environmental"]["error"] = str(e)
            
        # Gather Azure data
        try:
            report["azure"]["service_health"] = self.azure_agent.get_service_health()
            report["azure"]["cost_analysis"] = self.azure_agent.get_cost_analysis(resource_group)
            report["azure"]["security"] = self.azure_agent.get_security_recommendations(resource_group)
        except Exception as e:
            report["azure"]["error"] = str(e)
            
        return report
        
    def get_available_capabilities(self) -> Dict[str, List[str]]:
        """Get list of available capabilities from all agents
        
        Returns:
            Dictionary mapping agent names to their capabilities
        """
        return {
            "weather_agent": [
                "get_current_weather",
                "get_forecast",
                "get_air_quality"
            ],
            "environmental_agent": [
                "get_pollution_data",
                "get_climate_data",
                "get_ecosystem_health",
                "get_water_quality",
                "get_environmental_alerts"
            ],
            "azure_agent": [
                "get_resource_groups",
                "get_resources_in_group",
                "get_resource_metrics",
                "get_cost_analysis",
                "get_service_health",
                "get_security_recommendations"
            ]
        }
