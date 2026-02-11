# Agent Demo Guide - Customer Intelligence Dashboard

## Overview

This demo showcases an AI-powered multi-agent system for insurance agents, featuring real-time customer intelligence, cross-sell/up-sell recommendations, and natural disaster risk assessment.

## Key Features

### 1. **Agent Landing Page / Dashboard**
- Clean, modern interface with quick stats
- Rapid customer lookup with instant results
- Real-time AI insights surface automatically
- One-click access to recommendations

### 2. **Rapid Customer Lookup**
- Search by name, email, phone, or customer ID
- Instant results with customer summary
- Click to load full profile
- See key metrics at a glance (policies, LTV, satisfaction)

### 3. **AI-Generated Cross-Sell Suggestions**
- Automatic product recommendations based on customer profile
- Priority ranking (High/Medium/Low)
- Confidence scores and reasoning
- Pre-generated talking points for each recommendation
- One-click quote generation

### 4. **Up-Sell Opportunities**
- Policy enhancement recommendations
- Benefit comparisons (current vs. recommended)
- Cost analysis ($X more per month)
- Talking points for presenting upgrades

### 5. **Real-Time Customer Insights**
- Instant visual insights as you review profiles
- Satisfaction scores and trends
- Retention risk assessment
- Multi-product engagement indicators
- High-value customer alerts

### 6. **Customer Trends & Analytics**
- Retention score (0-100)
- Engagement trends
- Premium payment history
- Churn risk prediction
- Upsell readiness score

### 7. **AI-Powered Talking Points**
- Context-aware conversation guides
- Relationship highlights
- Key facts at your fingertips
- Personalized opening and closing statements
- Conversation starters for different scenarios

### 8. **Natural Disaster Risk Assessment** (Insurance-Focused)
- **Flood Risk**: FEMA flood zones, premium impact factors
- **Wildfire Risk**: Hazard scores, mitigation requirements
- **Earthquake Risk**: Seismic zones, peak ground acceleration
- Comprehensive property risk reports
- Underwriting recommendations

### 9. **Azure Cosmos DB Integration**
- Customer data stored in Azure Cosmos DB
- Fast queries and searches
- Scalable architecture
- Mock data fallback for demos

## Demo Scenario

### Scenario: Insurance Agent Reviews Customer Profile

**Starting Point**: Agent lands on dashboard

1. **Quick Stats Display**
   - See total customers (3)
   - Active opportunities (12)
   - AI insights generated today (8)
   - Average retention score (89%)

2. **Customer Search**
   - Agent types "Sarah" in search box
   - Instant results show "Sarah Johnson (C001)"
   - Profile displays: Premium customer, 2 policies, $45K LTV

3. **Profile Review - Real-Time Insights Surface**
   - ⭐ "Highly Satisfied Customer" - 4.5/5.0 score
   - ✅ "Excellent Claims History" - No claims filed
   - 💎 High engagement with 2 active policies
   - 📊 Retention score: 92/100

4. **One-Click Cross-Sell Access**
   - Agent clicks "Cross-Sell Opportunities"
   - Side panel slides in with AI recommendations:
     - **Life Insurance** (High Priority, 85% confidence)
       - Potential premium: $2,800/year
       - Bundle discount: 10%
       - 3 talking points pre-generated
     - **Umbrella Liability** (Medium Priority, 65% confidence)
       - Potential premium: $450/year
       - 3 talking points ready

5. **Talking Points for Conversation**
   - Agent clicks "Talking Points"
   - Gets personalized conversation guide:
     - "Hello Sarah! You've been with us for 5.9 years..."
     - Key facts about her policies
     - Conversation starters about bundling opportunities

6. **Up-Sell Opportunities**
   - Agent reviews policy enhancements
   - See "Upgrade to Comprehensive" recommendation
   - Only $29/month more
   - Benefits clearly outlined with talking points

## Mock Customer Data

### Customer C001 - Sarah Johnson (Premium)
- **Email**: sarah.johnson@email.com
- **Policies**: Auto Insurance ($1,250), Home Insurance ($1,800)
- **LTV**: $45,000
- **Satisfaction**: 4.5/5.0
- **Risk Score**: 0.25 (Low)
- **Best Cross-Sell**: Life Insurance
- **Best Up-Sell**: Comprehensive Auto Coverage

### Customer C002 - Michael Chen (Standard)
- **Email**: m.chen@techcorp.com
- **Policies**: Auto Insurance ($980)
- **LTV**: $8,500
- **Satisfaction**: 4.2/5.0
- **Risk Score**: 0.15 (Low)
- **Best Cross-Sell**: Home Insurance (bundle opportunity)
- **Best Up-Sell**: Upgrade to Comprehensive

### Customer C003 - Jennifer Martinez (Premium)
- **Email**: jmartinez@consulting.com
- **Policies**: Home ($2,200), Auto ($1,400), Life ($3,200)
- **LTV**: $125,000
- **Satisfaction**: 4.8/5.0
- **Risk Score**: 0.10 (Very Low)
- **Best Cross-Sell**: Umbrella Liability
- **Best Up-Sell**: Premium Plus with Accident Forgiveness

## Running the Demo

### Option 1: Web Dashboard (Recommended)

1. Start the API server:
   ```bash
   cd src
   python api.py
   ```

2. Open browser to: `http://localhost:8000`

3. Try the demo scenario:
   - Search for "Sarah", "Michael", or "Jennifer"
   - Click on a customer to load profile
   - Click "Cross-Sell Opportunities" to see AI recommendations
   - Click "Talking Points" to get conversation guide
   - Click "Customer Insights" to see trends and analytics

### Option 2: API Testing

Use the interactive API docs at `http://localhost:8000/docs`

Example API calls:
```bash
# Search customers
curl "http://localhost:8000/api/customers/search?query=Sarah"

# Get customer profile
curl "http://localhost:8000/api/customers/C001"

# Get cross-sell recommendations
curl "http://localhost:8000/api/customers/C001/cross-sell"

# Get talking points
curl "http://localhost:8000/api/customers/C001/talking-points?context=sales"

# Get customer insights
curl "http://localhost:8000/api/customers/C001/insights"
```

### Option 3: CLI Mode

```bash
cd src
python main.py --mode interactive
```

Then use commands like:
- `query What cross-sell opportunities does Sarah Johnson have?`
- `report London` (for comprehensive environmental/weather report)

## Natural Disaster Risk Demo

Test the insurance-relevant risk assessments:

```bash
# Get comprehensive property risk
curl "http://localhost:8000/api/weather/property-risk?location=Los+Angeles&address=123+Main+St&lat=34.05&lon=-118.24"

# Flood risk assessment
curl "http://localhost:8000/api/weather/flood-risk?location=Miami&lat=25.76&lon=-80.19"

# Wildfire risk assessment
curl "http://localhost:8000/api/weather/wildfire-risk?location=San+Francisco&lat=37.77&lon=-122.41"

# Earthquake risk assessment
curl "http://localhost:8000/api/weather/earthquake-risk?location=Seattle&lat=47.60&lon=-122.33"
```

## Key Demo Talking Points

1. **Speed**: "Notice how quickly customer insights load - this is real-time AI analysis"
2. **Intelligence**: "The system analyzes customer history, satisfaction, policies, and behavior to generate recommendations"
3. **Actionable**: "Every recommendation comes with talking points - no need to think about what to say"
4. **One-Click**: "Cross-sell and up-sell opportunities are just one click away"
5. **Retention Focus**: "We proactively identify at-risk customers and suggest retention strategies"
6. **Risk Assessment**: "Integrated natural disaster risk analysis for property underwriting"
7. **Azure-Powered**: "All customer data stored in Azure Cosmos DB for scalability and performance"

## Benefits Highlighted

- ✅ **Boost Retention**: Identify at-risk customers before they churn
- ✅ **Increase Revenue**: Automatic cross-sell and up-sell identification
- ✅ **Save Time**: AI-generated talking points and recommendations
- ✅ **Better Service**: Real-time insights help agents provide personalized service
- ✅ **Risk Management**: Comprehensive natural disaster risk assessment
- ✅ **Data-Driven**: All recommendations backed by AI analysis and confidence scores

## Architecture Highlights

- **Multi-Agent System**: Specialized agents for different capabilities
- **Azure Cosmos DB**: Scalable data storage
- **FastAPI**: High-performance REST API
- **Modern Web UI**: Responsive dashboard with real-time updates
- **Natural Language**: Can process conversational queries
- **Extensible**: Easy to add new agents and capabilities

## Next Steps for Production

1. Connect to real Azure Cosmos DB instance
2. Integrate with OpenWeatherMap API for live weather data
3. Connect to Azure services with real credentials
4. Add authentication and user management
5. Implement real-time notifications
6. Add more sophisticated AI models for recommendations
7. Integrate with CRM and policy management systems
