# Multi-Agent System for Weather, Environmental, and Azure Data

A comprehensive multi-agent application built for hackathon_pod2 (Strategic Insurance Pod 2). This system integrates weather data, environmental information, and Azure resource management through a unified interface.

## Overview

This multi-agent application is inspired by the TechWorkshop-L300-AI-Apps-and-agents repository and provides:

- **Weather Agent**: Real-time weather data, forecasts, air quality, and hazard risk assessment using Azure Maps and OpenFEMA
- **Environmental Agent**: Pollution levels, climate data, ecosystem health, and water quality metrics via Azure Maps
- **Azure Agent**: Azure resource management, cost analysis, service health, and security recommendations
- **Agent Orchestrator**: Intelligent routing and coordination of multiple agents
- **Hazard Risk Agent**: Flood, wildfire, and earthquake risk scoring using FEMA disaster data

## Features

- 🌤️ **Weather Data**: Current conditions, forecasts, and air quality from Azure Maps Weather API
- 🌍 **Environmental Monitoring**: Pollution levels, climate trends via Azure Maps Environmental APIs
- ☁️ **Azure Integration**: Resource management, cost tracking, and security insights via Azure SDK
- 🌊 **Hazard Risk Assessment**: Flood, wildfire, and earthquake risk scoring using OpenFEMA disaster data and claims
- 📊 **Parquet Data Support**: 261K+ records from customer profiles, policies, claims, and environmental signals
- 🤖 **Multi-Agent Orchestration**: Natural language query processing with intelligent agent routing
- 🌐 **REST API**: FastAPI-based web service with comprehensive endpoints
- 💻 **CLI Interface**: Interactive command-line interface for easy access

## Architecture

```
src/
├── agents/               # Individual agent implementations
│   ├── weather_agent.py
│   ├── environmental_agent.py
│   └── azure_agent.py
├── orchestrator.py       # Agent coordination and routing
├── main.py              # CLI application
└── api.py               # FastAPI web service

examples/
└── examples.py          # Usage examples
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/mkabukcu7/hackathon_pod2.git
cd hackathon_pod2
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

### Environment Variables

Edit the `.env` file with your credentials:

- **Azure Maps API Key**: Get from [Azure Portal](https://portal.azure.com/) > Azure Maps resource > Authentication > Primary Key
  - Provides weather, air quality, and environmental data
  - No separate credentials needed for OpenFEMA (public API)
- **Azure Credentials**: Set up Azure service principal credentials (subscription ID, tenant ID, client ID, client secret)
- **Azure OpenAI**: Configure for agent orchestration (endpoint and API key)

## Usage

### CLI Interface

#### Interactive Mode (Recommended)
```bash
cd src
python main.py --mode interactive
```

Available commands in interactive mode:
- `query <your question>` - Ask questions to the agents
- `report <location>` - Generate comprehensive reports
- `capabilities` - List available agent capabilities
- `help` - Show help message
- `exit` - Exit the application

#### Query Mode
```bash
python main.py --mode query --query "What's the weather in London?"
```

#### Report Mode
```bash
python main.py --mode report --location "Seattle" --output report.json
```

### REST API

Start the API server:
```bash
cd src
python api.py
```

The API will be available at `http://localhost:8000`

#### API Documentation
- Interactive API docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

#### Example API Calls

**Get current weather:**
```bash
curl "http://localhost:8000/api/weather/current?location=London"
```

**Process a query:**
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Paris?", "location": "Paris"}'
```

**Generate comprehensive report:**
```bash
curl -X POST "http://localhost:8000/api/report" \
  -H "Content-Type: application/json" \
  -d '{"location": "New York"}'
```

### Examples

Run the example scripts:
```bash
cd examples
python examples.py
```

## Agent Capabilities

### Weather Agent (Azure Maps + OpenFEMA)
- `get_current_weather(location, units)` - Current weather conditions via Azure Maps
- `get_forecast(location, days, units)` - 5-day weather forecast via Azure Maps
- `get_air_quality(lat, lon)` - Air quality index and pollutant components (PM2.5, PM10, NO2, O3, SO2, CO) via Azure Maps
- `get_flood_risk_assessment()` - Flood risk scoring using FEMA disaster declarations and NFIP claims
- `get_wildfire_risk_assessment()` - Wildfire risk scoring using FEMA disaster declarations and public assistance
- `get_earthquake_risk_assessment()` - Earthquake risk scoring using FEMA disaster declarations and public assistance

### Environmental Agent (Azure Maps)
- `get_pollution_data(location)` - Air quality index and pollutant metrics via Azure Maps
- `get_climate_data(region, timeframe)` - Current conditions and 5-day forecasts via Azure Maps
- `get_ecosystem_health(ecosystem_type, location)` - Ecosystem health metrics (mock implementation)
- `get_water_quality(water_body, location)` - Water quality parameters (mock implementation)
- `get_environmental_alerts(location, alert_types)` - Environmental alerts based on conditions (mock implementation)

### Azure Agent
- `get_resource_groups()` - List Azure resource groups
- `get_resources_in_group(resource_group)` - Resources in a group
- `get_resource_metrics(resource_id, metric_names)` - Resource metrics
- `get_cost_analysis(resource_group, time_period)` - Cost analysis
- `get_service_health()` - Azure service health status
- `get_security_recommendations(resource_group)` - Security recommendations

### Hazard Risk Agent (OpenFEMA Integration)
- `get_flood_risk(zip_code)` - Flood risk assessment using OpenFEMA NFIP claims and disaster declarations
- `get_wildfire_risk(zip_code)` - Wildfire risk assessment using OpenFEMA disaster data and public assistance
- `get_earthquake_risk(zip_code)` - Earthquake risk assessment using OpenFEMA disaster data and public assistance

#### Hazard Risk Scoring
The Hazard Risk Agent and Weather Agent compute risk scores (0-100) based on:
- **10-year historical window**: Analyzes data from the past decade (configurable)
- **50/50 frequency + financial blend**: 
  - Frequency score: Number of disaster declarations
  - Financial score: Total claims/assistance amounts from FEMA data
- **Risk Bands**: Low (0-25), Moderate (25-50), High (50-75), Severe (75-100)
- **County-level aggregation**: Uses ZIP-to-county crosswalk for accurate geographic mapping
- **Caching**: Results cached for 24 hours to optimize performance

**Data Sources (No API Key Required):**
- OpenFEMA DisasterDeclarationsSummaries (https://www.fema.gov/api/open/v2)
- OpenFEMA FimaNfipClaims (for flood risk analysis)
- OpenFEMA PublicAssistanceFundedProjectsDetails (for wildfire/earthquake analysis)

**Example API usage:**
```bash
curl "http://localhost:8000/api/risk/flood?zip=90001"
curl "http://localhost:8000/api/risk/wildfire?zip=94102"
curl "http://localhost:8000/api/risk/earthquake?zip=94102"
curl "http://localhost:8000/api/weather/flood-risk?location=Los%20Angeles,%20CA"
```

## Development

### Project Structure

The application follows the TechWorkshop-L300-AI-Apps-and-agents pattern with:
- Modular agent architecture
- Clear separation of concerns
- Extensible design for adding new agents
- RESTful API design
- Comprehensive error handling

### Adding New Agents

To add a new agent:

1. Create a new agent class in `src/agents/`
2. Implement required methods following the existing pattern
3. Add the agent to `src/agents/__init__.py`
4. Update the orchestrator in `src/orchestrator.py`
5. Add API endpoints in `src/api.py` if needed

## Testing

The application includes example scripts for testing:

```bash
cd examples
python examples.py
```

## Troubleshooting

### API Key Issues
- Ensure `.env` file is configured with valid API keys
- Check that environment variables are loaded correctly
- Verify API key permissions and quotas

### Import Errors
- Ensure you're running from the correct directory
- Verify virtual environment is activated
- Check that all dependencies are installed

### Azure Authentication
- Verify Azure credentials are correctly configured
- Ensure service principal has required permissions
- Check Azure subscription is active

## License

This project is part of the hackathon_pod2 initiative for Strategic Insurance Pod 2.

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue in the GitHub repository.

## Data Sources

### Parquet Data
The system includes 261,946+ records across 7 Parquet files (~5.5 MB):
- Customer profiles and demographics
- Insurance policies and coverage details
- Claims history and amounts
- Environmental signals and indicators
- Risk signals and assessments
- Producer information
- Activity logs and interactions

**Location:** `data/` directory (excluded from version control)

### External APIs
- **Azure Maps**: Weather, air quality, environmental data, and geocoding
- **OpenFEMA v2**: Federal disaster declarations, NFIP claims, and public assistance data
- **Azure OpenAI**: Agent orchestration and natural language processing

## Acknowledgments

- Inspired by Microsoft's TechWorkshop-L300-AI-Apps-and-agents
- Built for Strategic Insurance Pod 2 Hackathon
- Weather and environmental data provided by Azure Maps
- Disaster and risk data provided by OpenFEMA (public API)
- Azure integration powered by Azure SDK
