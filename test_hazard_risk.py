"""
Tests for Hazard Risk Agent and related utilities
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.zip_crosswalk import get_county_for_zip, get_zips_for_county
from agents.hazard_risk_agent import HazardRiskAgent


class TestZipCrosswalk:
    """Tests for ZIP to county crosswalk utility"""
    
    def test_get_county_for_zip_valid(self):
        """Test getting county for a valid ZIP code"""
        result = get_county_for_zip('90001')
        assert result is not None
        assert result['county'] == 'Los Angeles'
        assert result['state'] == 'California'
        assert result['state_abbr'] == 'CA'
    
    def test_get_county_for_zip_invalid(self):
        """Test getting county for an invalid ZIP code"""
        result = get_county_for_zip('99999')
        assert result is None
    
    def test_get_zips_for_county(self):
        """Test getting ZIPs for a county"""
        zips = get_zips_for_county('Los Angeles', 'CA')
        assert len(zips) > 0
        assert '90001' in zips
        assert '90002' in zips
    
    def test_get_zips_for_county_invalid(self):
        """Test getting ZIPs for an invalid county"""
        zips = get_zips_for_county('InvalidCounty', 'XX')
        assert len(zips) == 0


class TestHazardRiskAgent:
    """Tests for Hazard Risk Agent"""
    
    @pytest.fixture
    def agent(self):
        """Create a HazardRiskAgent instance"""
        return HazardRiskAgent(window_years=10)
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client"""
        mock_client = MagicMock()
        return mock_client
    
    def test_agent_initialization(self, agent):
        """Test agent can be initialized"""
        assert agent is not None
        assert agent.window_years == 10
        assert agent.timeout == 30
    
    def test_flood_risk_invalid_zip(self, agent):
        """Test flood risk with invalid ZIP code"""
        result = agent.get_flood_risk('99999')
        assert 'error' in result
        assert result['zip'] == '99999'
    
    def test_wildfire_risk_invalid_zip(self, agent):
        """Test wildfire risk with invalid ZIP code"""
        result = agent.get_wildfire_risk('99999')
        assert 'error' in result
        assert result['zip'] == '99999'
    
    def test_earthquake_risk_invalid_zip(self, agent):
        """Test earthquake risk with invalid ZIP code"""
        result = agent.get_earthquake_risk('99999')
        assert 'error' in result
        assert result['zip'] == '99999'
    
    @patch('agents.hazard_risk_agent.HazardRiskAgent._get_nfip_claims')
    @patch('agents.hazard_risk_agent.HazardRiskAgent._get_disaster_declarations')
    def test_flood_risk_with_mocked_data(self, mock_disasters, mock_nfip, agent):
        """Test flood risk calculation with mocked OpenFEMA data"""
        # Mock the OpenFEMA responses
        mock_nfip.return_value = {
            'count': 10,
            'total_amount': 500000,
            'source': 'NFIP Claims'
        }
        mock_disasters.return_value = {
            'count': 2,
            'source': 'Disaster Declarations'
        }
        
        result = agent.get_flood_risk('90001')
        
        # Verify response structure
        assert 'hazard_type' in result
        assert result['hazard_type'] == 'flood'
        assert 'zip' in result
        assert result['zip'] == '90001'
        assert 'county' in result
        assert result['county'] == 'Los Angeles'
        assert 'risk_score' in result
        assert 'band' in result
        assert result['band'] in ['Low', 'Moderate', 'High', 'Severe']
        assert 'drivers' in result
        assert 'sources' in result
        assert 'frequency' in result
        assert 'financial' in result
    
    @patch('agents.hazard_risk_agent.HazardRiskAgent._get_public_assistance')
    @patch('agents.hazard_risk_agent.HazardRiskAgent._get_disaster_declarations')
    def test_wildfire_risk_with_mocked_data(self, mock_disasters, mock_pa, agent):
        """Test wildfire risk calculation with mocked OpenFEMA data"""
        # Mock the OpenFEMA responses
        mock_pa.return_value = {
            'count': 5,
            'total_amount': 2000000,
            'source': 'Public Assistance'
        }
        mock_disasters.return_value = {
            'count': 3,
            'source': 'Disaster Declarations'
        }
        
        result = agent.get_wildfire_risk('90001')
        
        # Verify response structure
        assert 'hazard_type' in result
        assert result['hazard_type'] == 'wildfire'
        assert 'zip' in result
        assert 'risk_score' in result
        assert 'band' in result
    
    def test_calculate_risk_score_low(self, agent):
        """Test risk score calculation for low risk"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10 * 365)
        
        result = agent._calculate_risk_score(
            hazard_type='flood',
            zip_code='90001',
            county='Los Angeles',
            state='California',
            state_abbr='CA',
            start_date=start_date,
            end_date=end_date,
            frequency_data={'count': 0, 'source': 'Test'},
            financial_data={'count': 0, 'total_amount': 0, 'source': 'Test'}
        )
        
        assert result['risk_score'] == 0
        assert result['band'] == 'Low'
    
    def test_calculate_risk_score_high(self, agent):
        """Test risk score calculation for high risk"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10 * 365)
        
        result = agent._calculate_risk_score(
            hazard_type='flood',
            zip_code='90001',
            county='Los Angeles',
            state='California',
            state_abbr='CA',
            start_date=start_date,
            end_date=end_date,
            frequency_data={'count': 10, 'source': 'Test'},
            financial_data={'count': 100, 'total_amount': 20000000, 'source': 'Test'}
        )
        
        assert result['risk_score'] == 100
        assert result['band'] == 'Severe'


class TestHazardRiskAPI:
    """Tests for Hazard Risk API endpoints"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock HazardRiskAgent"""
        agent = Mock(spec=HazardRiskAgent)
        
        # Mock response for valid ZIP
        agent.get_flood_risk.return_value = {
            'hazard_type': 'flood',
            'zip': '90001',
            'county': 'Los Angeles',
            'state': 'California',
            'state_abbr': 'CA',
            'window_years': 10,
            'risk_score': 35.5,
            'band': 'Moderate',
            'drivers': ['Test driver'],
            'sources': ['OpenFEMA']
        }
        
        return agent
    
    def test_api_endpoints_exist(self):
        """Test that hazard risk API endpoints are defined"""
        from api import app
        
        routes = [route.path for route in app.routes]
        
        assert '/api/risk/flood' in routes
        assert '/api/risk/wildfire' in routes
        assert '/api/risk/earthquake' in routes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
