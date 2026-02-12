"""
Hazard Risk Agent - Computes hazard risk scores using OpenFEMA data
Provides flood, wildfire, and earthquake risk assessments by ZIP code
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.zip_crosswalk import get_county_for_zip, get_zips_for_county
from utils.cache import hazard_cache


class HazardRiskAgent:
    """Agent for computing hazard risk scores from OpenFEMA data"""
    
    # OpenFEMA API base URL
    OPENFEMA_BASE = "https://www.fema.gov/api/open/v2"
    
    # Hazard type mappings for disaster declarations
    HAZARD_TYPES = {
        "flood": ["Flood", "Severe Storm(s)", "Hurricane", "Coastal Storm"],
        "wildfire": ["Fire"],
        "earthquake": ["Earthquake"]
    }
    
    def __init__(self, window_years: int = 10, timeout: int = 30):
        """
        Initialize the Hazard Risk Agent
        
        Args:
            window_years: Number of years to look back for risk calculation
            timeout: HTTP timeout in seconds
        """
        self.window_years = window_years
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
    
    def __del__(self):
        """Cleanup HTTP client"""
        if hasattr(self, 'client'):
            self.client.close()
    
    def get_flood_risk(self, zip_code: str) -> Dict[str, Any]:
        """
        Get flood risk for a ZIP code
        
        Args:
            zip_code: 5-digit ZIP code
            
        Returns:
            Dictionary with risk score, metrics, and details
        """
        # Check cache first
        cache_key = f"flood_{zip_code}_{self.window_years}"
        cached = hazard_cache.get(cache_key)
        if cached:
            return cached
        
        # Get county info
        county_info = get_county_for_zip(zip_code)
        if not county_info:
            return self._error_response(zip_code, "ZIP code not found in crosswalk")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.window_years * 365)
        
        # Get NFIP claims for all ZIPs in the county
        county_zips = get_zips_for_county(county_info['county'], county_info['state_abbr'])
        nfip_data = self._get_nfip_claims(
            county_zips, 
            county_info['state_abbr'],
            start_date
        )
        
        # Get disaster declarations
        disaster_data = self._get_disaster_declarations(
            county_info['county'],
            county_info['state_abbr'],
            start_date,
            "flood"
        )
        
        # Calculate risk score
        result = self._calculate_risk_score(
            hazard_type="flood",
            zip_code=zip_code,
            county=county_info['county'],
            state=county_info['state'],
            state_abbr=county_info['state_abbr'],
            start_date=start_date,
            end_date=end_date,
            frequency_data=disaster_data,
            financial_data=nfip_data
        )
        
        # Cache result
        hazard_cache.set(cache_key, result)
        
        return result
    
    def get_wildfire_risk(self, zip_code: str) -> Dict[str, Any]:
        """
        Get wildfire risk for a ZIP code
        
        Args:
            zip_code: 5-digit ZIP code
            
        Returns:
            Dictionary with risk score, metrics, and details
        """
        # Check cache first
        cache_key = f"wildfire_{zip_code}_{self.window_years}"
        cached = hazard_cache.get(cache_key)
        if cached:
            return cached
        
        # Get county info
        county_info = get_county_for_zip(zip_code)
        if not county_info:
            return self._error_response(zip_code, "ZIP code not found in crosswalk")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.window_years * 365)
        
        # Get disaster declarations
        disaster_data = self._get_disaster_declarations(
            county_info['county'],
            county_info['state_abbr'],
            start_date,
            "wildfire"
        )
        
        # Get public assistance data
        pa_data = self._get_public_assistance(
            county_info['county'],
            county_info['state_abbr'],
            start_date,
            "wildfire"
        )
        
        # Calculate risk score
        result = self._calculate_risk_score(
            hazard_type="wildfire",
            zip_code=zip_code,
            county=county_info['county'],
            state=county_info['state'],
            state_abbr=county_info['state_abbr'],
            start_date=start_date,
            end_date=end_date,
            frequency_data=disaster_data,
            financial_data=pa_data
        )
        
        # Cache result
        hazard_cache.set(cache_key, result)
        
        return result
    
    def get_earthquake_risk(self, zip_code: str) -> Dict[str, Any]:
        """
        Get earthquake risk for a ZIP code
        
        Args:
            zip_code: 5-digit ZIP code
            
        Returns:
            Dictionary with risk score, metrics, and details
        """
        # Check cache first
        cache_key = f"earthquake_{zip_code}_{self.window_years}"
        cached = hazard_cache.get(cache_key)
        if cached:
            return cached
        
        # Get county info
        county_info = get_county_for_zip(zip_code)
        if not county_info:
            return self._error_response(zip_code, "ZIP code not found in crosswalk")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.window_years * 365)
        
        # Get disaster declarations
        disaster_data = self._get_disaster_declarations(
            county_info['county'],
            county_info['state_abbr'],
            start_date,
            "earthquake"
        )
        
        # Get public assistance data
        pa_data = self._get_public_assistance(
            county_info['county'],
            county_info['state_abbr'],
            start_date,
            "earthquake"
        )
        
        # Calculate risk score
        result = self._calculate_risk_score(
            hazard_type="earthquake",
            zip_code=zip_code,
            county=county_info['county'],
            state=county_info['state'],
            state_abbr=county_info['state_abbr'],
            start_date=start_date,
            end_date=end_date,
            frequency_data=disaster_data,
            financial_data=pa_data
        )
        
        # Cache result
        hazard_cache.set(cache_key, result)
        
        return result
    
    def _get_nfip_claims(
        self, 
        zip_codes: List[str], 
        state_abbr: str,
        start_date: datetime
    ) -> Dict[str, Any]:
        """
        Get NFIP claims data for ZIP codes
        
        Args:
            zip_codes: List of ZIP codes
            state_abbr: State abbreviation
            start_date: Start date for claims
            
        Returns:
            Dictionary with claim count and total paid amount
        """
        try:
            # Build filter for multiple ZIPs
            zip_filter = " OR ".join([f"reportedZipcode eq '{z}'" for z in zip_codes[:50]])  # Limit to 50 ZIPs
            date_filter = f"dateOfLoss gt '{start_date.strftime('%Y-%m-%d')}'"
            state_filter = f"state eq '{state_abbr}'"
            
            filter_str = f"({zip_filter}) AND {date_filter} AND {state_filter}"
            
            url = f"{self.OPENFEMA_BASE}/FimaNfipClaims"
            params = {
                "$filter": filter_str,
                "$select": "amountPaidOnBuildingClaim,amountPaidOnContentsClaim,amountPaidOnIncreasedCostOfComplianceClaim",
                "$top": 1000
            }
            
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            claims = data.get('FimaNfipClaims', [])
            
            total_paid = 0
            for claim in claims:
                building = float(claim.get('amountPaidOnBuildingClaim', 0) or 0)
                contents = float(claim.get('amountPaidOnContentsClaim', 0) or 0)
                icc = float(claim.get('amountPaidOnIncreasedCostOfComplianceClaim', 0) or 0)
                total_paid += building + contents + icc
            
            return {
                "count": len(claims),
                "total_amount": total_paid,
                "source": "NFIP Claims"
            }
            
        except Exception as e:
            print(f"Error fetching NFIP claims: {e}")
            return {"count": 0, "total_amount": 0, "source": "NFIP Claims", "error": str(e)}
    
    def _get_disaster_declarations(
        self,
        county: str,
        state_abbr: str,
        start_date: datetime,
        hazard_type: str
    ) -> Dict[str, Any]:
        """
        Get disaster declarations for a county
        
        Args:
            county: County name
            state_abbr: State abbreviation
            start_date: Start date for disasters
            hazard_type: Type of hazard (flood, wildfire, earthquake)
            
        Returns:
            Dictionary with disaster count
        """
        try:
            # Build filter
            date_filter = f"declarationDate ge '{start_date.strftime('%Y-%m-%d')}'"
            state_filter = f"state eq '{state_abbr}'"
            
            # Get incident types for this hazard
            incident_types = self.HAZARD_TYPES.get(hazard_type, [])
            if incident_types:
                type_filter = " OR ".join([f"incidentType eq '{t}'" for t in incident_types])
                filter_str = f"{date_filter} AND {state_filter} AND ({type_filter})"
            else:
                filter_str = f"{date_filter} AND {state_filter}"
            
            url = f"{self.OPENFEMA_BASE}/DisasterDeclarationsSummaries"
            params = {
                "$filter": filter_str,
                "$select": "designatedArea,incidentType,declarationDate",
                "$top": 1000
            }
            
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            disasters = data.get('DisasterDeclarationsSummaries', [])
            
            # Filter by county (designatedArea contains county name)
            county_disasters = [
                d for d in disasters 
                if county.lower() in d.get('designatedArea', '').lower()
            ]
            
            return {
                "count": len(county_disasters),
                "source": "Disaster Declarations"
            }
            
        except Exception as e:
            print(f"Error fetching disaster declarations: {e}")
            return {"count": 0, "source": "Disaster Declarations", "error": str(e)}
    
    def _get_public_assistance(
        self,
        county: str,
        state_abbr: str,
        start_date: datetime,
        hazard_type: str
    ) -> Dict[str, Any]:
        """
        Get public assistance funded projects
        
        Args:
            county: County name
            state_abbr: State abbreviation
            start_date: Start date for projects
            hazard_type: Type of hazard
            
        Returns:
            Dictionary with project count and total obligated amount
        """
        try:
            # Build filter
            date_filter = f"declarationDate ge '{start_date.strftime('%Y-%m-%d')}'"
            state_filter = f"state eq '{state_abbr}'"
            county_filter = f"county eq '{county}'"
            
            filter_str = f"{date_filter} AND {state_filter} AND {county_filter}"
            
            url = f"{self.OPENFEMA_BASE}/PublicAssistanceFundedProjectsDetails"
            params = {
                "$filter": filter_str,
                "$select": "projectAmount,federalShareObligated",
                "$top": 1000
            }
            
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            projects = data.get('PublicAssistanceFundedProjectsDetails', [])
            
            total_obligated = sum(
                float(p.get('federalShareObligated', 0) or 0) 
                for p in projects
            )
            
            return {
                "count": len(projects),
                "total_amount": total_obligated,
                "source": "Public Assistance"
            }
            
        except Exception as e:
            print(f"Error fetching public assistance: {e}")
            return {"count": 0, "total_amount": 0, "source": "Public Assistance", "error": str(e)}
    
    def _calculate_risk_score(
        self,
        hazard_type: str,
        zip_code: str,
        county: str,
        state: str,
        state_abbr: str,
        start_date: datetime,
        end_date: datetime,
        frequency_data: Dict[str, Any],
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate risk score from frequency and financial data
        
        Uses 50/50 blend of frequency and financial impact
        Score is 0-100 with bands: Low (0-25), Moderate (25-50), High (50-75), Severe (75-100)
        
        Args:
            hazard_type: Type of hazard
            zip_code: ZIP code
            county: County name
            state: State name
            state_abbr: State abbreviation
            start_date: Start date of analysis window
            end_date: End date of analysis window
            frequency_data: Disaster frequency data
            financial_data: Financial impact data
            
        Returns:
            Complete risk assessment
        """
        # Frequency score (0-50): based on disaster count
        disaster_count = frequency_data.get('count', 0)
        # Normalize: 0 disasters = 0, 5+ disasters = 50
        frequency_score = min(50, (disaster_count / 5.0) * 50)
        
        # Financial score (0-50): based on total financial impact
        total_financial = financial_data.get('total_amount', 0)
        # Normalize: $0 = 0, $10M+ = 50
        financial_score = min(50, (total_financial / 10_000_000) * 50)
        
        # Combined score
        total_score = frequency_score + financial_score
        
        # Determine band
        if total_score < 25:
            band = "Low"
        elif total_score < 50:
            band = "Moderate"
        elif total_score < 75:
            band = "High"
        else:
            band = "Severe"
        
        # Build drivers list
        drivers = []
        if disaster_count > 0:
            drivers.append(f"{disaster_count} disaster declaration(s) in past {self.window_years} years")
        if total_financial > 0:
            drivers.append(f"${total_financial:,.0f} in total claims/assistance")
        if not drivers:
            drivers.append("No significant historical incidents")
        
        return {
            "hazard_type": hazard_type,
            "zip": zip_code,
            "county": county,
            "state": state,
            "state_abbr": state_abbr,
            "window_years": self.window_years,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "frequency": {
                "disaster_count": disaster_count,
                "score": round(frequency_score, 2),
                "source": frequency_data.get('source', 'Unknown')
            },
            "financial": {
                "total_amount": total_financial,
                "claim_count": financial_data.get('count', 0),
                "score": round(financial_score, 2),
                "source": financial_data.get('source', 'Unknown')
            },
            "risk_score": round(total_score, 2),
            "band": band,
            "drivers": drivers,
            "sources": [
                "OpenFEMA DisasterDeclarationsSummaries",
                "OpenFEMA FimaNfipClaims" if hazard_type == "flood" else "OpenFEMA PublicAssistanceFundedProjectsDetails"
            ]
        }
    
    def _error_response(self, zip_code: str, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "error": error_message,
            "zip": zip_code,
            "risk_score": 0,
            "band": "Unknown"
        }
