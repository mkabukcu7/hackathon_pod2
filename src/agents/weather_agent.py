"""
Weather and Natural Disaster Risk Agent - Retrieves weather data and assesses 
insurance-relevant natural disaster risks (floods, wildfires, earthquakes)
"""
import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import random


class WeatherAgent:
    """Agent for retrieving weather information and natural disaster risk assessment"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Weather Agent
        
        Args:
            api_key: OpenWeatherMap API key (optional, defaults to env variable)
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Insurance risk zones data (mock - would come from FEMA, USGS, etc.)
        self.risk_zones = self._load_risk_zones()
        
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
