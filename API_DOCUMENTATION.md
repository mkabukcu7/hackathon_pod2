# API Documentation

## Overview

The Multi-Agent System provides a comprehensive REST API built with FastAPI. The API allows you to access weather data, environmental information, and Azure resource management capabilities through simple HTTP requests.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

Currently, the API uses API keys configured in environment variables. No additional authentication is required for API endpoints, but ensure your `.env` file is properly configured.

## Endpoints

### General Endpoints

#### GET /
Root endpoint with API information

**Response:**
```json
{
  "name": "Multi-Agent System API",
  "version": "1.0.0",
  "description": "API for Weather, Environmental, and Azure data agents",
  "endpoints": {...}
}
```

#### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET /api/capabilities
Get available agent capabilities

**Response:**
```json
{
  "weather_agent": ["get_current_weather", "get_forecast", "get_air_quality"],
  "environmental_agent": [...],
  "azure_agent": [...]
}
```

### Query & Report Endpoints

#### POST /api/query
Process a natural language query

**Request Body:**
```json
{
  "query": "What's the weather in London?",
  "location": "London",
  "context": {}
}
```

**Response:**
```json
{
  "query": "What's the weather in London?",
  "timestamp": "2026-02-11T17:00:00",
  "agents_used": ["weather"],
  "results": {
    "current_weather": {...}
  }
}
```

#### POST /api/report
Generate a comprehensive report

**Request Body:**
```json
{
  "location": "London",
  "resource_group": "my-resource-group"
}
```

**Response:**
```json
{
  "location": "London",
  "report_date": "2026-02-11T17:00:00",
  "weather": {...},
  "environmental": {...},
  "azure": {...}
}
```

### Weather Agent Endpoints

#### GET /api/weather/current
Get current weather for a location

**Parameters:**
- `location` (required): City name or location
- `units` (optional): metric, imperial, or standard (default: metric)

**Example:**
```bash
curl "http://localhost:8000/api/weather/current?location=London&units=metric"
```

**Response:**
```json
{
  "location": "London",
  "country": "GB",
  "temperature": 15.2,
  "feels_like": 14.1,
  "humidity": 72,
  "description": "partly cloudy",
  "wind_speed": 5.2,
  "timestamp": "2026-02-11T17:00:00"
}
```

#### GET /api/weather/forecast
Get weather forecast

**Parameters:**
- `location` (required): City name or location
- `days` (optional): Number of days (1-16, default: 5)
- `units` (optional): metric, imperial, or standard

**Example:**
```bash
curl "http://localhost:8000/api/weather/forecast?location=Paris&days=3"
```

#### GET /api/weather/air-quality
Get air quality data

**Parameters:**
- `lat` (required): Latitude
- `lon` (required): Longitude

**Example:**
```bash
curl "http://localhost:8000/api/weather/air-quality?lat=51.5074&lon=-0.1278"
```

### Environmental Agent Endpoints

#### GET /api/environmental/pollution
Get pollution data for a location

**Parameters:**
- `location` (required): Location name

**Example:**
```bash
curl "http://localhost:8000/api/environmental/pollution?location=Tokyo"
```

**Response:**
```json
{
  "location": "Tokyo",
  "pollution_levels": {
    "pm25": 15.2,
    "pm10": 28.4,
    "no2": 35.6,
    "so2": 12.3,
    "co": 0.8,
    "o3": 45.2
  },
  "overall_index": "Moderate",
  "health_recommendations": [...],
  "timestamp": "2026-02-11T17:00:00"
}
```

#### GET /api/environmental/climate
Get climate data for a region

**Parameters:**
- `region` (required): Region name
- `timeframe` (optional): current, historical, or projected

**Example:**
```bash
curl "http://localhost:8000/api/environmental/climate?region=Europe&timeframe=current"
```

#### GET /api/environmental/ecosystem
Get ecosystem health metrics

**Parameters:**
- `ecosystem_type` (required): Type of ecosystem (forest, ocean, wetland, etc.)
- `location` (required): Location name

**Example:**
```bash
curl "http://localhost:8000/api/environmental/ecosystem?ecosystem_type=forest&location=Amazon"
```

#### GET /api/environmental/water-quality
Get water quality information

**Parameters:**
- `water_body` (required): Name of water body
- `location` (required): Location name

**Example:**
```bash
curl "http://localhost:8000/api/environmental/water-quality?water_body=River+Thames&location=London"
```

#### GET /api/environmental/alerts
Get environmental alerts

**Parameters:**
- `location` (required): Location name
- `alert_types` (optional): List of alert types to filter

**Example:**
```bash
curl "http://localhost:8000/api/environmental/alerts?location=Seattle"
```

### Azure Agent Endpoints

#### GET /api/azure/resource-groups
Get list of Azure resource groups

**Example:**
```bash
curl "http://localhost:8000/api/azure/resource-groups"
```

**Response:**
```json
{
  "subscription_id": "...",
  "resource_group_count": 5,
  "resource_groups": [
    {
      "name": "my-rg",
      "location": "eastus",
      "tags": {}
    }
  ],
  "timestamp": "2026-02-11T17:00:00"
}
```

#### GET /api/azure/resources
Get resources in a resource group

**Parameters:**
- `resource_group` (required): Resource group name

**Example:**
```bash
curl "http://localhost:8000/api/azure/resources?resource_group=my-rg"
```

#### GET /api/azure/cost-analysis
Get cost analysis

**Parameters:**
- `resource_group` (optional): Resource group name
- `time_period` (optional): day, week, month, or year

**Example:**
```bash
curl "http://localhost:8000/api/azure/cost-analysis?time_period=month"
```

**Response:**
```json
{
  "scope": "subscription",
  "time_period": "month",
  "total_cost": 1245.67,
  "currency": "USD",
  "cost_by_service": {
    "Virtual Machines": 456.78,
    "Storage": 234.56,
    ...
  },
  "timestamp": "2026-02-11T17:00:00"
}
```

#### GET /api/azure/service-health
Get Azure service health status

**Example:**
```bash
curl "http://localhost:8000/api/azure/service-health"
```

#### GET /api/azure/security
Get security recommendations

**Parameters:**
- `resource_group` (optional): Resource group name

**Example:**
```bash
curl "http://localhost:8000/api/azure/security?resource_group=my-rg"
```

**Response:**
```json
{
  "scope": "my-rg",
  "security_score": 78,
  "recommendations": [
    {
      "severity": "High",
      "title": "Enable encryption at rest for storage accounts",
      "affected_resources": 3,
      "remediation": "Enable storage account encryption"
    }
  ],
  "timestamp": "2026-02-11T17:00:00"
}
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `500`: Internal Server Error

Error responses include details:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Rate limiting depends on the external APIs being used:

- **OpenWeatherMap**: Free tier allows 60 calls/minute
- **Azure APIs**: Varies by service

## Examples

### Python Example

```python
import requests

# Get current weather
response = requests.get(
    "http://localhost:8000/api/weather/current",
    params={"location": "London"}
)
print(response.json())

# Process a query
response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "What's the weather and pollution in Paris?",
        "location": "Paris"
    }
)
print(response.json())
```

### cURL Examples

```bash
# Get current weather
curl "http://localhost:8000/api/weather/current?location=London"

# Get comprehensive report
curl -X POST "http://localhost:8000/api/report" \
  -H "Content-Type: application/json" \
  -d '{"location": "New York"}'

# Get Azure cost analysis
curl "http://localhost:8000/api/azure/cost-analysis?time_period=month"
```

### JavaScript Example

```javascript
// Get current weather
fetch('http://localhost:8000/api/weather/current?location=London')
  .then(response => response.json())
  .then(data => console.log(data));

// Process a query
fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: "What's the weather in Tokyo?",
    location: "Tokyo"
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## Testing the API

You can test the API using:

1. **Interactive Docs**: Visit http://localhost:8000/docs
2. **cURL**: Use the examples above
3. **Postman**: Import the API and test endpoints
4. **Python Requests**: Use the Python examples above

## Notes

- Some features return mock data when external APIs are not configured
- Ensure your `.env` file is properly configured for full functionality
- The API server can be run with: `python src/api.py`
- Default port is 8000, configurable via `APP_PORT` environment variable
