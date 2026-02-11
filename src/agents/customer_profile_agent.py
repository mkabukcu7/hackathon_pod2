"""
Customer Profile Agent - Manages customer data and rapid lookup with Cosmos DB integration
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.cosmos_db_service import CosmosDBService


# Mock customer database
MOCK_CUSTOMERS = {
    "C001": {
        "id": "C001",
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "+1-555-0101",
        "type": "Premium",
        "status": "Active",
        "join_date": "2020-03-15",
        "last_contact": "2026-01-28",
        "policies": [
            {
                "policy_number": "AUTO-2020-001",
                "type": "Auto Insurance",
                "premium": 1250.00,
                "status": "Active",
                "renewal_date": "2026-03-15",
                "coverage": "Comprehensive"
            },
            {
                "policy_number": "HOME-2021-045",
                "type": "Home Insurance",
                "premium": 1800.00,
                "status": "Active",
                "renewal_date": "2026-05-20",
                "coverage": "Premium"
            }
        ],
        "lifetime_value": 45000.00,
        "claim_history": [
            {
                "claim_id": "CLM-2024-156",
                "date": "2024-06-10",
                "type": "Auto - Minor Collision",
                "amount": 3500.00,
                "status": "Settled"
            }
        ],
        "risk_score": 0.25,
        "satisfaction_score": 4.5
    },
    "C002": {
        "id": "C002",
        "name": "Michael Chen",
        "email": "m.chen@techcorp.com",
        "phone": "+1-555-0202",
        "type": "Standard",
        "status": "Active",
        "join_date": "2022-08-10",
        "last_contact": "2025-12-15",
        "policies": [
            {
                "policy_number": "AUTO-2022-089",
                "type": "Auto Insurance",
                "premium": 980.00,
                "status": "Active",
                "renewal_date": "2026-08-10",
                "coverage": "Standard"
            }
        ],
        "lifetime_value": 8500.00,
        "claim_history": [],
        "risk_score": 0.15,
        "satisfaction_score": 4.2
    },
    "C003": {
        "id": "C003",
        "name": "Jennifer Martinez",
        "email": "jmartinez@consulting.com",
        "phone": "+1-555-0303",
        "type": "Premium",
        "status": "Active",
        "join_date": "2019-01-20",
        "last_contact": "2026-02-05",
        "policies": [
            {
                "policy_number": "HOME-2019-012",
                "type": "Home Insurance",
                "premium": 2200.00,
                "status": "Active",
                "renewal_date": "2026-01-20",
                "coverage": "Premium Plus"
            },
            {
                "policy_number": "AUTO-2019-013",
                "type": "Auto Insurance",
                "premium": 1400.00,
                "status": "Active",
                "renewal_date": "2026-01-20",
                "coverage": "Comprehensive"
            },
            {
                "policy_number": "LIFE-2020-078",
                "type": "Life Insurance",
                "premium": 3200.00,
                "status": "Active",
                "renewal_date": "2026-06-01",
                "coverage": "Term Life - 500K"
            }
        ],
        "lifetime_value": 125000.00,
        "claim_history": [],
        "risk_score": 0.10,
        "satisfaction_score": 4.8
    }
}


class CustomerProfileAgent:
    """Agent for customer profile management and lookup with Cosmos DB backend"""
    
    def __init__(self, use_cosmos_db: bool = True):
        """Initialize the Customer Profile Agent
        
        Args:
            use_cosmos_db: Whether to use Cosmos DB (True) or mock data (False)
        """
        self.customers = MOCK_CUSTOMERS
        self.use_cosmos_db = use_cosmos_db
        self.cosmos_service = None
        
        if use_cosmos_db:
            try:
                self.cosmos_service = CosmosDBService()
                if self.cosmos_service.is_connected():
                    print("Customer Profile Agent connected to Cosmos DB")
                else:
                    print("Cosmos DB not configured, using mock data")
                    self.use_cosmos_db = False
            except Exception as e:
                print(f"Failed to connect to Cosmos DB: {e}, using mock data")
                self.use_cosmos_db = False
        
    def search_customer(self, query: str) -> List[Dict[str, Any]]:
        """Search for customers by name, email, phone, or ID
        
        Args:
            query: Search query string
            
        Returns:
            List of matching customer profiles
        """
        # Try Cosmos DB first if available
        if self.use_cosmos_db and self.cosmos_service:
            try:
                cosmos_results = self.cosmos_service.search_customers(query)
                if cosmos_results:
                    return [self._get_customer_summary(c) for c in cosmos_results]
            except Exception as e:
                print(f"Cosmos DB search failed: {e}, falling back to mock data")
        
        # Fall back to mock data
        query_lower = query.lower()
        results = []
        
        for customer_id, customer in self.customers.items():
            if (query_lower in customer["name"].lower() or
                query_lower in customer["email"].lower() or
                query_lower in customer["phone"] or
                query_lower in customer_id.lower()):
                results.append(self._get_customer_summary(customer))
                
        return results
        
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get complete customer profile
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Complete customer profile with all details
        """
        # Try Cosmos DB first if available
        if self.use_cosmos_db and self.cosmos_service:
            try:
                cosmos_customer = self.cosmos_service.get_customer(customer_id)
                if cosmos_customer:
                    cosmos_customer["retrieved_at"] = datetime.now().isoformat()
                    cosmos_customer["data_source"] = "cosmos_db"
                    return cosmos_customer
            except Exception as e:
                print(f"Cosmos DB get failed: {e}, falling back to mock data")
        
        # Fall back to mock data
        customer = self.customers.get(customer_id)
        
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
            
        return {
            **customer,
            "retrieved_at": datetime.now().isoformat(),
            "data_source": "mock_data"
        }
        
    def get_customer_policies(self, customer_id: str) -> Dict[str, Any]:
        """Get customer's insurance policies
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary containing policy information
        """
        customer = self.customers.get(customer_id)
        
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
            
        return {
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "policies": customer["policies"],
            "total_premium": sum(p["premium"] for p in customer["policies"]),
            "policy_count": len(customer["policies"]),
            "retrieved_at": datetime.now().isoformat()
        }
        
    def get_customer_claims(self, customer_id: str) -> Dict[str, Any]:
        """Get customer's claim history
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary containing claim history
        """
        customer = self.customers.get(customer_id)
        
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
            
        return {
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "claim_history": customer["claim_history"],
            "total_claims": len(customer["claim_history"]),
            "total_claimed": sum(c["amount"] for c in customer["claim_history"]),
            "retrieved_at": datetime.now().isoformat()
        }
        
    def get_customer_timeline(self, customer_id: str) -> Dict[str, Any]:
        """Get customer interaction timeline
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Timeline of customer interactions and events
        """
        customer = self.customers.get(customer_id)
        
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
            
        # Build timeline from various sources
        timeline = []
        
        # Add join date
        timeline.append({
            "date": customer["join_date"],
            "type": "customer_joined",
            "description": "Customer joined",
            "details": f"Became a {customer['type']} customer"
        })
        
        # Add policy start dates
        for policy in customer["policies"]:
            timeline.append({
                "date": policy.get("start_date", customer["join_date"]),
                "type": "policy_added",
                "description": f"Added {policy['type']}",
                "details": f"Policy {policy['policy_number']}"
            })
            
        # Add claims
        for claim in customer["claim_history"]:
            timeline.append({
                "date": claim["date"],
                "type": "claim_filed",
                "description": claim["type"],
                "details": f"Claim {claim['claim_id']} - ${claim['amount']:,.2f}"
            })
            
        # Add last contact
        timeline.append({
            "date": customer["last_contact"],
            "type": "contact",
            "description": "Last contact",
            "details": "Customer service interaction"
        })
        
        # Sort by date
        timeline.sort(key=lambda x: x["date"], reverse=True)
        
        return {
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "timeline": timeline,
            "retrieved_at": datetime.now().isoformat()
        }
        
    def _get_customer_summary(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Get customer summary for search results"""
        return {
            "id": customer["id"],
            "name": customer["name"],
            "email": customer["email"],
            "type": customer["type"],
            "status": customer["status"],
            "policy_count": len(customer["policies"]),
            "lifetime_value": customer["lifetime_value"]
        }
