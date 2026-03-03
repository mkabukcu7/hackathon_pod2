"""
MCP Server — Insurance Intelligence Platform

Exposes all agent capabilities as MCP tools so they can be consumed by
any MCP-compatible client (VS Code Copilot, Claude Desktop, Logic Apps, etc.).

Run:
    python src/mcp_server.py                   # stdio transport (default)
    python src/mcp_server.py --transport sse   # SSE transport for remote clients
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from fastmcp import FastMCP
from services.data_layer_client import DataLayerClient

from agents import (
    CustomerProfileAgent,
    SalesIntelligenceAgent,
    RetentionInsightsAgent,
    HazardRiskAgent,
    WeatherAgent,
    EnvironmentalAgent,
)

logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────────

mcp = FastMCP(
    "Insurance Intelligence Platform",
    description=(
        "Multi-agent insurance analytics platform providing customer profiles, "
        "sales intelligence, retention insights, hazard risk assessment, "
        "weather data, and environmental monitoring."
    ),
)

# ── Lazy-init agents (created on first tool call) ────────────────────

_agents = {}


def _get_agent(name: str):
    """Lazy-initialize agents so startup is fast and connections are reused."""
    if name not in _agents:
        if name == "customer":
            _agents[name] = CustomerProfileAgent(use_data_layer=True)
        elif name == "sales":
            _agents[name] = SalesIntelligenceAgent(use_data_layer=True)
        elif name == "retention":
            _agents[name] = RetentionInsightsAgent(use_data_layer=True)
        elif name == "hazard":
            _agents[name] = HazardRiskAgent(use_cosmos_db=True)
        elif name == "weather":
            _agents[name] = WeatherAgent()
        elif name == "environmental":
            _agents[name] = EnvironmentalAgent()
    return _agents[name]


def _get_platform_health() -> dict:
    """Collect runtime health/readiness signals for MCP clients."""
    data_layer_connected = False
    data_layer_error = None
    try:
        client = DataLayerClient()
        data_layer_connected = client.is_connected()
    except Exception as e:
        data_layer_error = str(e)

    return {
        "status": "healthy" if data_layer_connected else "degraded",
        "components": {
            "mcp_server": {
                "ready": True,
                "server": "Insurance Intelligence Platform",
            },
            "data_layer": {
                "ready": data_layer_connected,
                "base_url_set": bool(os.getenv("DATA_LAYER_URL")),
                "error": data_layer_error,
            },
            "agents": {
                "initialized": sorted(list(_agents.keys())),
                "count": len(_agents),
            },
            "env": {
                "azure_openai_endpoint_set": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
                "azure_maps_api_key_set": bool(os.getenv("AZURE_MAPS_API_KEY")),
            },
        },
    }


def _build_logic_apps_customer_packet(customer_id: str) -> dict:
    """Build a deterministic payload for workflow systems like Logic Apps."""
    request_id = str(uuid4())
    packet = {
        "request_id": request_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "customer_id": customer_id,
        "status": "success",
        "data": {},
        "errors": [],
    }

    customer_agent = _get_agent("customer")
    sales_agent = _get_agent("sales")
    retention_agent = _get_agent("retention")
    hazard_agent = _get_agent("hazard")

    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        packet["status"] = "failed"
        packet["errors"].append({"component": "customer_profile", "message": profile.get("error")})
        return packet

    packet["data"]["profile"] = profile

    try:
        packet["data"]["customer_insights"] = retention_agent.get_customer_insights(customer_id, profile)
    except Exception as e:
        packet["errors"].append({"component": "customer_insights", "message": str(e)})

    try:
        packet["data"]["retention_score"] = retention_agent.get_retention_score(customer_id, profile)
    except Exception as e:
        packet["errors"].append({"component": "retention_score", "message": str(e)})

    try:
        packet["data"]["cross_sell"] = sales_agent.get_cross_sell_recommendations(customer_id, profile)
    except Exception as e:
        packet["errors"].append({"component": "cross_sell", "message": str(e)})

    zip_code = profile.get("zip")
    if isinstance(zip_code, str) and len(zip_code) == 5:
        try:
            packet["data"]["flood_risk"] = hazard_agent.get_flood_risk(zip_code)
        except Exception as e:
            packet["errors"].append({"component": "flood_risk", "message": str(e)})

    if packet["errors"]:
        packet["status"] = "partial_success"

    packet["meta"] = {
        "errors_count": len(packet["errors"]),
        "components_returned": sorted(list(packet["data"].keys())),
    }
    return packet


# ═══════════════════════════════════════════════════════════════════════
#  CUSTOMER PROFILE TOOLS
# ═══════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_platform_health() -> str:
    """Get MCP platform health/readiness for orchestration and automation clients.

    Returns:
        JSON object with overall status, data-layer connectivity, initialized
        agent count, and key environment readiness flags.
    """
    return json.dumps(_get_platform_health(), default=str, indent=2)


@mcp.tool()
def search_customers(query: str, limit: int = 50) -> str:
    """Search for insurance customers by ID, name, state, region, ZIP code, or income band.

    Args:
        query: Search term — customer ID (e.g. C0000481), state (Texas),
               region (Southwest), ZIP (75001), or income band (High).
        limit: Maximum number of results to return (1-200).

    Returns:
        JSON array of matching customer summaries with id, state, region,
        policy count, and lifetime value.
    """
    agent = _get_agent("customer")
    results = agent.search_customer(query, limit=limit)
    return json.dumps(results, default=str, indent=2)


@mcp.tool()
def get_customer_profile(customer_id: str) -> str:
    """Get a complete insurance customer profile including demographics,
    policies, claims, risk score, satisfaction, and AI-generated summary.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with full customer profile.
    """
    agent = _get_agent("customer")
    profile = agent.get_customer_profile(customer_id)
    return json.dumps(profile, default=str, indent=2)


@mcp.tool()
def get_customer_policies(customer_id: str) -> str:
    """Get all insurance policies for a customer.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with policies array, total premium, and policy count.
    """
    agent = _get_agent("customer")
    result = agent.get_customer_policies(customer_id)
    return json.dumps(result, default=str, indent=2)


@mcp.tool()
def get_customer_claims(customer_id: str) -> str:
    """Get claim history for a customer.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with claim history, total claims count, and total claimed amount.
    """
    agent = _get_agent("customer")
    result = agent.get_customer_claims(customer_id)
    return json.dumps(result, default=str, indent=2)


@mcp.tool()
def get_customer_stats() -> str:
    """Get overall portfolio statistics — total customers, policies,
    claims, premiums, and breakdowns by state/region.

    Returns:
        JSON object with aggregate statistics.
    """
    agent = _get_agent("customer")
    stats = agent.get_stats()
    return json.dumps(stats, default=str, indent=2)


# ═══════════════════════════════════════════════════════════════════════
#  SALES INTELLIGENCE TOOLS
# ═══════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_cross_sell_recommendations(customer_id: str) -> str:
    """Generate cross-sell recommendations for a customer — suggests
    insurance products the customer doesn't currently have.

    Uses GPT-4o-mini for AI-powered recommendations with rule-based fallback.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with product recommendations, confidence scores,
        potential premiums, bundle discounts, and talking points.
    """
    customer_agent = _get_agent("customer")
    sales_agent = _get_agent("sales")
    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        return json.dumps(profile)
    return json.dumps(
        sales_agent.get_cross_sell_recommendations(customer_id, profile),
        default=str, indent=2,
    )


@mcp.tool()
def get_upsell_recommendations(customer_id: str) -> str:
    """Generate up-sell recommendations — suggests coverage upgrades
    for a customer's existing policies.

    Uses GPT-4o-mini for AI-powered recommendations with rule-based fallback.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with upgrade recommendations, additional premiums,
        benefits, and talking points per policy.
    """
    customer_agent = _get_agent("customer")
    sales_agent = _get_agent("sales")
    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        return json.dumps(profile)
    return json.dumps(
        sales_agent.get_upsell_recommendations(customer_id, profile),
        default=str, indent=2,
    )


@mcp.tool()
def generate_talking_points(customer_id: str, context: str = "general") -> str:
    """Generate personalized talking points for a customer interaction.

    Uses GPT-4o-mini for AI-generated talking points with template fallback.

    Args:
        customer_id: Customer ID (e.g. C0000481).
        context: Interaction context — "general", "sales", or "retention".

    Returns:
        JSON object with greeting, relationship highlights, conversation
        starters, key facts, objection handlers, and closing statement.
    """
    customer_agent = _get_agent("customer")
    sales_agent = _get_agent("sales")
    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        return json.dumps(profile)
    return json.dumps(
        sales_agent.generate_talking_points(customer_id, profile, context),
        default=str, indent=2,
    )


# ═══════════════════════════════════════════════════════════════════════
#  RETENTION INSIGHTS TOOLS
# ═══════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_customer_insights(customer_id: str) -> str:
    """Get AI-powered insights about a customer — satisfaction analysis,
    claims patterns, engagement level, renewal timing, and value assessment.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with categorized insights, health score, and recommended actions.
    """
    customer_agent = _get_agent("customer")
    retention_agent = _get_agent("retention")
    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        return json.dumps(profile)
    return json.dumps(
        retention_agent.get_customer_insights(customer_id, profile),
        default=str, indent=2,
    )


@mcp.tool()
def get_customer_trends(customer_id: str) -> str:
    """Analyze customer trends over time — engagement, premium, satisfaction,
    and risk trajectories with predictions.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with trend directions, monthly data, key observations,
        and retention/churn/upsell predictions.
    """
    customer_agent = _get_agent("customer")
    retention_agent = _get_agent("retention")
    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        return json.dumps(profile)
    return json.dumps(
        retention_agent.get_customer_trends(customer_id, profile),
        default=str, indent=2,
    )


@mcp.tool()
def get_retention_score(customer_id: str) -> str:
    """Calculate retention score and churn risk assessment for a customer.

    Evaluates satisfaction, policy count, tenure, claims history, and
    contact recency to produce a 0-100 retention score with risk level.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with retention score, risk level (Low/Medium/High),
        contributing factors, and AI-generated retention recommendations.
    """
    customer_agent = _get_agent("customer")
    retention_agent = _get_agent("retention")
    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        return json.dumps(profile)
    return json.dumps(
        retention_agent.get_retention_score(customer_id, profile),
        default=str, indent=2,
    )


# ═══════════════════════════════════════════════════════════════════════
#  HAZARD RISK TOOLS
# ═══════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_flood_risk(zip_code: str) -> str:
    """Assess flood risk for a ZIP code using OpenFEMA data.

    Combines NFIP claims history and FEMA disaster declarations over
    a 10-year window to produce a 0-100 risk score.

    Args:
        zip_code: 5-digit US ZIP code (e.g. "77001").

    Returns:
        JSON object with risk score, band (Low/Moderate/High/Severe),
        frequency data, financial impact, and AI risk narrative.
    """
    agent = _get_agent("hazard")
    result = agent.get_flood_risk(zip_code)
    return json.dumps(result, default=str, indent=2)


@mcp.tool()
def get_wildfire_risk(zip_code: str) -> str:
    """Assess wildfire risk for a ZIP code using OpenFEMA data.

    Combines disaster declarations and public assistance data over
    a 10-year window to produce a 0-100 risk score.

    Args:
        zip_code: 5-digit US ZIP code (e.g. "90210").

    Returns:
        JSON object with risk score, band (Low/Moderate/High/Severe),
        frequency data, financial impact, and AI risk narrative.
    """
    agent = _get_agent("hazard")
    result = agent.get_wildfire_risk(zip_code)
    return json.dumps(result, default=str, indent=2)


@mcp.tool()
def get_earthquake_risk(zip_code: str) -> str:
    """Assess earthquake risk for a ZIP code using OpenFEMA data.

    Combines disaster declarations and public assistance data over
    a 10-year window to produce a 0-100 risk score.

    Args:
        zip_code: 5-digit US ZIP code (e.g. "94102").

    Returns:
        JSON object with risk score, band (Low/Moderate/High/Severe),
        frequency data, financial impact, and AI risk narrative.
    """
    agent = _get_agent("hazard")
    result = agent.get_earthquake_risk(zip_code)
    return json.dumps(result, default=str, indent=2)


# ═══════════════════════════════════════════════════════════════════════
#  WEATHER TOOLS
# ═══════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_current_weather(location: str) -> str:
    """Get current weather conditions for a location using Azure Maps.

    Args:
        location: City name or location (e.g. "Dallas, TX").

    Returns:
        JSON object with temperature, humidity, wind, conditions,
        and insurance-relevant weather alerts.
    """
    agent = _get_agent("weather")
    result = agent.get_current_weather(location)
    return json.dumps(result, default=str, indent=2)


@mcp.tool()
def get_weather_forecast(location: str, days: int = 5) -> str:
    """Get weather forecast for a location using Azure Maps.

    Args:
        location: City name or location (e.g. "Dallas, TX").
        days: Number of forecast days (1-16).

    Returns:
        JSON object with daily forecast including temperature range,
        conditions, wind, and precipitation.
    """
    agent = _get_agent("weather")
    result = agent.get_forecast(location, days)
    return json.dumps(result, default=str, indent=2)


# ═══════════════════════════════════════════════════════════════════════
#  ENVIRONMENTAL TOOLS
# ═══════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_pollution_data(location: str) -> str:
    """Get air quality and pollution data for a location using Azure Maps.

    Args:
        location: City name or location (e.g. "Houston, TX").

    Returns:
        JSON object with AQI, pollutant levels (PM2.5, PM10, NO2, etc.),
        health recommendations, and AI insurance impact analysis.
    """
    agent = _get_agent("environmental")
    result = agent.get_pollution_data(location)
    return json.dumps(result, default=str, indent=2)


@mcp.tool()
def get_climate_data(region: str, timeframe: str = "current") -> str:
    """Get climate/weather data for a region using Azure Maps.

    Args:
        region: Region name or location (e.g. "Gulf Coast").
        timeframe: "current" or "forecast".

    Returns:
        JSON object with temperature, humidity, wind, UV index, and
        climate-related insurance risk factors.
    """
    agent = _get_agent("environmental")
    result = agent.get_climate_data(region, timeframe)
    return json.dumps(result, default=str, indent=2)


# ═══════════════════════════════════════════════════════════════════════
#  COMPOSITE TOOLS (multi-agent)
# ═══════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_customer_360(customer_id: str) -> str:
    """Get a comprehensive 360-degree view of a customer combining data
    from all agents — profile, sales opportunities, retention risk,
    and hazard exposure for their ZIP code.

    This is the most complete single-call view of a customer.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with profile, cross-sell recommendations, retention
        score, insights, and hazard risk for the customer's location.
    """
    customer_agent = _get_agent("customer")
    sales_agent = _get_agent("sales")
    retention_agent = _get_agent("retention")
    hazard_agent = _get_agent("hazard")

    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        return json.dumps(profile)

    result = {"customer_id": customer_id, "profile": profile}

    # Sales intelligence
    try:
        result["cross_sell"] = sales_agent.get_cross_sell_recommendations(customer_id, profile)
    except Exception as e:
        result["cross_sell"] = {"error": str(e)}

    # Retention
    try:
        result["retention"] = retention_agent.get_retention_score(customer_id, profile)
        result["insights"] = retention_agent.get_customer_insights(customer_id, profile)
    except Exception as e:
        result["retention"] = {"error": str(e)}

    # Hazard risk for customer's ZIP
    zip_code = profile.get("zip", "")
    if zip_code and len(zip_code) == 5:
        try:
            result["flood_risk"] = hazard_agent.get_flood_risk(zip_code)
        except Exception as e:
            result["flood_risk"] = {"error": str(e)}

    return json.dumps(result, default=str, indent=2)


@mcp.tool()
def get_logic_apps_customer_packet(customer_id: str) -> str:
    """Get workflow-ready customer packet for Logic Apps and automation pipelines.

    Provides a deterministic envelope with request metadata, normalized status,
    successful component payloads, and structured component-level errors.

    Args:
        customer_id: Customer ID (e.g. C0000481).

    Returns:
        JSON object with fields: request_id, generated_at, customer_id, status,
        data, errors, and meta.
    """
    return json.dumps(_build_logic_apps_customer_packet(customer_id), default=str, indent=2)


# ═══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Insurance Intelligence MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport: stdio (default) for local, sse for remote clients",
    )
    parser.add_argument("--port", type=int, default=8080, help="Port for SSE transport")
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
