"""
Cosmos DB Service - Manages data storage and retrieval from Azure Cosmos DB
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class CosmosDBService:
    """Service for interacting with Azure Cosmos DB"""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None,
        database_name: Optional[str] = None,
        container_name: Optional[str] = None
    ):
        """Initialize Cosmos DB service
        
        Args:
            endpoint: Cosmos DB endpoint URL
            key: Cosmos DB access key
            database_name: Database name
            container_name: Container name
        """
        self.endpoint = endpoint or os.getenv("COSMOS_DB_ENDPOINT")
        self.key = key or os.getenv("COSMOS_DB_KEY")
        self.database_name = database_name or os.getenv("COSMOS_DB_DATABASE", "insurance_data")
        self.container_name = container_name or os.getenv("COSMOS_DB_CONTAINER", "customers")
        
        self.client = None
        self.database = None
        self.container = None
        
        # Initialize Cosmos DB client if credentials are available
        if self.endpoint and self.key:
            try:
                from azure.cosmos import CosmosClient
                self.client = CosmosClient(self.endpoint, self.key)
                self.database = self.client.get_database_client(self.database_name)
                self.container = self.database.get_container_client(self.container_name)
            except ImportError:
                print("Warning: azure-cosmos package not installed. Using mock data.")
            except Exception as e:
                print(f"Warning: Could not connect to Cosmos DB: {e}. Using mock data.")
                
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer record
        
        Args:
            customer_data: Customer data dictionary
            
        Returns:
            Created customer record
        """
        if not self.container:
            return {"error": "Cosmos DB not configured", "status": "using_mock_data"}
            
        try:
            # Add metadata
            customer_data["created_at"] = datetime.now().isoformat()
            customer_data["updated_at"] = datetime.now().isoformat()
            customer_data["document_type"] = "customer"
            
            # Create document
            result = self.container.create_item(body=customer_data)
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
        if not self.container:
            return None
            
        try:
            # Query for customer
            query = "SELECT * FROM c WHERE c.id = @customer_id"
            parameters = [{"name": "@customer_id", "value": customer_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
        except Exception as e:
            print(f"Error retrieving customer: {e}")
            return None
            
    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer record
        
        Args:
            customer_id: Customer ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated customer record
        """
        if not self.container:
            return {"error": "Cosmos DB not configured"}
            
        try:
            # Get existing customer
            customer = self.get_customer(customer_id)
            if not customer:
                return {"error": f"Customer {customer_id} not found"}
                
            # Update fields
            customer.update(updates)
            customer["updated_at"] = datetime.now().isoformat()
            
            # Replace document
            result = self.container.replace_item(
                item=customer_id,
                body=customer
            )
            return result
        except Exception as e:
            return {"error": f"Failed to update customer: {str(e)}"}
            
    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        """Search customers by name, email, or phone
        
        Args:
            query: Search query string
            
        Returns:
            List of matching customers
        """
        if not self.container:
            return []
            
        try:
            # Build search query
            sql_query = """
                SELECT * FROM c 
                WHERE CONTAINS(LOWER(c.name), @query) 
                   OR CONTAINS(LOWER(c.email), @query)
                   OR CONTAINS(c.phone, @query)
            """
            parameters = [{"name": "@query", "value": query.lower()}]
            
            items = list(self.container.query_items(
                query=sql_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items
        except Exception as e:
            print(f"Error searching customers: {e}")
            return []
            
    def get_customers_by_type(self, customer_type: str) -> List[Dict[str, Any]]:
        """Get customers by type (Premium, Standard, etc.)
        
        Args:
            customer_type: Customer type to filter by
            
        Returns:
            List of customers
        """
        if not self.container:
            return []
            
        try:
            query = "SELECT * FROM c WHERE c.type = @type"
            parameters = [{"name": "@type", "value": customer_type}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items
        except Exception as e:
            print(f"Error retrieving customers by type: {e}")
            return []
            
    def store_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store customer interaction record
        
        Args:
            interaction_data: Interaction data
            
        Returns:
            Created interaction record
        """
        if not self.container:
            return {"error": "Cosmos DB not configured"}
            
        try:
            interaction_data["document_type"] = "interaction"
            interaction_data["created_at"] = datetime.now().isoformat()
            
            result = self.container.create_item(body=interaction_data)
            return result
        except Exception as e:
            return {"error": f"Failed to store interaction: {str(e)}"}
            
    def get_customer_interactions(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent interactions for a customer
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of interactions to return
            
        Returns:
            List of interaction records
        """
        if not self.container:
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
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items
        except Exception as e:
            print(f"Error retrieving interactions: {e}")
            return []
            
    def store_recommendation(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store AI-generated recommendation
        
        Args:
            recommendation_data: Recommendation data
            
        Returns:
            Created recommendation record
        """
        if not self.container:
            return {"error": "Cosmos DB not configured"}
            
        try:
            recommendation_data["document_type"] = "recommendation"
            recommendation_data["created_at"] = datetime.now().isoformat()
            
            result = self.container.create_item(body=recommendation_data)
            return result
        except Exception as e:
            return {"error": f"Failed to store recommendation: {str(e)}"}
            
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics and metrics from Cosmos DB
        
        Returns:
            Dictionary containing analytics data
        """
        if not self.container:
            return {"error": "Cosmos DB not configured"}
            
        try:
            # Get customer count by type
            type_query = """
                SELECT c.type, COUNT(1) as count
                FROM c 
                WHERE c.document_type = 'customer'
                GROUP BY c.type
            """
            
            type_counts = list(self.container.query_items(
                query=type_query,
                enable_cross_partition_query=True
            ))
            
            # Get total customers
            total_query = """
                SELECT VALUE COUNT(1)
                FROM c 
                WHERE c.document_type = 'customer'
            """
            
            total_result = list(self.container.query_items(
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
            
    def is_connected(self) -> bool:
        """Check if connected to Cosmos DB
        
        Returns:
            True if connected, False otherwise
        """
        return self.container is not None
