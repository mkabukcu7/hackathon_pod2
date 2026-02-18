"""
Agent Orchestrator - Manages and coordinates multiple agents
Uses Azure OpenAI GPT-4o-mini for intelligent query routing and natural language understanding.
"""
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

from agents.weather_agent import WeatherAgent
from agents.environmental_agent import EnvironmentalAgent
from agents.azure_agent import AzureAgent
from services.openai_service import chat_completion, is_available as openai_available

logger = logging.getLogger(__name__)

ROUTING_SYSTEM_PROMPT = """You are an intelligent query router for an insurance analytics platform.
Analyze the user's query and return a JSON object describing which agents and actions to invoke.

Available agents and their actions:
1. "weather" — actions: "current_weather", "forecast"
2. "environmental" — actions: "pollution", "ecosystem", "water_quality"
3. "azure" — actions: "resource_groups", "cost_analysis", "security", "service_health"

Return JSON with this exact structure (no markdown, no explanation):
{
  "agents": [
    {"name": "<agent_name>", "actions": ["<action1>", "<action2>"], "params": {}}
  ],
  "summary": "<one-sentence summary of user intent>"
}

Rules:
- You may route to MULTIPLE agents if the query spans multiple domains.
- If the query is unclear or doesn't match any agent, return {"agents": [], "summary": "..."}.
- For weather queries, include a "location" key in params if the user specifies one.
- For environmental queries, include "ecosystem_type" or "water_body" in params if mentioned.
- For azure queries, include "resource_group" in params if mentioned.
"""


class AgentOrchestrator:
    """Orchestrates multiple agents to handle complex queries.
    
    Uses GPT-4o-mini for intelligent natural-language routing when available,
    with keyword-based fallback when Azure OpenAI is not configured.
    """
    
    def __init__(self):
        """Initialize the agent orchestrator"""
        self.weather_agent = WeatherAgent()
        self.environmental_agent = EnvironmentalAgent()
        self.azure_agent = AzureAgent()
        self._ai_routing = openai_available()
        if self._ai_routing:
            logger.info("Orchestrator: AI-powered routing enabled (GPT-4o-mini)")
        else:
            logger.info("Orchestrator: Using keyword-based routing (Azure OpenAI not configured)")

    # ------------------------------------------------------------------ #
    # GPT-4o-mini powered routing
    # ------------------------------------------------------------------ #
    def _route_with_ai(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use GPT-4o-mini to understand user intent and decide routing."""
        messages = [
            {"role": "system", "content": ROUTING_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
        raw = chat_completion(messages, temperature=0.0, max_tokens=512,
                              response_format={"type": "json_object"})
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("AI routing returned invalid JSON, falling back to keywords")
            return None

    # ------------------------------------------------------------------ #
    # Keyword fallback routing (original logic)
    # ------------------------------------------------------------------ #
    def _route_with_keywords(self, query: str) -> List[Dict[str, Any]]:
        """Keyword-based routing — used when Azure OpenAI is unavailable."""
        query_lower = query.lower()
        agents: List[Dict[str, Any]] = []

        if any(kw in query_lower for kw in ["weather", "temperature", "forecast", "rain", "wind"]):
            actions = ["forecast"] if "forecast" in query_lower else ["current_weather"]
            agents.append({"name": "weather", "actions": actions, "params": {}})

        if any(kw in query_lower for kw in ["pollution", "air quality", "environmental", "ecosystem", "water quality"]):
            actions = []
            if "pollution" in query_lower or "air quality" in query_lower:
                actions.append("pollution")
            if "ecosystem" in query_lower:
                actions.append("ecosystem")
            if "water" in query_lower:
                actions.append("water_quality")
            if not actions:
                actions.append("pollution")
            agents.append({"name": "environmental", "actions": actions, "params": {}})

        if any(kw in query_lower for kw in ["azure", "resources", "cost", "security", "service health"]):
            actions = []
            if "resource" in query_lower:
                actions.append("resource_groups")
            if "cost" in query_lower:
                actions.append("cost_analysis")
            if "security" in query_lower:
                actions.append("security")
            if "health" in query_lower or "status" in query_lower:
                actions.append("service_health")
            if not actions:
                actions.append("resource_groups")
            agents.append({"name": "azure", "actions": actions, "params": {}})

        return agents

    # ------------------------------------------------------------------ #
    # Main entry point
    # ------------------------------------------------------------------ #
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user query by routing to appropriate agents.
        
        Uses GPT-4o-mini for NLU routing when available, falls back to keywords.
        """
        context = context or {}
        results: Dict[str, Any] = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "agents_used": [],
            "routing_method": "ai" if self._ai_routing else "keyword",
            "results": {}
        }

        # --- Routing decision ---
        routing: Optional[Dict[str, Any]] = None
        if self._ai_routing:
            routing = self._route_with_ai(query, context)

        if routing and routing.get("agents"):
            agent_list = routing["agents"]
            results["ai_summary"] = routing.get("summary", "")
        else:
            agent_list = self._route_with_keywords(query)
            results["routing_method"] = "keyword"

        # --- Execute agent actions ---
        for agent_info in agent_list:
            name = agent_info["name"]
            actions = agent_info.get("actions", [])
            params = {**context, **agent_info.get("params", {})}

            if name == "weather":
                results["agents_used"].append("weather")
                location = params.get("location", "London")
                if "forecast" in actions:
                    results["results"]["weather_forecast"] = self.weather_agent.get_forecast(location)
                if "current_weather" in actions or not actions:
                    results["results"]["current_weather"] = self.weather_agent.get_current_weather(location)

            elif name == "environmental":
                results["agents_used"].append("environmental")
                location = params.get("location", "London")
                if "pollution" in actions:
                    results["results"]["pollution"] = self.environmental_agent.get_pollution_data(location)
                if "ecosystem" in actions:
                    ecosystem_type = params.get("ecosystem_type", "forest")
                    results["results"]["ecosystem"] = self.environmental_agent.get_ecosystem_health(ecosystem_type, location)
                if "water_quality" in actions:
                    water_body = params.get("water_body", "River Thames")
                    results["results"]["water_quality"] = self.environmental_agent.get_water_quality(water_body, location)

            elif name == "azure":
                results["agents_used"].append("azure")
                if "resource_groups" in actions:
                    results["results"]["resource_groups"] = self.azure_agent.get_resource_groups()
                if "cost_analysis" in actions:
                    results["results"]["cost_analysis"] = self.azure_agent.get_cost_analysis()
                if "security" in actions:
                    results["results"]["security"] = self.azure_agent.get_security_recommendations()
                if "service_health" in actions:
                    results["results"]["service_health"] = self.azure_agent.get_service_health()

        # Fallback message when nothing matched
        if not results["agents_used"]:
            results["message"] = ("I can help you with weather data, environmental information, "
                                  "and Azure resource management. Please provide more specific details.")

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
