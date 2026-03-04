"""
Cosmos DB Service - Manages data storage and retrieval from Azure Cosmos DB
Supports all 7 insurance data containers with Entra ID authentication.
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


# All containers in the insurance_data database
CONTAINERS = [
    "customers", "policies", "claims", "customer_features",
    "external_signals", "producers", "producer_activity"
]


class CosmosDBService:
    """Service for interacting with Azure Cosmos DB (multi-container, Entra ID auth)"""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        database_name: Optional[str] = None,
    ):
        """Initialize Cosmos DB service with Entra ID (service principal) authentication.
        
        Args:
            endpoint: Cosmos DB endpoint URL
            database_name: Database name
        """
        self.endpoint = endpoint or os.getenv("COSMOS_DB_ENDPOINT")
        self.database_name = database_name or os.getenv("COSMOS_DB_DATABASE", "insurance_data")
        
        self.client = None
        self.database = None
        self._containers: Dict[str, Any] = {}
        
        if self.endpoint:
            try:
                from azure.cosmos import CosmosClient
                from azure.identity import ClientSecretCredential, DefaultAzureCredential
                
                credential = None
                cosmos_scope = "https://cosmos.azure.com/.default"
                
                # Priority 1: Service principal (explicit credentials)
                tenant_id = os.getenv("AZURE_TENANT_ID")
                client_id = os.getenv("AZURE_CLIENT_ID")
                client_secret = os.getenv("AZURE_CLIENT_SECRET")
                
                if all([tenant_id, client_id, client_secret]):
                    try:
                        service_principal_credential = ClientSecretCredential(tenant_id, client_id, client_secret)
                        service_principal_credential.get_token(cosmos_scope)
                        credential = service_principal_credential
                        print("Cosmos DB auth: using service principal")
                    except Exception as e:
                        print(f"Cosmos DB service principal auth failed: {e}")

                if credential is None:
                    # Priority 2: DefaultAzureCredential (az login, managed identity, etc.)
                    try:
                        default_credential = DefaultAzureCredential()
                        default_credential.get_token(cosmos_scope)
                        credential = default_credential
                        print("Cosmos DB auth: using DefaultAzureCredential (az login / managed identity)")
                    except Exception as e:
                        print(f"Cosmos DB DefaultAzureCredential auth failed: {e}")

                if credential is None:
                    # Priority 3: Key-based auth (may fail if disabled by policy)
                    key = os.getenv("COSMOS_DB_KEY")
                    if key:
                        self.client = CosmosClient(self.endpoint, key)
                        print("Cosmos DB auth: using key-based auth")
                
                if credential and not self.client:
                    self.client = CosmosClient(self.endpoint, credential=credential)
                        
                if self.client:
                    self.database = self.client.get_database_client(self.database_name)
                    # Pre-initialize container clients
                    for name in CONTAINERS:
                        self._containers[name] = self.database.get_container_client(name)
            except ImportError:
                print("Warning: azure-cosmos / azure-identity packages not installed.")
            except Exception as e:
                print(f"Warning: Could not connect to Cosmos DB: {e}")

    def _get_container(self, container_name: str):
        """Get a container client by name."""
        return self._containers.get(container_name)
                
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer record
        
        Args:
            customer_data: Customer data dictionary
            
        Returns:
            Created customer record
        """
        container = self._get_container("customers")
        if not container:
            return {"error": "Cosmos DB not configured", "status": "using_mock_data"}
            
        try:
            customer_data["created_at"] = datetime.now().isoformat()
            customer_data["updated_at"] = datetime.now().isoformat()
            customer_data["document_type"] = "customer"
            result = container.create_item(body=customer_data)
            return result
        except Exception as e:
            return {"error": f"Failed to create customer: {str(e)}"}
            
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer data or None if not found
        """
        container = self._get_container("customers")
        if not container:
            return None
            
        try:
            query = "SELECT * FROM c WHERE c.id = @customer_id"
            parameters = [{"name": "@customer_id", "value": customer_id}]
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception as e:
            print(f"Error retrieving customer: {e}")
            return None
            
    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer record"""
        container = self._get_container("customers")
        if not container:
            return {"error": "Cosmos DB not configured"}
            
        try:
            customer = self.get_customer(customer_id)
            if not customer:
                return {"error": f"Customer {customer_id} not found"}
            customer.update(updates)
            customer["updated_at"] = datetime.now().isoformat()
            result = container.replace_item(item=customer_id, body=customer)
            return result
        except Exception as e:
            return {"error": f"Failed to update customer: {str(e)}"}
            
    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        """Search customers by name, email, or phone"""
        container = self._get_container("customers")
        if not container:
            return []
            
        try:
            sql_query = """
                SELECT * FROM c 
                WHERE CONTAINS(LOWER(c.name), @query) 
                   OR CONTAINS(LOWER(c.email), @query)
                   OR CONTAINS(c.phone, @query)
            """
            parameters = [{"name": "@query", "value": query.lower()}]
            items = list(container.query_items(
                query=sql_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            print(f"Error searching customers: {e}")
            return []
            
    def get_customers_by_type(self, customer_type: str) -> List[Dict[str, Any]]:
        """Get customers by type (Premium, Standard, etc.)"""
        container = self._get_container("customers")
        if not container:
            return []
            
        try:
            query = "SELECT * FROM c WHERE c.type = @type"
            parameters = [{"name": "@type", "value": customer_type}]
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            print(f"Error retrieving customers by type: {e}")
            return []
            
    def store_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store customer interaction record"""
        container = self._get_container("customers")
        if not container:
            return {"error": "Cosmos DB not configured"}
            
        try:
            interaction_data["document_type"] = "interaction"
            interaction_data["created_at"] = datetime.now().isoformat()
            result = container.create_item(body=interaction_data)
            return result
        except Exception as e:
            return {"error": f"Failed to store interaction: {str(e)}"}
            
    def get_customer_interactions(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent interactions for a customer"""
        container = self._get_container("customers")
        if not container:
            return []
            
        try:
            query = """
                SELECT TOP @limit * FROM c 
                WHERE c.customer_id = @customer_id 
                  AND c.document_type = 'interaction'
                ORDER BY c.created_at DESC
            """
            parameters = [
                {"name": "@customer_id", "value": customer_id},
                {"name": "@limit", "value": limit}
            ]
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            print(f"Error retrieving interactions: {e}")
            return []
            
    def store_recommendation(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store AI-generated recommendation"""
        container = self._get_container("customers")
        if not container:
            return {"error": "Cosmos DB not configured"}
            
        try:
            recommendation_data["document_type"] = "recommendation"
            recommendation_data["created_at"] = datetime.now().isoformat()
            result = container.create_item(body=recommendation_data)
            return result
        except Exception as e:
            return {"error": f"Failed to store recommendation: {str(e)}"}
            
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics and metrics from Cosmos DB"""
        container = self._get_container("customers")
        if not container:
            return {"error": "Cosmos DB not configured"}
            
        try:
            type_query = """
                SELECT c.type, COUNT(1) as count
                FROM c 
                WHERE c.document_type = 'customer'
                GROUP BY c.type
            """
            type_counts = list(container.query_items(
                query=type_query,
                enable_cross_partition_query=True
            ))
            
            total_query = "SELECT VALUE COUNT(1) FROM c WHERE c.document_type = 'customer'"
            total_result = list(container.query_items(
                query=total_query,
                enable_cross_partition_query=True
            ))
            
            return {
                "total_customers": total_result[0] if total_result else 0,
                "customers_by_type": {item["type"]: item["count"] for item in type_counts},
                "retrieved_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to retrieve analytics: {str(e)}"}
            
    # ── Multi-container query methods ────────────────────────────────

    def query_container(self, container_name: str, query: str,
                        parameters: Optional[List[Dict]] = None,
                        max_items: int = 100) -> List[Dict[str, Any]]:
        """Run a SQL query against any container.
        
        Args:
            container_name: Target container (customers, policies, claims, etc.)
            query: Cosmos DB SQL query
            parameters: Optional query parameters
            max_items: Maximum items to return
            
        Returns:
            List of matching documents
        """
        container = self._get_container(container_name)
        if not container:
            return []
        try:
            items = list(container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True,
                max_item_count=max_items
            ))
            return items
        except Exception as e:
            print(f"Error querying {container_name}: {e}")
            return []

    def get_customer_policies(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all policies for a customer."""
        return self.query_container(
            "policies",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}]
        )

    def get_customer_claims(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all claims for a customer."""
        return self.query_container(
            "claims",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}]
        )

    def get_customer_features(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get ML features (churn risk, propensity, etc.) for a customer."""
        results = self.query_container(
            "customer_features",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}],
            max_items=1
        )
        return results[0] if results else None

    def get_customer_signals(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get external signals for a customer."""
        return self.query_container(
            "external_signals",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}]
        )

    def get_producer(self, producer_id: str) -> Optional[Dict[str, Any]]:
        """Get producer by ID."""
        results = self.query_container(
            "producers",
            "SELECT * FROM c WHERE c.ProducerId = @pid",
            [{"name": "@pid", "value": producer_id}],
            max_items=1
        )
        return results[0] if results else None

    def get_producer_activity(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get producer activity for a customer."""
        return self.query_container(
            "producer_activity",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}]
        )

    def get_full_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get a comprehensive customer profile across all containers.
        
        Returns:
            Dictionary with customer, policies, claims, features, signals, and activity
        """
        customer = self.get_customer(customer_id)
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
        
        profile = {
            "customer": customer,
            "policies": self.get_customer_policies(customer_id),
            "claims": self.get_customer_claims(customer_id),
            "features": self.get_customer_features(customer_id),
            "signals": self.get_customer_signals(customer_id),
            "activity": self.get_producer_activity(customer_id),
        }
        
        # Add producer info if customer has a ProducerId
        producer_id = customer.get("ProducerId")
        if producer_id:
            profile["producer"] = self.get_producer(producer_id)
        
        return profile
            
    # ── Search / aggregation helpers ────────────────────────────────

    def search_customers_flexible(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search customers by CustomerId, State, Region, IncomeBand, or ZipCode.

        Mirrors the Parquet _search_parquet logic so callers get identical results.
        """
        query_upper = query.strip().upper()
        query_lower = query.strip().lower()

        # Exact customer ID match
        if query_upper.startswith("C") and query_upper[1:].isdigit():
            return self.query_container(
                "customers",
                "SELECT * FROM c WHERE c.CustomerId = @q",
                [{"name": "@q", "value": query_upper}],
                max_items=limit,
            )

        # 5-digit ZIP code
        if query_upper.isdigit() and len(query_upper) == 5:
            return self.query_container(
                "customers",
                "SELECT * FROM c WHERE c.ZipCode = @q",
                [{"name": "@q", "value": query_upper}],
                max_items=limit,
            )

        # Free-text: search across multiple fields (case-insensitive via LOWER)
        sql = (
            "SELECT * FROM c WHERE "
            "CONTAINS(LOWER(c.CustomerId), @q) OR "
            "CONTAINS(LOWER(c.State), @q) OR "
            "CONTAINS(LOWER(c.Region), @q) OR "
            "CONTAINS(LOWER(c.IncomeBand), @q) OR "
            "CONTAINS(LOWER(c.MaritalStatus), @q) OR "
            "CONTAINS(c.ZipCode, @q)"
        )
        return self.query_container(
            "customers", sql,
            [{"name": "@q", "value": query_lower}],
            max_items=limit,
        )

    def get_customer_count(self) -> int:
        """Return total number of customer documents."""
        results = self.query_container(
            "customers",
            "SELECT VALUE COUNT(1) FROM c",
        )
        return results[0] if results else 0

    def get_policy_count(self) -> int:
        """Return total number of policy documents."""
        results = self.query_container(
            "policies",
            "SELECT VALUE COUNT(1) FROM c",
        )
        return results[0] if results else 0

    def get_active_policy_count(self) -> int:
        """Return number of active policies."""
        results = self.query_container(
            "policies",
            "SELECT VALUE COUNT(1) FROM c WHERE c.PolicyStatus = 'Active'",
        )
        return results[0] if results else 0

    def get_claim_count(self) -> int:
        """Return total number of claim documents."""
        results = self.query_container(
            "claims",
            "SELECT VALUE COUNT(1) FROM c",
        )
        return results[0] if results else 0

    def get_total_premium(self) -> float:
        """Return sum of all premiums."""
        results = self.query_container(
            "policies",
            "SELECT VALUE SUM(c.Premium) FROM c",
        )
        return float(results[0]) if results and results[0] is not None else 0.0

    def get_avg_premium(self) -> float:
        """Return average premium."""
        results = self.query_container(
            "policies",
            "SELECT VALUE AVG(c.Premium) FROM c",
        )
        return float(results[0]) if results and results[0] is not None else 0.0

    def get_distinct_states(self) -> List[str]:
        """Return sorted list of distinct customer states."""
        results = self.query_container(
            "customers",
            "SELECT DISTINCT VALUE c.State FROM c WHERE IS_DEFINED(c.State)",
            max_items=100,
        )
        return sorted([s for s in results if s])

    def get_distinct_regions(self) -> List[str]:
        """Return sorted list of distinct customer regions."""
        results = self.query_container(
            "customers",
            "SELECT DISTINCT VALUE c.Region FROM c WHERE IS_DEFINED(c.Region)",
            max_items=20,
        )
        return sorted([r for r in results if r])

    def get_external_signals_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get external signals for a specific customer."""
        return self.query_container(
            "external_signals",
            "SELECT * FROM c WHERE c.CustomerId = @cid",
            [{"name": "@cid", "value": customer_id}],
        )

    def is_connected(self) -> bool:
        """Check if connected to Cosmos DB
        
        Returns:
            True if connected, False otherwise
        """
        return self.client is not None and len(self._containers) > 0
