# AI-Powered Insurance Agent Dashboard — Multi-Agent System

A comprehensive multi-agent application built for hackathon_pod2 (Strategic Insurance Pod 2). This system integrates weather data, environmental information, customer intelligence, sales analytics, and hazard risk assessment through a unified web dashboard and REST API — all powered by Azure OpenAI GPT-4o-mini.

## Overview

This multi-agent application is inspired by the TechWorkshop-L300-AI-Apps-and-agents repository and provides:

- **Weather Agent**: Real-time weather data, forecasts, air quality, and hazard risk assessment using Azure Maps and OpenFEMA
- **Environmental Agent**: Pollution levels, climate data, ecosystem health, and water quality metrics via Azure Maps
- **Azure Agent**: Azure resource management, cost analysis, service health, and security recommendations
- **Customer Profile Agent**: Customer lookup, profile management, and AI-generated customer summaries from Parquet data
- **Sales Intelligence Agent**: AI-powered cross-sell, up-sell recommendations, and personalized talking points
- **Retention Insights Agent**: Customer insights, trend analysis, retention scoring, and churn prediction
- **Hazard Risk Agent**: Flood, wildfire, and earthquake risk scoring using FEMA disaster data
- **Agent Orchestrator**: GPT-4o-mini powered intelligent routing with keyword-based fallback

## Features

- 🌤️ **Weather Data**: Current conditions, forecasts, and air quality from Azure Maps Weather API
- 🌍 **Environmental Monitoring**: Pollution levels, climate trends via Azure Maps Environmental APIs
- ☁️ **Azure Integration**: Resource management, cost tracking, and security insights via Azure SDK
- 🌊 **Hazard Risk Assessment**: Flood, wildfire, and earthquake risk scoring using OpenFEMA disaster data
- 📊 **Parquet Data Support**: 261K+ records from customer profiles, policies, claims, and environmental signals
- 🤖 **AI-Powered Intelligence**: All 7 agents + orchestrator enriched with Azure OpenAI GPT-4o-mini narratives
- 👤 **Customer Profiles**: 60K customer profiles with AI-generated summaries, searchable by ID/state/region/ZIP
- 💰 **Sales Intelligence**: AI-driven cross-sell, up-sell recommendations, and personalized talking points
- 📈 **Retention Analytics**: Customer insights, trend analysis, retention scoring, and churn prediction
- 🌐 **Web Dashboard**: Interactive browser-based dashboard with live weather, AI insights, and customer management
- 🌐 **REST API**: FastAPI-based web service with 25+ endpoints
- 💻 **CLI Interface**: Interactive command-line interface for easy access

## Architecture

```
src/
├── agents/                        # Individual agent implementations
│   ├── weather_agent.py           # Azure Maps weather + FEMA risk + AI narratives
│   ├── environmental_agent.py     # Azure Maps environmental + AI analysis
│   ├── azure_agent.py             # Azure resource management + AI analysis
│   ├── customer_profile_agent.py  # Parquet customer profiles + AI summaries
│   ├── sales_intelligence_agent.py # AI cross-sell, up-sell, talking points
│   ├── retention_insights_agent.py # AI insights, trends, retention scoring
│   └── hazard_risk_agent.py       # FEMA hazard risk scoring + AI narratives
├── services/
│   ├── openai_service.py          # Azure OpenAI GPT-4o-mini client (Entra ID auth)
│   └── cosmos_db_service.py       # Cosmos DB integration
├── utils/
│   ├── parquet_loader.py          # Parquet data loading with region correction
│   ├── zip_crosswalk.py           # ZIP-to-county mapping (20 states)
│   └── cache.py                   # Hazard risk cache (24-hour TTL)
├── orchestrator.py                # GPT-4o-mini intelligent routing + keyword fallback
├── main.py                        # CLI application
└── api.py                         # FastAPI web service (25+ endpoints)

web/
├── templates/
│   └── index.html                 # Dashboard UI
└── static/
    ├── css/styles.css              # Dashboard styles
    └── js/dashboard.js             # Dashboard logic (live API, AI formatting)

data/
├── *.parquet                      # 7 Parquet files (261K+ records)
└── zip_county_crosswalk.csv       # ZIP-to-county mapping

examples/
└── examples.py                    # Usage examples
```

## Workflow Integration

The project includes shared workflow payload builders and dedicated tests to support Logic Apps and other orchestration clients.

- **`src/workflows/logic_apps.py`**
  - Centralizes deterministic workflow payload construction used by both API and MCP entrypoints.
  - Prevents response-shape drift by keeping customer packet and platform health builders in one place.
  - Improves maintainability by removing duplicated workflow assembly logic.

- **`test_workflows.py`**
  - Verifies workflow routes are present.
  - Validates workflow auth behavior (`x-workflow-key`) including:
    - `401` when key is configured but missing/incorrect,
    - `503` default-deny behavior when auth is enabled but no shared key is configured,
    - explicit bypass only when `WORKFLOW_AUTH_DISABLED=true`.
  - Confirms authorized requests succeed for workflow endpoints.

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

```env
# Azure OpenAI (GPT-4o-mini) - Powers all AI features
AZURE_OPENAI_ENDPOINT=https://<your-openai-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Service Principal (Entra ID auth)
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>

# Azure Maps (Weather & Environmental data)
AZURE_MAPS_API_KEY=<your-maps-api-key>
```

> **Note**: The OpenAI service uses **Entra ID authentication** via `ClientSecretCredential` + `get_bearer_token_provider` (not API key auth) when `disableLocalAuth` is enabled by subscription policy. The API key field is still required in `.env` but Entra ID tokens are used for actual authentication.

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

### Web Dashboard

The application includes an interactive web dashboard for customer management and AI-powered intelligence.

Start the server and open `http://localhost:8000` in your browser:
```bash
cd src
python api.py
```

**Dashboard Features:**
- 📊 **Live Statistics**: Total customers, active policies, claims count, average premium (from Parquet data)
- 🔍 **Customer Search**: Search by customer ID, state, region, ZIP code, or income band
- 👤 **Customer Profiles**: Full profile with demographics, policies, claims, risk score, and AI summary
- 🌤️ **Weather Widget**: Real-time weather for the customer's location with AI insurance impact analysis
- 🌍 **Hazard Risk Cards**: Flood, wildfire, and earthquake risk scores by ZIP code
- 💰 **Cross-Sell/Up-Sell**: AI-generated product recommendations with confidence scores and talking points
- 💡 **Insights & Trends**: AI-powered customer insights, trend analysis, and retention scoring
- 💬 **Talking Points**: AI-generated conversation guides with greeting, relationship highlights, objection handlers, and closing
- 🤖 **AI Badge**: Visual indicator on all AI-generated content

#### Additional Customer API Endpoints

```bash
# Search customers
curl "http://localhost:8000/api/customers/search?query=NC&limit=50"

# Get customer profile
curl "http://localhost:8000/api/customers/C0052225"

# Get customer statistics
curl "http://localhost:8000/api/customers/stats"

# Cross-sell recommendations
curl "http://localhost:8000/api/customers/C0052225/cross-sell"

# Up-sell recommendations
curl "http://localhost:8000/api/customers/C0052225/upsell"

# Customer insights
curl "http://localhost:8000/api/customers/C0052225/insights"

# Customer trends
curl "http://localhost:8000/api/customers/C0052225/trends"

# Retention score
curl "http://localhost:8000/api/customers/C0052225/retention"

# Talking points
curl "http://localhost:8000/api/customers/C0052225/talking-points?context=sales"
```

### Examples

Run the example scripts:
```bash
cd examples
python examples.py
```

## Agent Capabilities

### Weather Agent (Azure Maps + OpenFEMA + AI)
- `get_current_weather(location, units)` - Current weather conditions via Azure Maps + AI insurance impact narrative
- `get_forecast(location, days, units)` - 5-day weather forecast via Azure Maps
- `get_air_quality(lat, lon)` - Air quality index and pollutant components (PM2.5, PM10, NO2, O3, SO2, CO) via Azure Maps
- `get_flood_risk_assessment()` - Flood risk scoring using FEMA disaster declarations and NFIP claims
- `get_wildfire_risk_assessment()` - Wildfire risk scoring using FEMA disaster declarations and public assistance
- `get_earthquake_risk_assessment()` - Earthquake risk scoring using FEMA disaster declarations and public assistance
- AI: `_ai_weather_insurance_analysis()` - GPT-4o-mini insurance weather impact and underwriting narratives

### Environmental Agent (Azure Maps + AI)
- `get_pollution_data(location)` - Air quality index and pollutant metrics via Azure Maps + AI insurance risk analysis
- `get_climate_data(region, timeframe)` - Current conditions and 5-day forecasts via Azure Maps + AI analysis
- `get_ecosystem_health(ecosystem_type, location)` - Ecosystem health metrics (mock implementation)
- `get_water_quality(water_body, location)` - Water quality parameters (mock implementation)
- `get_environmental_alerts(location, alert_types)` - Environmental alerts based on conditions (mock implementation)
- AI: `_ai_environmental_analysis()` - GPT-4o-mini insurance-relevant environmental risk analysis

### Azure Agent (AI-Enriched)
- `get_resource_groups()` - List Azure resource groups
- `get_resources_in_group(resource_group)` - Resources in a group
- `get_resource_metrics(resource_id, metric_names)` - Resource metrics
- `get_cost_analysis(resource_group, time_period)` - Cost analysis + AI cost optimization narrative
- `get_service_health()` - Azure service health status
- `get_security_recommendations(resource_group)` - Security recommendations + AI security narrative

### Customer Profile Agent (Parquet + AI)
- `search_customer(query, limit)` - Search by customer ID, state, region, ZIP code, or income band
- `get_customer_profile(customer_id)` - Full profile with policies, claims, and AI-generated summary
- `get_customer_policies(customer_id)` - Customer's insurance policies from Parquet data
- `get_stats()` - Overall statistics (total customers, policies, claims, premiums)
- AI: `_ai_generate_summary()` - GPT-4o-mini call-prep narrative for each customer

### Sales Intelligence Agent (AI-Powered)
- `get_cross_sell_recommendations(customer_id, customer_data)` - AI-generated cross-sell with confidence scores
- `get_upsell_recommendations(customer_id, customer_data)` - AI-generated policy upgrades
- `get_talking_points(customer_id, customer_data, context)` - Personalized conversation guides with greeting, relationship highlights, conversation starters, key facts, objection handlers, and closing
- `get_retention_offers(customer_id, customer_data)` - Retention-focused offers
- All methods: AI-first with rule-based fallback, `ai_generated` flag

### Retention Insights Agent (AI-Powered)
- `get_customer_insights(customer_id, customer_data)` - AI-generated customer insights with categories and actions
- `get_customer_trends(customer_id, customer_data)` - Trend analysis with predictions (retention probability, upsell readiness, churn risk)
- `get_retention_score(customer_id, customer_data)` - Retention scoring with AI recommendations
- All methods: AI-first with rule-based fallback, `ai_generated` flag

### Hazard Risk Agent (OpenFEMA + AI)
- `get_flood_risk(zip_code)` - Flood risk assessment using OpenFEMA NFIP claims and disaster declarations
- `get_wildfire_risk(zip_code)` - Wildfire risk assessment using OpenFEMA disaster data and public assistance
- `get_earthquake_risk(zip_code)` - Earthquake risk assessment using OpenFEMA disaster data and public assistance
- AI: `_ai_risk_narrative()` - GPT-4o-mini underwriting narrative for risk assessments

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

## Azure Setup

### Quick Setup with Automation Scripts

The fastest way to set up all Azure resources.

**Prerequisites:** Sign in to Azure CLI first using device code authentication:
```bash
az login --use-device-code
```
This will display a code and URL — open the URL in your browser, enter the code, and sign in with your Azure account.

#### Windows (PowerShell):
```powershell
.\setup-resources.ps1                  # Full setup (with Key Vault)
.\setup-resources.ps1 -SkipKeyVault    # Skip Key Vault (recommended for hackathon)
```

#### Linux/Mac (Bash):
```bash
chmod +x setup-resources.sh
./setup-resources.sh                           # Full setup (with Key Vault)
SKIP_KEYVAULT=true ./setup-resources.sh        # Skip Key Vault (recommended for hackathon)
```

These scripts will automatically create:
- ✅ Azure Maps (G2) - Weather and environmental data
- ✅ Azure OpenAI (gpt-4o-mini) - Agent orchestration
- ✅ Service Principal - Azure resource management
- ⬜ Key Vault - Secure credential storage (optional, skip with `-SkipKeyVault`)
- ✅ `.env.generated` file with all credentials

### Manual Setup

For step-by-step instructions, see [AZURE_SETUP.md](./AZURE_SETUP.md)

## Documentation

### Getting Started
- **[INDEX.md](./INDEX.md)** - Complete documentation index and quick navigation
- **[DEMO_GUIDE.md](./DEMO_GUIDE.md)** - Guided walkthrough of features
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - REST API endpoint reference

### Integration & Setup
- **[AZURE_SETUP.md](./AZURE_SETUP.md)** - Azure resource provisioning guide
- **[PARQUET_INTEGRATION.md](./PARQUET_INTEGRATION.md)** - Parquet data integration guide
- **[AGENTS_UPDATE_SUMMARY.md](./AGENTS_UPDATE_SUMMARY.md)** - Agent implementation details

### Verification & Testing
- **[FINAL_VERIFICATION.md](./FINAL_VERIFICATION.md)** - Complete verification report
- **[TASK_VERIFICATION_REPORT.md](./TASK_VERIFICATION_REPORT.md)** - Detailed test results
- **[IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)** - Implementation details

### Security & Compliance
- **[SECURITY.md](./SECURITY.md)** - Security guidelines and best practices

## Development

### Project Structure

The application follows the TechWorkshop-L300-AI-Apps-and-agents pattern with:
- Modular agent architecture (7 agents + orchestrator)
- AI-first with rule-based fallback pattern across all agents
- Azure OpenAI GPT-4o-mini integration via shared `openai_service.py`
- Entra ID authentication (service principal) for Azure OpenAI
- Clear separation of concerns (agents → services → utils)
- Parquet data integration with 60K customers, 90K policies, ~20K claims
- US Census Bureau region correction in `parquet_loader.py`
- ZIP-to-county crosswalk for 20 states
- Interactive web dashboard with live API data
- OData v4 compliant FEMA queries (lowercase `and`/`or`)
- FastAPI with `pattern=` parameter validation (no deprecated `regex=`)
- Comprehensive error handling and graceful degradation

### Adding New Agents

To add a new agent:

1. Create a new agent class in `src/agents/`
2. Implement required methods following the existing pattern
3. Add Parquet data support using `utils/parquet_loader.py`
4. Add the agent to `src/agents/__init__.py`
5. Update the orchestrator in `src/orchestrator.py`
6. Add API endpoints in `src/api.py` if needed

See [AGENTS_UPDATE_SUMMARY.md](./AGENTS_UPDATE_SUMMARY.md) for detailed implementation patterns.

## Testing

The application includes comprehensive example scripts:

```bash
# Verify all agents work with Parquet data (6/6 tests)
python examples/verify_agent_tasks.py

# Run all examples
cd examples
python examples.py
```

See [PARQUET_INTEGRATION.md](./PARQUET_INTEGRATION.md) for more examples.

## Troubleshooting

### API Key Issues
- Ensure `.env` file is configured with valid API keys
- Check that environment variables are loaded correctly
- Verify API key permissions and quotas
- See [AZURE_SETUP.md](./AZURE_SETUP.md#troubleshooting) for Azure-specific issues

### Import Errors
- Ensure you're running from the correct directory
- Verify virtual environment is activated
- Check that all dependencies are installed
- Verify Parquet files are in `data/` directory

### Azure Authentication
- Verify Azure credentials are correctly configured
- Ensure service principal has required permissions
- Check Azure subscription is active
- See [SECURITY.md](./SECURITY.md) for security guidelines

### Parquet Data Issues
- Verify `data/` directory exists with `.parquet` files
- Check that `pyarrow` is installed: `pip install pyarrow`
- Run verification: `python examples/verify_agent_tasks.py`
- See [PARQUET_INTEGRATION.md](./PARQUET_INTEGRATION.md#troubleshooting) for details

### OpenAI Model Deployment
- Ensure model is deployed in Azure OpenAI
- Check deployment name matches `AZURE_OPENAI_DEPLOYMENT_NAME`
- Verify API version is supported: `2024-02-15-preview`
- See [AZURE_SETUP.md](./AZURE_SETUP.md#troubleshooting) for fixes

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
- **Azure Maps (G2)**: Weather, air quality, environmental data, and geocoding
- **OpenFEMA v2**: Federal disaster declarations, NFIP claims, and public assistance data (OData v4 syntax)
- **Azure OpenAI (GPT-4o-mini)**: AI-powered agent intelligence across all 7 agents + orchestrator
  - Deployment: `gpt-4o-mini` (model version `2024-07-18`)
  - Authentication: Entra ID via `ClientSecretCredential` + `get_bearer_token_provider`
  - Features: Customer summaries, risk narratives, sales recommendations, retention insights, weather analysis, query routing

### OpenAI Service (`src/services/openai_service.py`)
Singleton Azure OpenAI client with:
- `chat_completion(messages, temperature, max_tokens, response_format)` → `Optional[str]`
- `is_available()` → `bool`
- Entra ID auth scope: `https://cognitiveservices.azure.com/.default`
- All agents use AI-first with rule-based fallback pattern

## Acknowledgments

- Inspired by Microsoft's TechWorkshop-L300-AI-Apps-and-agents
- Built for Strategic Insurance Pod 2 Hackathon
- Weather and environmental data provided by Azure Maps
- Disaster and risk data provided by OpenFEMA (public API)
- Azure integration powered by Azure SDK
