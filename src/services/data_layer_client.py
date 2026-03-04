"""
Data Layer Client — HTTP client for the Azure Functions data layer.

Drop-in replacement for CosmosDBService. Agents import this instead
of connecting to Cosmos DB directly. All data access goes through
the Azure Functions REST API.

Usage:
    from services.data_layer_client import DataLayerClient
    
    client = DataLayerClient()  # reads DATA_LAYER_URL from env
    customer = client.get_customer("C0000481")
    profile = client.get_full_customer_profile("C0000481")
    results = client.search_customers("Texas")
"""
import os
import logging
from typing import Dict, Any, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0


class DataLayerClient:
    """HTTP client for the Azure Functions data access layer.
    
    Provides the same interface as CosmosDBService so agents can
    switch with minimal code changes.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = (base_url or os.getenv("DATA_LAYER_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("DATA_LAYER_API_KEY", "")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        self._closed = False

        if not self.base_url:
            logger.warning("DATA_LAYER_URL not set — DataLayerClient will not function.")

    # ── Internal HTTP helpers ────────────────────────────────────────

    def _get(self, path: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Make a GET request to the data layer."""
        if self._closed or not self.base_url:
            return None
        url = f"{self.base_url}/api/{path.lstrip('/')}"
        headers = {}
        if self.api_key:
            headers["x-functions-key"] = self.api_key
        try:
            resp = self._client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Data layer HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Data layer request failed: {e}")
            return None

    def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        if self._closed:
            return
        self._client.close()
        self._closed = True

    def __enter__(self) -> "DataLayerClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    # ── Health ───────────────────────────────────────────────────────

    def is_connected(self) -> bool:
        """Check if the data layer is reachable and connected to DB."""
        result = self._get("health")
        return result is not None and result.get("status") == "healthy"

    # ── Customer operations ──────────────────────────────────────────

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID."""
        return self._get(f"customers/{customer_id}")

    def search_customers(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search customers by ID, state, region, ZIP, etc."""
        result = self._get("search/customers", params={"q": query, "limit": limit})
        if result and "results" in result:
            return result["results"]
        return []

    def search_customers_flexible(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Alias for search_customers — matches CosmosDBService interface."""
        return self.search_customers(query, limit)

    # ── Related entities ─────────────────────────────────────────────

    def get_customer_policies(self, customer_id: str) -> List[Dict[str, Any]]:
        result = self._get(f"customers/{customer_id}/policies")
        return result.get("policies", []) if result else []

    def get_customer_claims(self, customer_id: str) -> List[Dict[str, Any]]:
        result = self._get(f"customers/{customer_id}/claims")
        return result.get("claims", []) if result else []

    def get_customer_features(self, customer_id: str) -> Optional[Dict[str, Any]]:
        return self._get(f"customers/{customer_id}/features")

    def get_customer_signals(self, customer_id: str) -> List[Dict[str, Any]]:
        result = self._get(f"customers/{customer_id}/signals")
        return result.get("signals", []) if result else []

    def get_producer(self, producer_id: str) -> Optional[Dict[str, Any]]:
        return self._get(f"producers/{producer_id}")

    def get_producer_activity(self, customer_id: str) -> List[Dict[str, Any]]:
        result = self._get(f"customers/{customer_id}/activity")
        return result.get("activity", []) if result else []

    # ── Full profile ─────────────────────────────────────────────────

    def get_full_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get comprehensive profile (customer + policies + claims + features + signals + activity)."""
        result = self._get(f"customers/{customer_id}/full")
        return result if result else {"error": f"Customer {customer_id} not found"}

    # ── Aggregations ─────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        result = self._get("stats")
        return result if result else {}

    def get_customer_count(self) -> int:
        return self.get_stats().get("customer_count", 0)

    def get_policy_count(self) -> int:
        return self.get_stats().get("policy_count", 0)

    def get_active_policy_count(self) -> int:
        return self.get_stats().get("active_policy_count", 0)

    def get_claim_count(self) -> int:
        return self.get_stats().get("claim_count", 0)

    def get_total_premium(self) -> float:
        return self.get_stats().get("total_premium", 0.0)

    def get_avg_premium(self) -> float:
        return self.get_stats().get("avg_premium", 0.0)

    def get_distinct_states(self) -> List[str]:
        return self.get_stats().get("states", [])

    def get_distinct_regions(self) -> List[str]:
        return self.get_stats().get("regions", [])

    def get_external_signals_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """Alias for get_customer_signals — matches CosmosDBService interface."""
        return self.get_customer_signals(customer_id)
