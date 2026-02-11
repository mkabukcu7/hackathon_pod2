# Multi-Agent System for Weather, Environmental, and Azure Data

A comprehensive multi-agent application built for hackathon_pod2 (Strategic Insurance Pod 2). This system integrates weather data, environmental information, and Azure resource management through a unified interface.

## Overview

This multi-agent application is inspired by the TechWorkshop-L300-AI-Apps-and-agents repository and provides:

- **Weather Agent**: Real-time weather data, forecasts, and air quality information
- **Environmental Agent**: Pollution levels, climate data, ecosystem health, and water quality metrics
- **Azure Agent**: Azure resource management, cost analysis, service health, and security recommendations
- **Agent Orchestrator**: Intelligent routing and coordination of multiple agents

## Features

- 🌤️ **Weather Data**: Current conditions, forecasts, and air quality from OpenWeatherMap
- 🌍 **Environmental Monitoring**: Pollution, climate trends, ecosystem health, and water quality
- ☁️ **Azure Integration**: Resource management, cost tracking, and security insights
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

- **OpenWeatherMap API**: Get a free API key from [OpenWeatherMap](https://openweathermap.org/api)
- **Azure Credentials**: Set up Azure service principal credentials
- **Environmental API**: Configure if using a specific environmental data service

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

### Weather Agent
- `get_current_weather(location, units)` - Current weather conditions
- `get_forecast(location, days, units)` - Weather forecast
- `get_air_quality(lat, lon)` - Air quality index and components

### Environmental Agent
- `get_pollution_data(location)` - Pollution levels and metrics
- `get_climate_data(region, timeframe)` - Climate trends and data
- `get_ecosystem_health(ecosystem_type, location)` - Ecosystem metrics
- `get_water_quality(water_body, location)` - Water quality parameters
- `get_environmental_alerts(location, alert_types)` - Environmental alerts

### Azure Agent
- `get_resource_groups()` - List Azure resource groups
- `get_resources_in_group(resource_group)` - Resources in a group
- `get_resource_metrics(resource_id, metric_names)` - Resource metrics
- `get_cost_analysis(resource_group, time_period)` - Cost analysis
- `get_service_health()` - Azure service health status
- `get_security_recommendations(resource_group)` - Security recommendations

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

## Acknowledgments

- Inspired by Microsoft's TechWorkshop-L300-AI-Apps-and-agents
- Built for Strategic Insurance Pod 2 Hackathon
- Weather data provided by OpenWeatherMap
- Azure integration powered by Azure SDK
