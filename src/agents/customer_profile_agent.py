"""
Customer Profile Agent - Manages customer data and rapid lookup with Parquet, Cosmos DB integration
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random
import sys
import os
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.cosmos_db_service import CosmosDBService
from services.openai_service import chat_completion, is_available as openai_available
from utils.parquet_loader import (
    get_customers,
    get_policies,
    get_claims,
    get_customer_features
)


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
    """Agent for customer profile management and lookup with Parquet, Cosmos DB, or mock data backends"""
    
    def __init__(self, use_parquet: bool = True, use_cosmos_db: bool = False):
        """Initialize the Customer Profile Agent
        
        Args:
            use_parquet: Whether to use Parquet data (True) or mock data (False)
            use_cosmos_db: Whether to use Cosmos DB (True) or mock data (False)
        """
        self.customers = MOCK_CUSTOMERS
        self.use_parquet = use_parquet
        self.use_cosmos_db = use_cosmos_db
        self.cosmos_service = None
        self.parquet_data = None
        
        # Try to load Parquet data first
        if use_parquet:
            try:
                self.parquet_data = self._load_parquet_data()
                if self.parquet_data:
                    print("Customer Profile Agent loaded Parquet data")
                    self.use_parquet = True
                else:
                    print("Parquet data not available, trying Cosmos DB or mock data")
                    self.use_parquet = False
            except Exception as e:
                print(f"Failed to load Parquet data: {e}, trying Cosmos DB or mock data")
                self.use_parquet = False
        
        # Try Cosmos DB if Parquet is not available
        if not self.use_parquet and use_cosmos_db:
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
    
    def _load_parquet_data(self) -> Optional[Dict[str, Any]]:
        """Load customer data from Parquet files
        
        Returns:
            Dictionary with parquet dataframes or None if not available
        """
        try:
            customers_df = get_customers()
            policies_df = get_policies()
            claims_df = get_claims()
            
            return {
                'customers_df': customers_df,
                'policies_df': policies_df,
                'claims_df': claims_df
            }
        except Exception as e:
            print(f"Error loading Parquet data: {e}")
            return None
        
    def search_customer(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for customers by ID, state, region, or income band
        
        Args:
            query: Search query string (customer ID, state, region, etc.)
            limit: Maximum number of results to return
            
        Returns:
            List of matching customer summaries
        """
        # Try Parquet data first
        if self.use_parquet and self.parquet_data:
            try:
                return self._search_parquet(query, limit)
            except Exception as e:
                print(f"Parquet search failed: {e}, falling back")

        # Try Cosmos DB if available
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

    def _search_parquet(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search Parquet customer data
        
        Searches across CustomerId, State, Region, IncomeBand, MaritalStatus.
        """
        customers_df = self.parquet_data['customers_df']
        policies_df = self.parquet_data['policies_df']
        query_upper = query.strip().upper()
        query_lower = query.strip().lower()

        # Exact customer ID match
        if query_upper.startswith('C') and query_upper[1:].isdigit():
            mask = customers_df['CustomerId'].str.upper() == query_upper
        elif query_upper.isdigit() and len(query_upper) == 5:
            # ZIP code search
            mask = customers_df['ZipCode'].astype(str) == query_upper
        else:
            # Search across multiple text fields (case-insensitive)
            mask = (
                customers_df['CustomerId'].str.lower().str.contains(query_lower, na=False) |
                customers_df['State'].str.lower().str.contains(query_lower, na=False) |
                customers_df['Region'].str.lower().str.contains(query_lower, na=False) |
                customers_df['IncomeBand'].str.lower().str.contains(query_lower, na=False) |
                customers_df['MaritalStatus'].str.lower().str.contains(query_lower, na=False) |
                customers_df['ZipCode'].astype(str).str.contains(query_lower, na=False)
            )

        matched = customers_df[mask].head(limit)

        if matched.empty:
            return []

        # Get policy counts and total premiums per customer
        customer_ids = matched['CustomerId'].tolist()
        cust_policies = policies_df[policies_df['CustomerId'].isin(customer_ids)]
        policy_counts = cust_policies.groupby('CustomerId').size().to_dict()
        premium_totals = cust_policies.groupby('CustomerId')['Premium'].sum().to_dict()

        results = []
        for _, row in matched.iterrows():
            cid = row['CustomerId']
            results.append({
                "id": cid,
                "name": f"Customer {cid}",
                "email": f"{cid.lower()}@customer.local",
                "type": "Premium" if row.get('IncomeBand') in ('High', 'Very High') else "Standard",
                "status": "Active",
                "state": row.get('State', ''),
                "region": row.get('Region', ''),
                "zip": str(row.get('ZipCode', '')),
                "policy_count": policy_counts.get(cid, 0),
                "lifetime_value": round(premium_totals.get(cid, 0), 2)
            })

        return results
        
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get complete customer profile
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Complete customer profile with all details
        """
        # Try Parquet data first
        if self.use_parquet and self.parquet_data:
            try:
                profile = self._get_parquet_profile(customer_id)
                if profile:
                    return profile
            except Exception as e:
                print(f"Parquet profile lookup failed: {e}, falling back")

        # Try Cosmos DB if available
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

    def _get_parquet_profile(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Build a full customer profile from Parquet data"""
        customers_df = self.parquet_data['customers_df']
        policies_df = self.parquet_data['policies_df']
        claims_df = self.parquet_data['claims_df']

        row = customers_df[customers_df['CustomerId'] == customer_id]
        if row.empty:
            return None
        row = row.iloc[0]

        # Build policies list
        cust_policies = policies_df[policies_df['CustomerId'] == customer_id]
        policies = []
        for _, p in cust_policies.iterrows():
            policies.append({
                "policy_number": p['PolicyId'],
                "type": f"{p['ProductLine']} Insurance",
                "premium": float(p['Premium']),
                "status": p['PolicyStatus'],
                "coverage": p.get('CoverageSummary', 'Standard'),
                "effective_date": str(p.get('EffectiveDate', '')),
                "expiration_date": str(p.get('ExpirationDate', ''))
            })

        # Build claims list
        cust_claims = claims_df[claims_df['CustomerId'] == customer_id]
        claim_history = []
        for _, cl in cust_claims.iterrows():
            claim_history.append({
                "claim_id": cl['ClaimId'],
                "date": str(cl.get('LossDate', '')),
                "type": cl.get('ClaimType', 'Unknown'),
                "amount": float(cl['ClaimAmount']),
                "status": "Settled"
            })

        total_premium = sum(p['premium'] for p in policies)
        income = row.get('IncomeBand', 'Medium')
        customer_type = "Premium" if income in ('High', 'Very High') else "Standard"

        profile = {
            "id": customer_id,
            "name": f"Customer {customer_id}",
            "email": f"{customer_id.lower()}@customer.local",
            "phone": "",
            "zip": str(row.get('ZipCode', '')),
            "type": customer_type,
            "status": "Active",
            "state": row.get('State', ''),
            "region": row.get('Region', ''),
            "county": "",
            "age": int(row.get('Age', 0)),
            "marital_status": row.get('MaritalStatus', ''),
            "has_kids": bool(row.get('HasKids', False)),
            "is_homeowner": bool(row.get('IsHomeOwner', False)),
            "income_band": income,
            "join_date": str(row.get('ingest_date', '')),
            "last_contact": datetime.now().strftime('%Y-%m-%d'),
            "policies": policies,
            "lifetime_value": round(total_premium, 2),
            "claim_history": claim_history,
            "risk_score": round(len(claim_history) / max(len(policies), 1) * 0.5, 2),
            "satisfaction_score": round(4.0 + random.uniform(0, 1), 1),
            "retrieved_at": datetime.now().isoformat(),
            "data_source": "parquet"
        }

        # Enrich with AI-generated summary
        ai_summary = self._ai_generate_summary(profile)
        if ai_summary:
            profile["ai_summary"] = ai_summary
            profile["ai_generated"] = True
        else:
            profile["ai_generated"] = False

        return profile
        
    # ---- Azure OpenAI helpers ------------------------------------------------

    def _ai_generate_summary(self, profile: Dict[str, Any]) -> Optional[str]:
        """Generate an AI-powered plain-language customer summary.

        Uses GPT-4o-mini to produce a concise narrative useful for agents
        preparing for a customer call or policy review.

        Returns:
            Summary string, or None if AI is unavailable.
        """
        if not openai_available():
            return None

        try:
            policies_text = ", ".join(
                f"{p['type']} (${p['premium']:,.0f}, {p['status']})"
                for p in profile.get("policies", [])
            ) or "No active policies"

            claims_text = ", ".join(
                f"{c['type']} ${c['amount']:,.0f} ({c['status']})"
                for c in profile.get("claim_history", [])
            ) or "No claims on file"

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an insurance agent assistant. Write a concise "
                        "2-3 sentence customer summary useful for a call-center "
                        "agent about to speak with this customer. Include key "
                        "risk factors, value indicators, and conversation tips. "
                        "Do NOT use markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Customer {profile['id']} — {profile.get('type', 'Standard')} tier, "
                        f"Age {profile.get('age', 'N/A')}, {profile.get('state', 'N/A')} "
                        f"({profile.get('region', '')}), "
                        f"Income: {profile.get('income_band', 'N/A')}, "
                        f"Homeowner: {profile.get('is_homeowner', False)}, "
                        f"Policies: {policies_text}. "
                        f"Claims: {claims_text}. "
                        f"Lifetime value: ${profile.get('lifetime_value', 0):,.0f}."
                    ),
                },
            ]

            return chat_completion(messages, temperature=0.5, max_tokens=250)
        except Exception as e:
            print(f"AI summary generation failed: {e}")
            return None

    def get_customer_policies(self, customer_id: str) -> Dict[str, Any]:
        """Get customer's insurance policies
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary containing policy information
        """
        # Try Parquet data first
        if self.use_parquet and self.parquet_data:
            try:
                policies_df = self.parquet_data['policies_df']
                cust_policies = policies_df[policies_df['CustomerId'] == customer_id]
                if not cust_policies.empty:
                    policies = []
                    for _, p in cust_policies.iterrows():
                        policies.append({
                            "policy_number": p['PolicyId'],
                            "type": f"{p['ProductLine']} Insurance",
                            "premium": float(p['Premium']),
                            "status": p['PolicyStatus'],
                            "coverage": p.get('CoverageSummary', 'Standard'),
                            "effective_date": str(p.get('EffectiveDate', '')),
                            "expiration_date": str(p.get('ExpirationDate', ''))
                        })
                    return {
                        "customer_id": customer_id,
                        "customer_name": f"Customer {customer_id}",
                        "policies": policies,
                        "total_premium": sum(p['premium'] for p in policies),
                        "policy_count": len(policies),
                        "retrieved_at": datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"Parquet policies lookup failed: {e}, falling back")

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

    def get_stats(self) -> Dict[str, Any]:
        """Get overall customer statistics
        
        Returns:
            Dictionary with total customers, policies, claims counts
        """
        if self.use_parquet and self.parquet_data:
            customers_df = self.parquet_data['customers_df']
            policies_df = self.parquet_data['policies_df']
            claims_df = self.parquet_data['claims_df']
            active_policies = policies_df[policies_df['PolicyStatus'] == 'Active'] if 'PolicyStatus' in policies_df.columns else policies_df
            return {
                "total_customers": len(customers_df),
                "total_policies": len(policies_df),
                "active_policies": len(active_policies),
                "total_claims": len(claims_df),
                "total_premium": round(float(policies_df['Premium'].sum()), 2),
                "avg_premium": round(float(policies_df['Premium'].mean()), 2),
                "states": sorted(customers_df['State'].dropna().unique().tolist()),
                "regions": sorted(customers_df['Region'].dropna().unique().tolist()),
                "data_source": "parquet"
            }
        else:
            return {
                "total_customers": len(self.customers),
                "total_policies": sum(len(c["policies"]) for c in self.customers.values()),
                "active_policies": sum(len(c["policies"]) for c in self.customers.values()),
                "total_claims": sum(len(c["claim_history"]) for c in self.customers.values()),
                "data_source": "mock"
            }
