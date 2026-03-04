"""
Azure Functions Data Layer — Insurance Data API

HTTP-triggered functions that expose Cosmos DB data through a clean REST API.
All functions use the shared CosmosDBRepository singleton.
"""
import json
import logging
import azure.functions as func

from shared.data_repository import get_repository

logger = logging.getLogger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


# ── Health & Info ────────────────────────────────────────────────────

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check — verifies Cosmos DB connectivity."""
    import os
    repo = get_repository()
    connected = repo.is_connected()
    status = "healthy" if connected else "degraded"
    diag = {
        "status": status,
        "database": repo.database_name,
        "endpoint_set": bool(repo.endpoint),
        "client_exists": repo.client is not None,
        "containers_count": len(repo._containers),
        "connect_error": getattr(repo, '_connect_error', None),
        "env_check": {
            "COSMOS_DB_ENDPOINT": bool(os.getenv("COSMOS_DB_ENDPOINT")),
            "COSMOS_DB_DATABASE": bool(os.getenv("COSMOS_DB_DATABASE")),
            "AZURE_TENANT_ID": bool(os.getenv("AZURE_TENANT_ID")),
            "AZURE_CLIENT_ID": bool(os.getenv("AZURE_CLIENT_ID")),
            "AZURE_CLIENT_SECRET": bool(os.getenv("AZURE_CLIENT_SECRET")),
        },
    }
    # If connected, try a quick query to verify actual data access
    if connected:
        try:
            count = repo.query_container("customers", "SELECT VALUE COUNT(1) FROM c", max_items=1)
            diag["test_query"] = {"customer_count": count[0] if count else "empty"}
        except Exception as e:
            diag["test_query"] = {"error": str(e)}
    return func.HttpResponse(
        json.dumps(diag, default=str),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="info", methods=["GET"])
def info(req: func.HttpRequest) -> func.HttpResponse:
    """API information and available endpoints."""
    return func.HttpResponse(
        json.dumps({
            "name": "Insurance Data Layer API",
            "version": "1.0.0",
            "endpoints": {
                "health": "GET /api/health",
                "info": "GET /api/info",
                "stats": "GET /api/stats",
                "customer_search": "GET /api/search/customers?q={query}&limit={limit}",
                "customer_profile": "GET /api/customers/{customer_id}",
                "customer_full_profile": "GET /api/customers/{customer_id}/full",
                "customer_policies": "GET /api/customers/{customer_id}/policies",
                "customer_claims": "GET /api/customers/{customer_id}/claims",
                "customer_features": "GET /api/customers/{customer_id}/features",
                "customer_signals": "GET /api/customers/{customer_id}/signals",
                "customer_activity": "GET /api/customers/{customer_id}/activity",
                "producer": "GET /api/producers/{producer_id}",
            },
        }),
        mimetype="application/json",
    )


# ── Statistics ───────────────────────────────────────────────────────

@app.route(route="stats", methods=["GET"])
def stats(req: func.HttpRequest) -> func.HttpResponse:
    """Get dashboard statistics (counts, premiums, distinct states/regions)."""
    repo = get_repository()
    if not repo.is_connected():
        return _error(503, "Data layer not connected to database")

    try:
        data = repo.get_stats()
        return _ok(data)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return _error(500, str(e))


# ── Customer Search ──────────────────────────────────────────────────

@app.route(route="search/customers", methods=["GET"])
def customer_search(req: func.HttpRequest) -> func.HttpResponse:
    """Search customers by ID, state, region, ZIP, or free text."""
    repo = get_repository()
    if not repo.is_connected():
        return _error(503, "Data layer not connected to database")

    q = req.params.get("q")
    if not q:
        return _error(400, "Missing required parameter: q")

    limit = int(req.params.get("limit", "50"))
    limit = min(max(limit, 1), 200)

    try:
        results = repo.search_customers(q, limit=limit)
        return _ok({"results": results, "count": len(results), "query": q})
    except Exception as e:
        logger.error(f"Search error: {e}")
        return _error(500, str(e))


# ── Customer Profile ─────────────────────────────────────────────────

@app.route(route="customers/{customer_id}", methods=["GET"])
def customer_get(req: func.HttpRequest) -> func.HttpResponse:
    """Get a single customer by ID."""
    repo = get_repository()
    if not repo.is_connected():
        return _error(503, "Data layer not connected to database")

    customer_id = req.route_params.get("customer_id")
    try:
        customer = repo.get_customer(customer_id)
        if not customer:
            return _error(404, f"Customer {customer_id} not found")
        return _ok(customer)
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        return _error(500, str(e))


@app.route(route="customers/{customer_id}/full", methods=["GET"])
def customer_full_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Get full customer profile (customer + policies + claims + features + signals + activity)."""
    repo = get_repository()
    if not repo.is_connected():
        return _error(503, "Data layer not connected to database")

    customer_id = req.route_params.get("customer_id")
    try:
        profile = repo.get_full_customer_profile(customer_id)
        if "error" in profile:
            return _error(404, profile["error"])
        return _ok(profile)
    except Exception as e:
        logger.error(f"Error getting full profile for {customer_id}: {e}")
        return _error(500, str(e))


# ── Customer Sub-resources ───────────────────────────────────────────

@app.route(route="customers/{customer_id}/policies", methods=["GET"])
def customer_policies(req: func.HttpRequest) -> func.HttpResponse:
    """Get all policies for a customer."""
    return _customer_sub_resource(req, "policies")


@app.route(route="customers/{customer_id}/claims", methods=["GET"])
def customer_claims(req: func.HttpRequest) -> func.HttpResponse:
    """Get all claims for a customer."""
    return _customer_sub_resource(req, "claims")


@app.route(route="customers/{customer_id}/features", methods=["GET"])
def customer_features(req: func.HttpRequest) -> func.HttpResponse:
    """Get ML features for a customer."""
    repo = get_repository()
    if not repo.is_connected():
        return _error(503, "Data layer not connected to database")

    customer_id = req.route_params.get("customer_id")
    try:
        features = repo.get_customer_features(customer_id)
        if not features:
            return _error(404, f"No features found for {customer_id}")
        return _ok(features)
    except Exception as e:
        logger.error(f"Error getting features for {customer_id}: {e}")
        return _error(500, str(e))


@app.route(route="customers/{customer_id}/signals", methods=["GET"])
def customer_signals(req: func.HttpRequest) -> func.HttpResponse:
    """Get external signals for a customer."""
    return _customer_sub_resource(req, "signals")


@app.route(route="customers/{customer_id}/activity", methods=["GET"])
def customer_activity(req: func.HttpRequest) -> func.HttpResponse:
    """Get producer activity for a customer."""
    return _customer_sub_resource(req, "activity")


# ── Producers ────────────────────────────────────────────────────────

@app.route(route="producers/{producer_id}", methods=["GET"])
def producer_get(req: func.HttpRequest) -> func.HttpResponse:
    """Get a producer by ID."""
    repo = get_repository()
    if not repo.is_connected():
        return _error(503, "Data layer not connected to database")

    producer_id = req.route_params.get("producer_id")
    try:
        producer = repo.get_producer(producer_id)
        if not producer:
            return _error(404, f"Producer {producer_id} not found")
        return _ok(producer)
    except Exception as e:
        logger.error(f"Error getting producer {producer_id}: {e}")
        return _error(500, str(e))


# ── Helpers ──────────────────────────────────────────────────────────

def _customer_sub_resource(req: func.HttpRequest, resource_type: str) -> func.HttpResponse:
    """Generic handler for customer sub-resources (policies, claims, signals, activity)."""
    repo = get_repository()
    if not repo.is_connected():
        return _error(503, "Data layer not connected to database")

    customer_id = req.route_params.get("customer_id")
    method_map = {
        "policies": repo.get_customer_policies,
        "claims": repo.get_customer_claims,
        "signals": repo.get_customer_signals,
        "activity": repo.get_producer_activity,
    }

    try:
        results = method_map[resource_type](customer_id)
        return _ok({"customer_id": customer_id, resource_type: results, "count": len(results)})
    except Exception as e:
        logger.error(f"Error getting {resource_type} for {customer_id}: {e}")
        return _error(500, str(e))


def _ok(data) -> func.HttpResponse:
    """Return a 200 JSON response."""
    return func.HttpResponse(
        json.dumps(data, default=str),
        status_code=200,
        mimetype="application/json",
    )


def _error(status_code: int, message: str) -> func.HttpResponse:
    """Return an error JSON response."""
    return func.HttpResponse(
        json.dumps({"error": message}),
        status_code=status_code,
        mimetype="application/json",
    )
