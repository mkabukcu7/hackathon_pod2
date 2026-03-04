"""Shared workflow payload builders used by API and MCP entrypoints."""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from uuid import uuid4


def build_logic_apps_customer_packet(
    customer_id: str,
    customer_agent: Any,
    retention_agent: Any,
    sales_agent: Any,
    hazard_agent: Any,
) -> Dict[str, Any]:
    """Build deterministic customer packet for Logic Apps workflows."""
    request_id = str(uuid4())
    packet: Dict[str, Any] = {
        "request_id": request_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "customer_id": customer_id,
        "status": "success",
        "data": {},
        "errors": [],
    }

    profile = customer_agent.get_customer_profile(customer_id)
    if "error" in profile:
        packet["status"] = "failed"
        packet["errors"].append({"component": "customer_profile", "message": profile.get("error")})
        return packet

    packet["data"]["profile"] = profile

    try:
        packet["data"]["customer_insights"] = retention_agent.get_customer_insights(customer_id, profile)
    except Exception as e:
        packet["errors"].append({"component": "customer_insights", "message": str(e)})

    try:
        packet["data"]["retention_score"] = retention_agent.get_retention_score(customer_id, profile)
    except Exception as e:
        packet["errors"].append({"component": "retention_score", "message": str(e)})

    try:
        packet["data"]["cross_sell"] = sales_agent.get_cross_sell_recommendations(customer_id, profile)
    except Exception as e:
        packet["errors"].append({"component": "cross_sell", "message": str(e)})

    zip_code = profile.get("zip")
    if isinstance(zip_code, str) and len(zip_code) == 5:
        try:
            packet["data"]["flood_risk"] = hazard_agent.get_flood_risk(zip_code)
        except Exception as e:
            packet["errors"].append({"component": "flood_risk", "message": str(e)})

    if packet["errors"]:
        packet["status"] = "partial_success"

    packet["meta"] = {
        "errors_count": len(packet["errors"]),
        "components_returned": sorted(list(packet["data"].keys())),
    }
    return packet


def build_logic_apps_platform_health(
    component_name: str,
    component_payload: Dict[str, Any],
    agents_payload: Dict[str, Any],
    data_layer_client_factory: Callable[[], Any],
    extra_components: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build shared workflow-facing health/readiness payload."""
    data_layer_connected = False
    data_layer_error = None
    client = None

    try:
        client = data_layer_client_factory()
        data_layer_connected = bool(client.is_connected())
    except Exception as e:
        data_layer_error = str(e)
    finally:
        if client is not None and hasattr(client, "close"):
            try:
                client.close()
            except Exception:
                pass

    components: Dict[str, Any] = {
        component_name: component_payload,
        "data_layer": {
            "ready": data_layer_connected,
            "error": data_layer_error,
        },
        "agents": agents_payload,
    }
    if extra_components:
        for key, value in extra_components.items():
            if key in components and isinstance(components[key], dict) and isinstance(value, dict):
                components[key].update(value)
            else:
                components[key] = value

    return {
        "status": "healthy" if data_layer_connected else "degraded",
        "components": components,
    }
