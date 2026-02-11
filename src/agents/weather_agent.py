"""
Weather Agent - Retrieves weather data from OpenWeatherMap API
"""
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class WeatherAgent:
    """Agent for retrieving weather information"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Weather Agent
        
        Args:
            api_key: OpenWeatherMap API key (optional, defaults to env variable)
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    def get_current_weather(self, location: str, units: str = "metric") -> Dict[str, Any]:
        """Get current weather for a location
        
        Args:
            location: City name or coordinates
            units: Temperature units (metric, imperial, or standard)
            
        Returns:
            Dictionary containing weather data
        """
        if not self.api_key:
            return {"error": "Weather API key not configured"}
            
        try:
            endpoint = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": units
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "location": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temperature": data.get("main", {}).get("temp"),
                "feels_like": data.get("main", {}).get("feels_like"),
                "humidity": data.get("main", {}).get("humidity"),
                "pressure": data.get("main", {}).get("pressure"),
                "description": data.get("weather", [{}])[0].get("description"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "clouds": data.get("clouds", {}).get("all"),
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch weather data: {str(e)}"}
            
    def get_forecast(self, location: str, days: int = 5, units: str = "metric") -> Dict[str, Any]:
        """Get weather forecast for a location
        
        Args:
            location: City name or coordinates
            days: Number of days for forecast (default 5)
            units: Temperature units (metric, imperial, or standard)
            
        Returns:
            Dictionary containing forecast data
        """
        if not self.api_key:
            return {"error": "Weather API key not configured"}
            
        try:
            endpoint = f"{self.base_url}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": units,
                "cnt": days * 8  # 8 data points per day (every 3 hours)
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            forecast_list = []
            for item in data.get("list", []):
                forecast_list.append({
                    "datetime": item.get("dt_txt"),
                    "temperature": item.get("main", {}).get("temp"),
                    "description": item.get("weather", [{}])[0].get("description"),
                    "humidity": item.get("main", {}).get("humidity"),
                    "wind_speed": item.get("wind", {}).get("speed")
                })
            
            return {
                "location": data.get("city", {}).get("name"),
                "country": data.get("city", {}).get("country"),
                "forecast": forecast_list,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch forecast data: {str(e)}"}
            
    def get_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get air quality data for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing air quality data
        """
        if not self.api_key:
            return {"error": "Weather API key not configured"}
            
        try:
            endpoint = f"{self.base_url}/air_pollution"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            aqi_map = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
            
            if data.get("list"):
                air_data = data["list"][0]
                return {
                    "air_quality_index": air_data.get("main", {}).get("aqi"),
                    "quality_level": aqi_map.get(air_data.get("main", {}).get("aqi"), "Unknown"),
                    "components": air_data.get("components", {}),
                    "timestamp": datetime.now().isoformat()
                }
            
            return {"error": "No air quality data available"}
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch air quality data: {str(e)}"}
