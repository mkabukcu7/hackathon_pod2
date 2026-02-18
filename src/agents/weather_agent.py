"""
Weather and Natural Disaster Risk Agent - Retrieves weather data and assesses 
insurance-relevant natural disaster risks (floods, wildfires, earthquakes)
Uses Azure Maps API for weather and OpenFEMA API for disaster data
"""
import os
import httpx
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import random
import sys
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.parquet_loader import get_external_signals
from utils.zip_crosswalk import get_county_for_zip
from services.openai_service import chat_completion, is_available as openai_available


class WeatherAgent:
    """Agent for retrieving weather information using Azure Maps and natural disaster risk assessment using OpenFEMA"""
    
    # Azure Maps API endpoints
    AZURE_MAPS_WEATHER_BASE = "https://atlas.microsoft.com/weather"
    AZURE_MAPS_SEARCH_BASE = "https://atlas.microsoft.com/search"
    
    # OpenFEMA API endpoints
    OPENFEMA_BASE = "https://www.fema.gov/api/open/v2"
    
    # Hazard type mappings for disaster declarations
    HAZARD_TYPES = {
        "flood": ["Flood", "Severe Storm(s)", "Hurricane", "Coastal Storm"],
        "wildfire": ["Fire"],
        "earthquake": ["Earthquake"]
    }
    
    def __init__(self, api_key: Optional[str] = None, use_parquet: bool = True):
        """Initialize the Weather Agent
        
        Args:
            api_key: Azure Maps API key (optional, defaults to env variable)
            use_parquet: Whether to use Parquet data for external signals (True) or mock data (False)
        """
        self.api_key = api_key or os.getenv("AZURE_MAPS_API_KEY")
        self.use_parquet = use_parquet
        self.external_signals_df = None
        self.client = httpx.Client(timeout=30)
        self.window_years = 10  # Historical window for FEMA data
        
        # Try to load Parquet data
        if use_parquet:
            try:
                self.external_signals_df = get_external_signals()
                print("Weather Agent loaded Parquet external signals data")
            except Exception as e:
                print(f"Failed to load external signals Parquet data: {e}")
                self.use_parquet = False
        
        # Insurance risk zones data (mock - would come from FEMA, USGS, etc.)
        self.risk_zones = self._load_risk_zones()
    
    def __del__(self):
        """Cleanup HTTP client"""
        if hasattr(self, 'client'):
            self.client.close()
        
    def get_current_weather(self, location: str, units: str = "metric") -> Dict[str, Any]:
        """Get current weather for a location using Azure Maps
        
        Args:
            location: City name or coordinates (lat,lon format)
            units: Temperature units (metric or imperial)
            
        Returns:
            Dictionary containing weather data
        """
        if not self.api_key:
            return {"error": "Azure Maps API key not configured", "source": "Azure Maps Weather API"}
            
        try:
            # First, geocode the location using Azure Maps Search
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": f"Location '{location}' not found", "source": "Azure Maps Search API"}
            
            lat, lon = coords
            
            # Get current weather from Azure Maps Weather API
            endpoint = f"{self.AZURE_MAPS_WEATHER_BASE}/currentConditions/json"
            params = {
                "api-version": "1.0",
                "query": f"{lat},{lon}",
                "subscription-key": self.api_key,
                "details": True  # Get additional details
            }
            
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("results"):
                return {"error": "No weather data available", "source": "Azure Maps Weather API"}
            
            weather = data["results"][0]
            
            result = {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "temperature": weather.get("temperature", {}).get("value"),
                "temperature_unit": weather.get("temperature", {}).get("unit"),
                "feels_like": weather.get("realFeelTemperature", {}).get("value"),
                "humidity": weather.get("relativeHumidity"),
                "pressure": weather.get("pressure", {}).get("value"),
                "pressure_unit": weather.get("pressure", {}).get("unit"),
                "description": weather.get("weatherText"),
                "wind_speed": weather.get("wind", {}).get("speed", {}).get("value"),
                "wind_unit": weather.get("wind", {}).get("speed", {}).get("unit"),
                "visibility": weather.get("visibility", {}).get("value"),
                "uv_index": weather.get("uvIndex"),
                "source": "Azure Maps Weather API",
                "timestamp": datetime.now().isoformat()
            }

            # Enrich with AI insurance impact analysis
            ai_narrative = self._ai_weather_insurance_analysis(result, "current")
            if ai_narrative:
                result["ai_insurance_narrative"] = ai_narrative
                result["ai_generated"] = True
            else:
                result["ai_generated"] = False

            return result
            
        except Exception as e:
            return {"error": f"Failed to fetch weather data: {str(e)}", "source": "Azure Maps Weather API"}
            
    def get_forecast(self, location: str, days: int = 5, units: str = "metric") -> Dict[str, Any]:
        """Get weather forecast for a location using Azure Maps
        
        Args:
            location: City name or coordinates (lat,lon format)
            days: Number of days for forecast (default 5)
            units: Temperature units (metric or imperial)
            
        Returns:
            Dictionary containing forecast data
        """
        if not self.api_key:
            return {"error": "Azure Maps API key not configured", "source": "Azure Maps Forecast API"}
            
        try:
            # Get coordinates for location
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": f"Location '{location}' not found", "source": "Azure Maps Search API"}
            
            lat, lon = coords
            
            # Get forecast from Azure Maps Weather API
            # Note: Azure Maps offers 1, 5, and 10 day forecasts
            duration = "5day" if days >= 5 else "1day"
            endpoint = f"{self.AZURE_MAPS_WEATHER_BASE}/forecast/{duration}/json"
            
            params = {
                "api-version": "1.0",
                "query": f"{lat},{lon}",
                "subscription-key": self.api_key,
                "details": True
            }
            
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("forecasts"):
                return {"error": "No forecast data available", "source": "Azure Maps Forecast API"}
            
            forecast_list = []
            for forecast in data["forecasts"][:days]:
                forecast_list.append({
                    "date": forecast.get("date"),
                    "temperature_min": forecast.get("temperature", {}).get("minimum", {}).get("value"),
                    "temperature_max": forecast.get("temperature", {}).get("maximum", {}).get("value"),
                    "temperature_unit": forecast.get("temperature", {}).get("minimum", {}).get("unit"),
                    "description_day": forecast.get("day", {}).get("iconPhrase"),
                    "description_night": forecast.get("night", {}).get("iconPhrase"),
                    "wind_speed": forecast.get("wind", {}).get("speed", {}).get("value"),
                    "wind_unit": forecast.get("wind", {}).get("speed", {}).get("unit"),
                    "rain_probability": forecast.get("day", {}).get("rainProbability"),
                    "snow_probability": forecast.get("day", {}).get("snowProbability")
                })
            
            return {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "forecast_days": len(forecast_list),
                "forecast": forecast_list,
                "source": "Azure Maps Forecast API",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch forecast data: {str(e)}", "source": "Azure Maps Forecast API"}
            
    def get_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get air quality data for coordinates using Azure Maps
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing air quality data
        """
        if not self.api_key:
            return {"error": "Azure Maps API key not configured", "source": "Azure Maps Air Quality API"}
            
        try:
            # Get current air quality index from Azure Maps
            endpoint = f"{self.AZURE_MAPS_WEATHER_BASE}/currentConditions/json"
            params = {
                "api-version": "1.0",
                "query": f"{lat},{lon}",
                "subscription-key": self.api_key,
                "details": True
            }
            
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("results"):
                return {"error": "No air quality data available", "source": "Azure Maps Air Quality API"}
            
            weather = data["results"][0]
            
            # Map Azure AQI to quality levels
            aqi = weather.get("airQuality", {}).get("aqi", -1)
            aqi_category_map = {
                1: "Good",
                2: "Fair", 
                3: "Moderate",
                4: "Poor",
                5: "Very Poor",
                6: "Hazardous"
            }
            
            return {
                "coordinates": {"lat": lat, "lon": lon},
                "air_quality_index": aqi,
                "quality_level": aqi_category_map.get(aqi, "Unknown"),
                "pollutants": {
                    "pm2_5": weather.get("airQuality", {}).get("pm25"),
                    "pm10": weather.get("airQuality", {}).get("pm10"),
                    "no2": weather.get("airQuality", {}).get("no2"),
                    "o3": weather.get("airQuality", {}).get("o3"),
                    "so2": weather.get("airQuality", {}).get("so2"),
                    "co": weather.get("airQuality", {}).get("co")
                },
                "source": "Azure Maps Air Quality API",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch air quality data: {str(e)}", "source": "Azure Maps Air Quality API"}
            
    def get_flood_risk_assessment(self, location: str, lat: float, lon: float) -> Dict[str, Any]:
        """Get flood risk assessment for a location using FEMA disaster data
        
        Args:
            location: Location name
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing flood risk data based on actual FEMA disasters
        """
        try:
            # Get county from coordinates
            county_info = self._get_county_from_coords(lat, lon)
            if not county_info:
                # Try parsing location as ZIP code
                county_info = get_county_for_zip(location)
            
            if not county_info:
                return {
                    "error": "Could not determine county from location",
                    "location": location,
                    "source": "OpenFEMA Disaster Declarations"
                }
            
            # Get flood disaster declarations from FEMA
            disaster_count = self._get_disaster_count(
                county=county_info.get('county'),
                state=county_info.get('state_abbr', 'US'),
                hazard_type="flood"
            )
            
            # Get NFIP claims data
            claims_data = self._get_flood_claims(
                county=county_info.get('county'),
                state=county_info.get('state_abbr', 'US')
            )
            
            # Calculate risk level based on FEMA data
            risk_score = self._calculate_flood_risk_score(disaster_count, claims_data)
            
            return {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "county": county_info.get('county'),
                "state": county_info.get('state'),
                "flood_disasters_10_years": disaster_count,
                "nfip_claims": claims_data.get('count', 0),
                "total_claims_amount": claims_data.get('total_amount', 0),
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
                "premium_impact_factor": self._get_premium_factor(risk_score),
                "recommendations": self._get_flood_recommendations(risk_score),
                "data_sources": [
                    "OpenFEMA DisasterDeclarationsSummaries",
                    "OpenFEMA FimaNfipClaims"
                ],
                "source": "OpenFEMA",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to fetch FEMA flood data: {str(e)}",
                "location": location,
                "source": "OpenFEMA Disaster Declarations"
            }
        
    def get_wildfire_risk_assessment(self, location: str, lat: float, lon: float) -> Dict[str, Any]:
        """Get wildfire risk assessment for a location using FEMA disaster data
        
        Args:
            location: Location name
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing wildfire risk data based on actual FEMA disasters
        """
        try:
            # Get county from coordinates
            county_info = self._get_county_from_coords(lat, lon)
            if not county_info:
                county_info = get_county_for_zip(location)
            
            if not county_info:
                return {
                    "error": "Could not determine county from location",
                    "location": location,
                    "source": "OpenFEMA Disaster Declarations"
                }
            
            # Get fire disaster declarations from FEMA
            disaster_count = self._get_disaster_count(
                county=county_info.get('county'),
                state=county_info.get('state_abbr', 'US'),
                hazard_type="wildfire"
            )
            
            # Get public assistance data for fires
            assistance_data = self._get_public_assistance(
                county=county_info.get('county'),
                state=county_info.get('state_abbr', 'US'),
                hazard_type="wildfire"
            )
            
            # Calculate risk level based on FEMA data
            risk_score = self._calculate_wildfire_risk_score(disaster_count, assistance_data)
            
            return {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "county": county_info.get('county'),
                "state": county_info.get('state'),
                "fire_disasters_10_years": disaster_count,
                "public_assistance_projects": assistance_data.get('count', 0),
                "total_assistance_amount": assistance_data.get('total_amount', 0),
                "risk_score": risk_score,
                "wildfire_risk_level": self._get_risk_level(risk_score),
                "premium_impact_factor": self._get_premium_factor(risk_score),
                "mitigation_required": risk_score >= 50,
                "defensible_space_required_feet": 100 if risk_score >= 50 else 30,
                "recommendations": self._get_wildfire_recommendations_from_score(risk_score),
                "data_sources": [
                    "OpenFEMA DisasterDeclarationsSummaries",
                    "OpenFEMA PublicAssistanceFundedProjectsDetails"
                ],
                "source": "OpenFEMA",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to fetch FEMA wildfire data: {str(e)}",
                "location": location,
                "source": "OpenFEMA Disaster Declarations"
            }
        
    def get_earthquake_risk_assessment(self, location: str, lat: float, lon: float) -> Dict[str, Any]:
        """Get earthquake risk assessment for a location using FEMA disaster data
        
        Args:
            location: Location name
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing earthquake risk data based on actual FEMA disasters
        """
        try:
            # Get county from coordinates
            county_info = self._get_county_from_coords(lat, lon)
            if not county_info:
                county_info = get_county_for_zip(location)
            
            if not county_info:
                return {
                    "error": "Could not determine county from location",
                    "location": location,
                    "source": "OpenFEMA Disaster Declarations"
                }
            
            # Get earthquake disaster declarations from FEMA
            disaster_count = self._get_disaster_count(
                county=county_info.get('county'),
                state=county_info.get('state_abbr', 'US'),
                hazard_type="earthquake"
            )
            
            # Get public assistance data for earthquakes
            assistance_data = self._get_public_assistance(
                county=county_info.get('county'),
                state=county_info.get('state_abbr', 'US'),
                hazard_type="earthquake"
            )
            
            # Calculate risk level based on FEMA data
            risk_score = self._calculate_earthquake_risk_score(disaster_count, assistance_data)
            
            return {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "county": county_info.get('county'),
                "state": county_info.get('state'),
                "earthquake_disasters_10_years": disaster_count,
                "public_assistance_projects": assistance_data.get('count', 0),
                "total_assistance_amount": assistance_data.get('total_amount', 0),
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
                "premium_impact_factor": self._get_premium_factor(risk_score),
                "earthquake_insurance_recommended": risk_score >= 40,
                "seismic_retrofit_required": risk_score >= 70,
                "building_code_requirements": {
                    "seismic_retrofit_required": risk_score >= 70,
                    "special_inspection_required": risk_score >= 60
                },
                "recommendations": self._get_earthquake_recommendations_from_score(risk_score),
                "data_sources": [
                    "OpenFEMA DisasterDeclarationsSummaries",
                    "OpenFEMA PublicAssistanceFundedProjectsDetails"
                ],
                "source": "OpenFEMA",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to fetch FEMA earthquake data: {str(e)}",
                "location": location,
                "source": "OpenFEMA Disaster Declarations"
            }
        
    def get_comprehensive_property_risk(
        self,
        location: str,
        property_address: str,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:
        """Get comprehensive natural disaster risk assessment for property
        
        Args:
            location: Location name  
            property_address: Full property address
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing all natural disaster risks
        """
        flood_risk = self.get_flood_risk_assessment(location, lat, lon)
        wildfire_risk = self.get_wildfire_risk_assessment(location, lat, lon)
        earthquake_risk = self.get_earthquake_risk_assessment(location, lat, lon)
        
        # Calculate combined risk score (0-100)
        flood_score = {"Low": 10, "High": 60, "Very High": 90}.get(flood_risk["risk_level"], 10)
        wildfire_score = {"Low": 10, "Moderate": 30, "High": 60, "Very High": 80, "Extreme": 95}.get(
            wildfire_risk["wildfire_risk_level"], 10
        )
        earthquake_score = {"Negligible": 5, "Low": 15, "Moderate": 40, "High": 70, "Very High": 90}.get(
            earthquake_risk["risk_level"], 5
        )
        
        combined_score = int((flood_score + wildfire_score + earthquake_score) / 3)
        
        # Calculate total premium impact
        total_premium_factor = (
            flood_risk["premium_impact_factor"] * 0.4 +
            wildfire_risk["premium_impact_factor"] * 0.3 +
            earthquake_risk["premium_impact_factor"] * 0.3
        )
        
        result = {
            "property_address": property_address,
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "assessment_date": datetime.now().isoformat(),
            "combined_risk_score": combined_score,
            "overall_risk_rating": self._get_overall_risk_rating(combined_score),
            "flood_risk": flood_risk,
            "wildfire_risk": wildfire_risk,
            "earthquake_risk": earthquake_risk,
            "total_premium_impact_factor": round(total_premium_factor, 2),
            "insurance_recommendations": {
                "standard_homeowners": "Available",
                "flood_insurance": "Required" if flood_risk["flood_insurance_required"] else "Recommended",
                "earthquake_insurance": "Highly Recommended" if earthquake_risk["earthquake_insurance_recommended"] else "Optional",
                "wildfire_coverage_enhancement": "Required" if wildfire_risk["mitigation_required"] else "Optional"
            },
            "underwriting_notes": self._generate_underwriting_notes(flood_risk, wildfire_risk, earthquake_risk)
        }

        # Enrich with AI-generated comprehensive narrative
        ai_narrative = self._ai_weather_insurance_analysis(result, "comprehensive")
        if ai_narrative:
            result["ai_underwriting_narrative"] = ai_narrative
            result["ai_generated"] = True
        else:
            result["ai_generated"] = False

        return result
        
    # ---- Azure OpenAI helpers ------------------------------------------------

    def _ai_weather_insurance_analysis(self, data: Dict[str, Any], data_type: str) -> Optional[str]:
        """Generate AI-powered weather/risk insurance impact analysis.

        Args:
            data: The weather or risk data dictionary.
            data_type: 'current' for weather, 'comprehensive' for property risk.

        Returns:
            Analysis string, or None if AI is unavailable.
        """
        if not openai_available():
            return None

        try:
            if data_type == "current":
                context = (
                    f"Location: {data.get('location')}, "
                    f"Temp: {data.get('temperature')}{data.get('temperature_unit', 'C')}, "
                    f"Feels like: {data.get('feels_like')}, "
                    f"Humidity: {data.get('humidity')}%, "
                    f"Wind: {data.get('wind_speed')} {data.get('wind_unit', '')}, "
                    f"UV: {data.get('uv_index')}, "
                    f"Conditions: {data.get('description')}"
                )
                system_msg = (
                    "You are an insurance weather risk analyst. Given current weather "
                    "conditions, provide a concise 2-3 sentence assessment of how "
                    "these conditions affect property and auto insurance risk today. "
                    "Mention any actionable alerts for policyholders. Do NOT use markdown."
                )
            else:
                flood_score = data.get('flood_risk', {}).get('risk_score', 0)
                wildfire_score = data.get('wildfire_risk', {}).get('risk_score', 0)
                earthquake_score = data.get('earthquake_risk', {}).get('risk_score', 0)
                context = (
                    f"Property: {data.get('property_address', data.get('location'))}, "
                    f"Combined risk score: {data.get('combined_risk_score')}/100, "
                    f"Overall rating: {data.get('overall_risk_rating')}, "
                    f"Flood risk: {flood_score}/100, "
                    f"Wildfire risk: {wildfire_score}/100, "
                    f"Earthquake risk: {earthquake_score}/100, "
                    f"Premium impact factor: {data.get('total_premium_impact_factor')}"
                )
                system_msg = (
                    "You are a senior insurance underwriter. Given a comprehensive "
                    "property risk assessment, write a 3-4 sentence underwriting "
                    "narrative summarizing the key risks, premium implications, "
                    "and required coverage. Be specific about which perils drive "
                    "the most risk. Do NOT use markdown."
                )

            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": context},
            ]

            return chat_completion(messages, temperature=0.4, max_tokens=300)
        except Exception as e:
            print(f"AI weather analysis failed: {e}")
            return None

    def _get_coordinates(self, location: str) -> Optional[tuple]:
        """Get coordinates for a location using Azure Maps Search API
        
        Args:
            location: Location name or coordinates (lat,lon format)
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Check if already in lat,lon format
        try:
            parts = location.split(",")
            if len(parts) == 2:
                lat, lon = float(parts[0].strip()), float(parts[1].strip())
                return (lat, lon)
        except (ValueError, AttributeError):
            pass
        
        # Query Azure Maps Search API
        try:
            endpoint = f"{self.AZURE_MAPS_SEARCH_BASE}/address/json"
            params = {
                "api-version": "1.0",
                "query": location,
                "subscription-key": self.api_key
            }
            
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                coords = data["results"][0].get("position", {})
                lat = coords.get("lat")
                lon = coords.get("lon")
                if lat and lon:
                    return (lat, lon)
        except Exception as e:
            print(f"Error geocoding location: {e}")
        
        return None
        
    def _get_county_from_coords(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """Get county information from coordinates using ZIP crosswalk
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with county and state info, or None if not found
        """
        try:
            # For now, use a simple approximation - in production would use proper reverse geocoding
            # Try to approximate ZIP code from coordinates
            # This is a placeholder - proper implementation would use Google's Reverse Geocoding or similar
            return None
        except Exception:
            return None
    
    def _get_disaster_count(self, county: str, state: str, hazard_type: str) -> int:
        """Get count of FEMA disasters for a county and hazard type
        
        Args:
            county: County name
            state: State abbreviation
            hazard_type: Type of hazard (flood, wildfire, earthquake)
            
        Returns:
            Count of disaster declarations in past 10 years
        """
        try:
            start_date = datetime.now() - timedelta(days=self.window_years * 365)
            date_filter = f"declarationDate ge '{start_date.strftime('%Y-%m-%d')}'"
            state_filter = f"state eq '{state}'"
            
            incident_types = self.HAZARD_TYPES.get(hazard_type, [])
            if incident_types:
                type_filter = " or ".join([f"incidentType eq '{t}'" for t in incident_types])
                filter_str = f"{date_filter} and {state_filter} and ({type_filter})"
            else:
                filter_str = f"{date_filter} and {state_filter}"
            
            url = f"{self.OPENFEMA_BASE}/DisasterDeclarationsSummaries"
            params = {
                "$filter": filter_str,
                "$select": "designatedArea,incidentType",
                "$top": 1000
            }
            
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            disasters = data.get('DisasterDeclarationsSummaries', [])
            
            # Filter by county
            county_disasters = [
                d for d in disasters 
                if county.lower() in d.get('designatedArea', '').lower()
            ]
            
            return len(county_disasters)
            
        except Exception as e:
            print(f"Error fetching FEMA disaster count: {e}")
            return 0
    
    def _get_flood_claims(self, county: str, state: str) -> Dict[str, Any]:
        """Get NFIP flood claims for a county
        
        Args:
            county: County name
            state: State abbreviation
            
        Returns:
            Dictionary with claim count and total amount
        """
        try:
            start_date = datetime.now() - timedelta(days=self.window_years * 365)
            date_filter = f"dateOfLoss gt '{start_date.strftime('%Y-%m-%d')}'"
            state_filter = f"state eq '{state}'"
            
            url = f"{self.OPENFEMA_BASE}/FimaNfipClaims"
            params = {
                "$filter": f"{date_filter} and {state_filter}",
                "$select": "amountPaidOnBuildingClaim,amountPaidOnContentsClaim",
                "$top": 5000
            }
            
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            claims = data.get('FimaNfipClaims', [])
            
            total_amount = 0
            for claim in claims:
                building = float(claim.get('amountPaidOnBuildingClaim', 0) or 0)
                contents = float(claim.get('amountPaidOnContentsClaim', 0) or 0)
                total_amount += building + contents
            
            return {
                "count": len(claims),
                "total_amount": total_amount
            }
            
        except Exception as e:
            print(f"Error fetching flood claims: {e}")
            return {"count": 0, "total_amount": 0}
    
    def _get_public_assistance(self, county: str, state: str, hazard_type: str) -> Dict[str, Any]:
        """Get public assistance data for disasters
        
        Args:
            county: County name
            state: State abbreviation
            hazard_type: Type of hazard
            
        Returns:
            Dictionary with project count and total obligated amount
        """
        try:
            start_date = datetime.now() - timedelta(days=self.window_years * 365)
            date_filter = f"declarationDate ge '{start_date.strftime('%Y-%m-%d')}'"
            state_filter = f"stateAbbreviation eq '{state}'"
            county_filter = f"county eq '{county}'"
            
            filter_str = f"{date_filter} and {state_filter} and {county_filter}"
            
            url = f"{self.OPENFEMA_BASE}/PublicAssistanceFundedProjectsDetails"
            params = {
                "$filter": filter_str,
                "$select": "totalObligatedAmount",
                "$top": 5000
            }
            
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            projects = data.get('PublicAssistanceFundedProjectsDetails', [])
            
            total_amount = sum(
                float(p.get('totalObligatedAmount', 0) or 0)
                for p in projects
            )
            
            return {
                "count": len(projects),
                "total_amount": total_amount
            }
            
        except Exception as e:
            print(f"Error fetching public assistance: {e}")
            return {"count": 0, "total_amount": 0}
    
    def _calculate_flood_risk_score(self, disaster_count: int, claims_data: Dict[str, Any]) -> float:
        """Calculate flood risk score (0-100) based on FEMA data
        
        Args:
            disaster_count: Number of flood disasters in window
            claims_data: Dictionary with claim count and total
            
        Returns:
            Risk score 0-100
        """
        # Frequency score: (disaster_count / 5) * 50, max 50
        frequency_score = min(50, (disaster_count / 5.0) * 50)
        
        # Financial score: (total_claims / 10M) * 50, max 50
        total_claims = claims_data.get('total_amount', 0)
        financial_score = min(50, (total_claims / 10_000_000) * 50)
        
        return round(frequency_score + financial_score, 1)
    
    def _calculate_wildfire_risk_score(self, disaster_count: int, assistance_data: Dict[str, Any]) -> float:
        """Calculate wildfire risk score (0-100) based on FEMA data"""
        frequency_score = min(50, (disaster_count / 3.0) * 50)
        financial_score = min(50, (assistance_data.get('total_amount', 0) / 5_000_000) * 50)
        return round(frequency_score + financial_score, 1)
    
    def _calculate_earthquake_risk_score(self, disaster_count: int, assistance_data: Dict[str, Any]) -> float:
        """Calculate earthquake risk score (0-100) based on FEMA data"""
        frequency_score = min(50, (disaster_count / 2.0) * 50)
        financial_score = min(50, (assistance_data.get('total_amount', 0) / 10_000_000) * 50)
        return round(frequency_score + financial_score, 1)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 75:
            return "Severe"
        elif risk_score >= 50:
            return "High"
        elif risk_score >= 25:
            return "Moderate"
        else:
            return "Low"
    
    def _get_premium_factor(self, risk_score: float) -> float:
        """Calculate premium impact factor from risk score"""
        if risk_score >= 75:
            return 3.5
        elif risk_score >= 50:
            return 2.0
        elif risk_score >= 25:
            return 1.3
        else:
            return 1.0
        
    def _load_risk_zones(self) -> Dict[str, Dict[str, Any]]:
        """Load risk zone data (mock implementation)"""
        return {
            "Los Angeles": {
                "flood_zone": "X",
                "wildfire_risk": "High",
                "seismic_zone": "Zone 4"
            },
            "San Francisco": {
                "flood_zone": "X",
                "wildfire_risk": "Moderate",
                "seismic_zone": "Zone 4"
            },
            "Miami": {
                "flood_zone": "AE",
                "wildfire_risk": "Low",
                "seismic_zone": "Zone 0"
            },
            "Seattle": {
                "flood_zone": "X",
                "wildfire_risk": "Moderate",
                "seismic_zone": "Zone 3"
            }
        }
        
    def _get_flood_recommendations(self, risk_score_or_zone) -> List[str]:
        """Get flood mitigation recommendations based on risk score or zone"""
        # Support both risk score (float) and zone (string) formats
        if isinstance(risk_score_or_zone, (int, float)):
            risk_score = risk_score_or_zone
            if risk_score >= 75:
                return [
                    "CRITICAL: Flood insurance is required by mortgage lenders",
                    "Elevation of utilities and HVAC systems strongly recommended",
                    "Install flood vents and sump pump systems",
                    "Maintain excellent drainage systems",
                    "Develop detailed evacuation and emergency plans",
                    "Monitor flood warnings closely during storm season"
                ]
            elif risk_score >= 50:
                return [
                    "Flood insurance is highly recommended",
                    "Consider elevation of utilities and HVAC systems",
                    "Install flood vents in foundation walls",
                    "Maintain adequate drainage around property",
                    "Keep emergency supplies and evacuation plan ready"
                ]
            elif risk_score >= 25:
                return [
                    "Flood insurance is recommended",
                    "Monitor local weather and flood warnings",
                    "Maintain proper grading away from foundation",
                    "Consider flood vents or barriers"
                ]
            else:
                return [
                    "Monitor local weather and flood warnings",
                    "Consider optional flood insurance for peace of mind",
                    "Maintain proper grading away from foundation"
                ]
        else:
            # Legacy zone-based recommendations
            flood_zone = risk_score_or_zone
            if flood_zone in ["A", "AE", "V", "VE"]:
                return [
                    "Flood insurance is required by mortgage lenders",
                    "Consider elevation of utilities and HVAC systems",
                    "Install flood vents in foundation walls",
                    "Maintain adequate drainage around property",
                    "Keep emergency supplies and evacuation plan ready"
                ]
            return [
                "Monitor local weather and flood warnings",
                "Consider optional flood insurance for peace of mind",
                "Maintain proper grading away from foundation"
            ]
        
    def _get_wildfire_recommendations_from_score(self, risk_score: float) -> List[str]:
        """Get wildfire mitigation recommendations based on FEMA risk score"""
        if risk_score >= 75:
            return [
                "CRITICAL: Create and maintain 100+ foot defensible space around home",
                "Use fire-resistant roofing (Class A) and siding materials",
                "Remove all dead vegetation and maintain aggressive landscaping",
                "Install ember-resistant vents and screens",
                "Keep fire extinguishers and sprinkler systems accessible",
                "Develop and regularly practice evacuation plan",
                "Maintain access roads for emergency vehicles"
            ]
        elif risk_score >= 50:
            return [
                "Create and maintain 100-foot defensible space around home",
                "Use fire-resistant roofing and siding materials",
                "Remove dead vegetation and maintain landscaping",
                "Install ember-resistant vents",
                "Keep fire extinguishers accessible",
                "Develop and practice evacuation plan"
            ]
        elif risk_score >= 25:
            return [
                "Maintain 50-foot defensible space around home",
                "Trim branches away from roof and chimney",
                "Remove dead vegetation regularly",
                "Consider fire-resistant landscaping"
            ]
        else:
            return [
                "Maintain 30-foot defensible space around home",
                "Remove dead vegetation regularly",
                "Consider fire-resistant landscaping"
            ]
        
    def _get_wildfire_recommendations(self, risk_level: str) -> List[str]:
        """Get wildfire mitigation recommendations (legacy zone-based)"""
        if risk_level in ["High", "Very High", "Extreme"]:
            return [
                "Create and maintain 100-foot defensible space around home",
                "Use fire-resistant roofing and siding materials",
                "Remove dead vegetation and maintain landscaping",
                "Install ember-resistant vents",
                "Keep fire extinguishers accessible",
                "Develop and practice evacuation plan"
            ]
        return [
            "Maintain 30-foot defensible space around home",
            "Remove dead vegetation regularly",
            "Consider fire-resistant landscaping"
        ]
        
    def _get_earthquake_recommendations_from_score(self, risk_score: float) -> List[str]:
        """Get earthquake mitigation recommendations based on FEMA risk score"""
        if risk_score >= 75:
            return [
                "REQUIRED: Seismic retrofit likely required for older structures",
                "Bolt house to foundation immediately",
                "Secure water heater, HVAC, and large appliances",
                "Install automatic gas shut-off valve",
                "Strengthen or replace cripple walls and crawl spaces",
                "Earthquake insurance highly recommended",
                "Maintain comprehensive emergency supplies"
            ]
        elif risk_score >= 50:
            return [
                "Seismic retrofit recommended for structures built before 1980",
                "Bolt house to foundation",
                "Secure water heater and large appliances",
                "Install automatic gas shut-off valve",
                "Consider earthquake insurance",
                "Maintain emergency supplies"
            ]
        elif risk_score >= 25:
            return [
                "Secure heavy furniture and fixtures to walls",
                "Have structural inspection for older buildings",
                "Consider earthquake insurance",
                "Keep emergency supplies on hand"
            ]
        else:
            return [
                "Secure heavy furniture and fixtures",
                "Have structural inspection for older buildings",
                "Keep emergency supplies on hand"
            ]
        
    def _get_earthquake_recommendations(self, seismic_zone: str) -> List[str]:
        """Get earthquake mitigation recommendations (legacy zone-based)"""
        if seismic_zone in ["Zone 3", "Zone 4"]:
            return [
                "Seismic retrofit may be required for older structures",
                "Bolt house to foundation",
                "Secure water heater and large appliances",
                "Install automatic gas shut-off valve",
                "Strengthen cripple walls and crawl spaces",
                "Consider earthquake insurance",
                "Maintain emergency supplies"
            ]
        return [
            "Secure heavy furniture and fixtures",
            "Have structural inspection for older buildings",
            "Keep emergency supplies on hand"
        ]
        
    def _get_overall_risk_rating(self, combined_score: int) -> str:
        """Determine overall risk rating from combined score"""
        if combined_score >= 70:
            return "High Risk"
        elif combined_score >= 40:
            return "Moderate Risk"
        else:
            return "Low Risk"
            
    def _generate_underwriting_notes(
        self,
        flood_risk: Dict,
        wildfire_risk: Dict,
        earthquake_risk: Dict
    ) -> List[str]:
        """Generate underwriting notes based on risk assessments"""
        notes = []
        
        if flood_risk["flood_insurance_required"]:
            notes.append(f"REQUIRED: Flood insurance due to {flood_risk['flood_zone']} zone designation")
            
        if wildfire_risk["mitigation_required"]:
            notes.append(f"Property inspection required to verify {wildfire_risk['defensible_space_required_feet']}-ft defensible space")
            
        if earthquake_risk["building_code_requirements"]["seismic_retrofit_required"]:
            notes.append(f"Seismic retrofit certification required for properties in {earthquake_risk['seismic_zone']}")
            
        if not notes:
            notes.append("Standard underwriting procedures apply - no special requirements")
            
        return notes
