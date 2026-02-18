"""
Weather and Natural Disaster Risk Agent - Retrieves weather data and assesses 
insurance-relevant natural disaster risks (floods, wildfires, earthquakes)
Uses Azure Maps API for weather and environmental data
"""
import os
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import random
import sys
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.parquet_loader import get_external_signals


class WeatherAgent:
    """Agent for retrieving weather information using Azure Maps and natural disaster risk assessment"""
    
    # Azure Maps API endpoints
    AZURE_MAPS_WEATHER_BASE = "https://atlas.microsoft.com/weather"
    AZURE_MAPS_SEARCH_BASE = "https://atlas.microsoft.com/search"
    
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
            
            return {
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
        """Get flood risk assessment for a location (insurance underwriting)
        
        Args:
            location: Location name
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing flood risk data
        """
        # Mock implementation - would integrate with FEMA Flood Maps, NOAA, etc.
        zone_data = self.risk_zones.get(location, {})
        
        # Simulate flood zone determination
        flood_zones = ["X", "A", "AE", "V", "VE"]  # FEMA flood zones
        flood_zone = zone_data.get("flood_zone", random.choice(flood_zones))
        
        risk_levels = {
            "X": {"level": "Low", "description": "Minimal flood risk", "premium_factor": 1.0},
            "A": {"level": "High", "description": "High flood risk area", "premium_factor": 2.5},
            "AE": {"level": "High", "description": "Special Flood Hazard Area", "premium_factor": 2.8},
            "V": {"level": "Very High", "description": "Coastal high hazard", "premium_factor": 4.0},
            "VE": {"level": "Very High", "description": "Coastal with wave action", "premium_factor": 4.5}
        }
        
        risk_info = risk_levels.get(flood_zone, risk_levels["X"])
        
        return {
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "flood_zone": flood_zone,
            "risk_level": risk_info["level"],
            "description": risk_info["description"],
            "premium_impact_factor": risk_info["premium_factor"],
            "recommendations": self._get_flood_recommendations(flood_zone),
            "recent_flood_history": {
                "last_major_flood": "2019-05-15",
                "events_last_10_years": random.randint(0, 5),
                "average_depth_inches": random.randint(0, 48)
            },
            "flood_insurance_required": flood_zone in ["A", "AE", "V", "VE"],
            "base_flood_elevation_ft": random.randint(10, 50) if flood_zone != "X" else None,
            "timestamp": datetime.now().isoformat()
        }
        
    def get_wildfire_risk_assessment(self, location: str, lat: float, lon: float) -> Dict[str, Any]:
        """Get wildfire risk assessment for a location (insurance underwriting)
        
        Args:
            location: Location name
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing wildfire risk data
        """
        # Mock implementation - would integrate with USDA Forest Service, state fire agencies
        zone_data = self.risk_zones.get(location, {})
        
        # Wildfire risk categories
        risk_categories = ["Low", "Moderate", "High", "Very High", "Extreme"]
        wildfire_risk = zone_data.get("wildfire_risk", random.choice(risk_categories[:3]))
        
        risk_factors = {
            "Low": {"premium_factor": 1.0, "mitigation_required": False},
            "Moderate": {"premium_factor": 1.3, "mitigation_required": False},
            "High": {"premium_factor": 1.8, "mitigation_required": True},
            "Very High": {"premium_factor": 2.5, "mitigation_required": True},
            "Extreme": {"premium_factor": 3.5, "mitigation_required": True}
        }
        
        risk_info = risk_factors.get(wildfire_risk, risk_factors["Low"])
        
        # Calculate wildfire hazard score (0-100)
        vegetation_density = random.uniform(0.3, 0.9)
        slope_factor = random.uniform(0.1, 0.7)
        drought_index = random.uniform(0.0, 1.0)
        
        hazard_score = int((vegetation_density * 40 + slope_factor * 30 + drought_index * 30))
        
        return {
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "wildfire_risk_level": wildfire_risk,
            "hazard_score": hazard_score,
            "premium_impact_factor": risk_info["premium_factor"],
            "mitigation_required": risk_info["mitigation_required"],
            "risk_factors": {
                "vegetation_density": round(vegetation_density * 100, 1),
                "terrain_slope": round(slope_factor * 100, 1),
                "drought_index": round(drought_index * 100, 1),
                "proximity_to_wildland": random.choice(["Within 1 mile", "1-3 miles", "3-5 miles", ">5 miles"])
            },
            "recent_fire_history": {
                "fires_within_10_miles_last_5_years": random.randint(0, 8),
                "acres_burned_nearby": random.randint(0, 50000),
                "last_major_fire_distance_miles": round(random.uniform(2, 50), 1)
            },
            "recommendations": self._get_wildfire_recommendations(wildfire_risk),
            "defensible_space_required_feet": 100 if risk_info["mitigation_required"] else 30,
            "timestamp": datetime.now().isoformat()
        }
        
    def get_earthquake_risk_assessment(self, location: str, lat: float, lon: float) -> Dict[str, Any]:
        """Get earthquake risk assessment for a location (insurance underwriting)
        
        Args:
            location: Location name
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing earthquake risk data
        """
        # Mock implementation - would integrate with USGS earthquake data
        zone_data = self.risk_zones.get(location, {})
        
        # Seismic zones (based on USGS classifications)
        seismic_zones = ["Zone 0", "Zone 1", "Zone 2A", "Zone 2B", "Zone 3", "Zone 4"]
        seismic_zone = zone_data.get("seismic_zone", random.choice(seismic_zones[:3]))
        
        zone_risk = {
            "Zone 0": {"risk": "Negligible", "pga": 0.02, "premium_factor": 1.0},
            "Zone 1": {"risk": "Low", "pga": 0.075, "premium_factor": 1.1},
            "Zone 2A": {"risk": "Moderate", "pga": 0.15, "premium_factor": 1.4},
            "Zone 2B": {"risk": "Moderate", "pga": 0.20, "premium_factor": 1.6},
            "Zone 3": {"risk": "High", "pga": 0.30, "premium_factor": 2.2},
            "Zone 4": {"risk": "Very High", "pga": 0.40, "premium_factor": 3.0}
        }
        
        zone_info = zone_risk.get(seismic_zone, zone_risk["Zone 0"])
        
        # Calculate expected ground motion
        peak_ground_acceleration = zone_info["pga"]  # g-force
        
        return {
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "seismic_zone": seismic_zone,
            "risk_level": zone_info["risk"],
            "peak_ground_acceleration_g": peak_ground_acceleration,
            "premium_impact_factor": zone_info["premium_factor"],
            "fault_proximity": {
                "nearest_active_fault": f"{random.choice(['San Andreas', 'Hayward', 'Calaveras', 'N/A'])}",
                "distance_to_fault_miles": round(random.uniform(0.5, 100), 1)
            },
            "earthquake_history": {
                "magnitude_5plus_within_50_miles_10_years": random.randint(0, 15),
                "last_significant_quake": {
                    "magnitude": round(random.uniform(3.0, 6.5), 1),
                    "date": "2022-08-14",
                    "distance_miles": round(random.uniform(5, 100), 1)
                }
            },
            "building_code_requirements": {
                "seismic_retrofit_required": seismic_zone in ["Zone 3", "Zone 4"],
                "special_inspection_required": seismic_zone in ["Zone 3", "Zone 4"],
                "reinforcement_standards": f"UBC {seismic_zone}"
            },
            "recommendations": self._get_earthquake_recommendations(seismic_zone),
            "earthquake_insurance_recommended": seismic_zone in ["Zone 2B", "Zone 3", "Zone 4"],
            "timestamp": datetime.now().isoformat()
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
        
        return {
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
        
    def _get_flood_recommendations(self, flood_zone: str) -> List[str]:
        """Get flood mitigation recommendations"""
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
        
    def _get_wildfire_recommendations(self, risk_level: str) -> List[str]:
        """Get wildfire mitigation recommendations"""
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
        
    def _get_earthquake_recommendations(self, seismic_zone: str) -> List[str]:
        """Get earthquake mitigation recommendations"""
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
