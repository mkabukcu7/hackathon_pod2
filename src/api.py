"""
Multi-Agent Application - FastAPI Web Server
Provides REST API endpoints for the multi-agent system
"""
import os
import sys
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from orchestrator import AgentOrchestrator
from agents import WeatherAgent, EnvironmentalAgent, AzureAgent


# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query to process")
    location: Optional[str] = Field(None, description="Location for context")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ReportRequest(BaseModel):
    location: str = Field(..., description="Location for the report")
    resource_group: Optional[str] = Field(None, description="Azure resource group")


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent System API",
    description="API for Weather, Environmental, and Azure data agents",
    version="1.0.0"
)

# Initialize orchestrator
orchestrator = AgentOrchestrator()


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Multi-Agent System API",
        "version": "1.0.0",
        "description": "API for Weather, Environmental, and Azure data agents",
        "endpoints": {
            "query": "/api/query",
            "report": "/api/report",
            "weather": "/api/weather/*",
            "environmental": "/api/environmental/*",
            "azure": "/api/azure/*",
            "capabilities": "/api/capabilities"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/query")
async def process_query(request: QueryRequest):
    """Process a natural language query
    
    Args:
        request: QueryRequest with query and optional context
        
    Returns:
        Results from relevant agents
    """
    try:
        context = request.context or {}
        if request.location:
            context["location"] = request.location
            
        result = orchestrator.process_query(request.query, context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/report")
async def generate_report(request: ReportRequest):
    """Generate a comprehensive report
    
    Args:
        request: ReportRequest with location and optional resource group
        
    Returns:
        Comprehensive report from all agents
    """
    try:
        result = orchestrator.get_comprehensive_report(
            request.location,
            request.resource_group
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capabilities")
async def get_capabilities():
    """Get available agent capabilities
    
    Returns:
        Dictionary of agent capabilities
    """
    return orchestrator.get_available_capabilities()


# Weather Agent Endpoints
@app.get("/api/weather/current")
async def get_current_weather(
    location: str = Query(..., description="Location name"),
    units: str = Query("metric", description="Units (metric, imperial, standard)")
):
    """Get current weather for a location"""
    try:
        weather_agent = WeatherAgent()
        result = weather_agent.get_current_weather(location, units)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weather/forecast")
async def get_weather_forecast(
    location: str = Query(..., description="Location name"),
    days: int = Query(5, ge=1, le=16, description="Number of days"),
    units: str = Query("metric", description="Units (metric, imperial, standard)")
):
    """Get weather forecast for a location"""
    try:
        weather_agent = WeatherAgent()
        result = weather_agent.get_forecast(location, days, units)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weather/air-quality")
async def get_air_quality(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """Get air quality data for coordinates"""
    try:
        weather_agent = WeatherAgent()
        result = weather_agent.get_air_quality(lat, lon)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Environmental Agent Endpoints
@app.get("/api/environmental/pollution")
async def get_pollution_data(
    location: str = Query(..., description="Location name")
):
    """Get pollution data for a location"""
    try:
        env_agent = EnvironmentalAgent()
        result = env_agent.get_pollution_data(location)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/environmental/climate")
async def get_climate_data(
    region: str = Query(..., description="Region name"),
    timeframe: str = Query("current", description="Timeframe (current, historical, projected)")
):
    """Get climate data for a region"""
    try:
        env_agent = EnvironmentalAgent()
        result = env_agent.get_climate_data(region, timeframe)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/environmental/ecosystem")
async def get_ecosystem_health(
    ecosystem_type: str = Query(..., description="Ecosystem type"),
    location: str = Query(..., description="Location name")
):
    """Get ecosystem health metrics"""
    try:
        env_agent = EnvironmentalAgent()
        result = env_agent.get_ecosystem_health(ecosystem_type, location)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/environmental/water-quality")
async def get_water_quality(
    water_body: str = Query(..., description="Water body name"),
    location: str = Query(..., description="Location name")
):
    """Get water quality information"""
    try:
        env_agent = EnvironmentalAgent()
        result = env_agent.get_water_quality(water_body, location)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/environmental/alerts")
async def get_environmental_alerts(
    location: str = Query(..., description="Location name"),
    alert_types: Optional[List[str]] = Query(None, description="Alert types to filter")
):
    """Get environmental alerts for a location"""
    try:
        env_agent = EnvironmentalAgent()
        result = env_agent.get_environmental_alerts(location, alert_types)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Azure Agent Endpoints
@app.get("/api/azure/resource-groups")
async def get_resource_groups():
    """Get list of Azure resource groups"""
    try:
        azure_agent = AzureAgent()
        result = azure_agent.get_resource_groups()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/azure/resources")
async def get_resources(
    resource_group: str = Query(..., description="Resource group name")
):
    """Get resources in a resource group"""
    try:
        azure_agent = AzureAgent()
        result = azure_agent.get_resources_in_group(resource_group)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/azure/cost-analysis")
async def get_cost_analysis(
    resource_group: Optional[str] = Query(None, description="Resource group name"),
    time_period: str = Query("month", description="Time period (day, week, month, year)")
):
    """Get cost analysis"""
    try:
        azure_agent = AzureAgent()
        result = azure_agent.get_cost_analysis(resource_group, time_period)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/azure/service-health")
async def get_service_health():
    """Get Azure service health status"""
    try:
        azure_agent = AzureAgent()
        result = azure_agent.get_service_health()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/azure/security")
async def get_security_recommendations(
    resource_group: Optional[str] = Query(None, description="Resource group name")
):
    """Get security recommendations"""
    try:
        azure_agent = AzureAgent()
        result = azure_agent.get_security_recommendations(resource_group)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the app with: uvicorn api:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
