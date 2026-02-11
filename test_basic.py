"""
Simple test script to verify the multi-agent system works
"""
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from agents import WeatherAgent, EnvironmentalAgent, AzureAgent
        from orchestrator import AgentOrchestrator
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_agent_initialization():
    """Test that agents can be initialized"""
    print("\nTesting agent initialization...")
    try:
        from agents import WeatherAgent, EnvironmentalAgent, AzureAgent
        
        weather = WeatherAgent()
        print("✓ WeatherAgent initialized")
        
        environmental = EnvironmentalAgent()
        print("✓ EnvironmentalAgent initialized")
        
        azure = AzureAgent()
        print("✓ AzureAgent initialized")
        
        return True
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        return False

def test_orchestrator():
    """Test that orchestrator works"""
    print("\nTesting orchestrator...")
    try:
        from orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        print("✓ Orchestrator initialized")
        
        # Test capabilities
        capabilities = orchestrator.get_available_capabilities()
        assert len(capabilities) == 3
        print("✓ Capabilities retrieved")
        
        # Test basic query (without API keys, will return mock data or error)
        result = orchestrator.process_query("test query")
        assert "query" in result
        print("✓ Query processing works")
        
        return True
    except Exception as e:
        print(f"✗ Orchestrator test failed: {e}")
        return False

def test_environmental_agent():
    """Test environmental agent methods"""
    print("\nTesting environmental agent...")
    try:
        from agents import EnvironmentalAgent
        
        agent = EnvironmentalAgent()
        
        # Test pollution data (mock implementation)
        result = agent.get_pollution_data("London")
        assert "location" in result
        assert "pollution_levels" in result
        print("✓ Pollution data retrieval works")
        
        # Test climate data (mock implementation)
        result = agent.get_climate_data("Europe")
        assert "region" in result
        assert "temperature_trends" in result
        print("✓ Climate data retrieval works")
        
        return True
    except Exception as e:
        print(f"✗ Environmental agent test failed: {e}")
        return False

def test_azure_agent():
    """Test Azure agent methods"""
    print("\nTesting Azure agent...")
    try:
        from agents import AzureAgent
        
        agent = AzureAgent()
        
        # Test service health (mock implementation)
        result = agent.get_service_health()
        assert "overall_status" in result
        print("✓ Service health retrieval works")
        
        # Test cost analysis (mock implementation)
        result = agent.get_cost_analysis()
        assert "total_cost" in result
        print("✓ Cost analysis works")
        
        return True
    except Exception as e:
        print(f"✗ Azure agent test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Multi-Agent System - Basic Tests")
    print("="*60)
    
    tests = [
        test_imports,
        test_agent_initialization,
        test_orchestrator,
        test_environmental_agent,
        test_azure_agent
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
