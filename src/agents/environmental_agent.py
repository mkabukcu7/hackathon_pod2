"""
Environmental Agent - Retrieves environmental data including pollution, climate, and ecosystem information
Uses Azure Maps API for environmental monitoring and air quality data
"""
import os
import httpx
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import sys
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.parquet_loader import get_external_signals


class EnvironmentalAgent:
    """Agent for retrieving environmental information using Azure Maps"""
    
    # Azure Maps API endpoints
    AZURE_MAPS_WEATHER_BASE = "https://atlas.microsoft.com/weather"
    AZURE_MAPS_SEARCH_BASE = "https://atlas.microsoft.com/search"
    
    def __init__(self, api_key: Optional[str] = None, use_parquet: bool = True):
        """Initialize the Environmental Agent
        
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
                print("Environmental Agent loaded Parquet external signals data")
            except Exception as e:
                print(f"Failed to load external signals Parquet data: {e}")
                self.use_parquet = False
    
    def __del__(self):
        """Cleanup HTTP client"""
        if hasattr(self, 'client'):
            self.client.close()
        
    def get_pollution_data(self, location: str) -> Dict[str, Any]:
        """Get pollution/air quality data for a location using Azure Maps
        
        Args:
            location: Location name or coordinates (lat,lon format)
            
        Returns:
            Dictionary containing pollution data
        """
        if not self.api_key:
            return {"error": "Azure Maps API key not configured", "source": "Azure Maps Air Quality API"}
        
        try:
            # Get coordinates for location
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": f"Location '{location}' not found", "source": "Azure Maps Search API"}
            
            lat, lon = coords
            
            # Get air quality from Azure Maps
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
            air_quality = weather.get("airQuality", {})
            
            # Map AQI to health recommendations
            aqi = air_quality.get("aqi", -1)
            aqi_levels = {
                1: ("Good", "Air quality is satisfactory"),
                2: ("Fair", "Air quality is acceptable for most, sensitive groups should limit prolonged exertion"),
                3: ("Moderate", "Some members of sensitive groups may experience health effects"),
                4: ("Poor", "Members of sensitive groups and general public may experience health effects"),
                5: ("Very Poor", "Health alert: The risk of health effects is increased for the general population"),
                6: ("Hazardous", "Health warning: Everyone may experience serious health effects")
            }
            
            level, description = aqi_levels.get(aqi, ("Unknown", "Unable to determine air quality"))
            
            return {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "air_quality_index": aqi,
                "level": level,
                "description": description,
                "pollution_levels": {
                    "pm2_5": air_quality.get("pm25"),  # PM2.5 particulate matter (μg/m³)
                    "pm10": air_quality.get("pm10"),  # PM10 particulate matter (μg/m³)
                    "no2": air_quality.get("no2"),   # Nitrogen dioxide (μg/m³)
                    "so2": air_quality.get("so2"),   # Sulfur dioxide (μg/m³)
                    "co": air_quality.get("co"),     # Carbon monoxide (mg/m³)
                    "o3": air_quality.get("o3")      # Ozone (μg/m³)
                },
                "health_recommendations": self._get_health_recommendations(aqi),
                "source": "Azure Maps Air Quality API",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch pollution data: {str(e)}", "source": "Azure Maps Air Quality API"}
        
    def get_climate_data(self, region: str, timeframe: str = "current") -> Dict[str, Any]:
        """Get climate/weather data for a region using Azure Maps
        
        Args:
            region: Region name or coordinates (lat,lon format)
            timeframe: Timeframe for data (current, forecast)
            
        Returns:
            Dictionary containing climate data
        """
        if not self.api_key:
            return {"error": "Azure Maps API key not configured", "source": "Azure Maps Weather API"}
        
        try:
            # Get coordinates for location
            coords = self._get_coordinates(region)
            if not coords:
                return {"error": f"Location '{region}' not found", "source": "Azure Maps Search API"}
            
            lat, lon = coords
            
            if timeframe == "forecast":
                # Get forecast data
                endpoint = f"{self.AZURE_MAPS_WEATHER_BASE}/forecast/5day/json"
            else:
                # Get current conditions
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
            
            if timeframe == "forecast" and data.get("forecasts"):
                forecasts = data["forecasts"]
                return {
                    "region": region,
                    "coordinates": {"lat": lat, "lon": lon},
                    "timeframe": "5-day forecast",
                    "forecasts": [
                        {
                            "date": f.get("date"),
                            "temperature_min": f.get("temperature", {}).get("minimum", {}).get("value"),
                            "temperature_max": f.get("temperature", {}).get("maximum", {}).get("value"),
                            "description_day": f.get("day", {}).get("iconPhrase"),
                            "description_night": f.get("night", {}).get("iconPhrase"),
                            "wind_speed": f.get("wind", {}).get("speed", {}).get("value")
                        }
                        for f in forecasts
                    ],
                    "source": "Azure Maps Forecast API",
                    "timestamp": datetime.now().isoformat()
                }
            elif data.get("results"):
                weather = data["results"][0]
                return {
                    "region": region,
                    "coordinates": {"lat": lat, "lon": lon},
                    "timeframe": timeframe,
                    "temperature": weather.get("temperature", {}).get("value"),
                    "temperature_unit": weather.get("temperature", {}).get("unit", "C"),
                    "weather_text": weather.get("weatherText"),
                    "humidity": weather.get("relativeHumidity"),
                    "uv_index": weather.get("uvIndex"),
                    "visibility": weather.get("visibility", {}).get("value"),
                    "wind": {
                        "speed": weather.get("wind", {}).get("speed", {}).get("value"),
                        "direction": weather.get("wind", {}).get("direction", {}).get("degrees")
                    },
                    "source": "Azure Maps Weather API",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": "No climate data available", "source": "Azure Maps Weather API"}
            
        except Exception as e:
            return {"error": f"Failed to fetch climate data: {str(e)}", "source": "Azure Maps Weather API"}
    
    async def _get_coordinates(self, location: str) -> Tuple[float, float]:
        """Convert location name to coordinates using Azure Maps Search API
        
        Args:
            location: Location name (address, city, landmark, etc.)
            
        Returns:
            Tuple of (latitude, longitude)
        """
        try:
            params = {
                "query": location,
                "subscription-key": self.api_key,
                "api-version": "1.0"
            }
            url = f"{self.AZURE_MAPS_SEARCH_BASE}/search/address/json"
            response = await self.client.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                position = result.get("position", {})
                return (position.get("lat"), position.get("lon"))
            
            raise ValueError(f"Could not find coordinates for location: {location}")
        except Exception as e:
            raise ValueError(f"Geocoding failed for {location}: {str(e)}")
    
    def _get_health_recommendations(self, aqi: int) -> str:
        """Get health recommendations based on Air Quality Index
        
        Args:
            aqi: Air Quality Index (1-6)
            
        Returns:
            Health recommendation string
        """
        recommendations = {
            1: "Air quality is excellent. Enjoy outdoor activities.",
            2: "Air quality is good. Suitable for outdoor activities.",
            3: "Air quality is acceptable. Sensitive groups may experience issues.",
            4: "Air quality is poor. General public may experience health effects.",
            5: "Air quality is very poor. Everyone advised to limit outdoor exposure.",
            6: "Air quality is hazardous. Avoid all outdoor activities."
        }
        return recommendations.get(aqi, "Health status uncertain. Check local air quality updates.")
    
    def get_ecosystem_health(self, ecosystem_type: str, location: str) -> Dict[str, Any]:
        """Get ecosystem health metrics
        
        Args:
            ecosystem_type: Type of ecosystem (forest, ocean, wetland, etc.)
            location: Location of the ecosystem
            
        Returns:
            Dictionary containing ecosystem health data
        """
        # Mock implementation - replace with actual API call when available
        return {
            "ecosystem_type": ecosystem_type,
            "location": location,
            "health_score": 7.2,  # Out of 10
            "biodiversity_index": 0.75,
            "vegetation_coverage": 82.3,  # Percentage
            "water_quality": "Good",
            "threats": [
                "Urban expansion",
                "Climate change impacts"
            ],
            "conservation_status": "Protected",
            "recent_changes": {
                "vegetation_change": "+2.1%",
                "species_diversity": "-1.5%"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    def get_water_quality(self, water_body: str, location: str) -> Dict[str, Any]:
        """Get water quality information
        
        Args:
            water_body: Name or type of water body
            location: Location of the water body
            
        Returns:
            Dictionary containing water quality data
        """
        # Mock implementation - replace with actual API call when available
        return {
            "water_body": water_body,
            "location": location,
            "quality_rating": "Good",
            "parameters": {
                "ph": 7.4,
                "dissolved_oxygen": 8.2,  # mg/L
                "turbidity": 3.5,  # NTU
                "temperature": 15.5,  # Celsius
                "conductivity": 450  # μS/cm
            },
            "contaminants": {
                "heavy_metals": "Below threshold",
                "bacteria": "Safe levels",
                "nutrients": "Moderate"
            },
            "suitability": {
                "drinking": False,
                "swimming": True,
                "fishing": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
    def get_environmental_alerts(self, location: str, alert_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get environmental alerts for a location
        
        Args:
            location: Location to check for alerts
            alert_types: Types of alerts to filter (optional)
            
        Returns:
            Dictionary containing environmental alerts
        """
        # Mock implementation - replace with actual API call when available
        all_alerts = [
            {
                "type": "air_quality",
                "severity": "moderate",
                "message": "Elevated PM2.5 levels expected due to weather conditions",
                "expires": "2026-02-12T12:00:00Z"
            },
            {
                "type": "pollen",
                "severity": "high",
                "message": "High pollen count - allergy sufferers advised to take precautions",
                "expires": "2026-02-11T20:00:00Z"
            }
        ]
        
        if alert_types:
            filtered_alerts = [a for a in all_alerts if a["type"] in alert_types]
        else:
            filtered_alerts = all_alerts
            
        return {
            "location": location,
            "alert_count": len(filtered_alerts),
            "alerts": filtered_alerts,
            "timestamp": datetime.now().isoformat()
        }
