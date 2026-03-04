"""Tests for workflow endpoints and workflow auth behavior."""

import os
import sys

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import api


class TestWorkflowRoutes:
    def test_workflow_routes_exist(self):
        routes = [route.path for route in api.app.routes]
        assert "/api/workflows/platform-health" in routes
        assert "/api/workflows/customer-packet/{customer_id}" in routes


class TestWorkflowAuthValidation:
    def test_validate_workflow_key_enforces_401_when_configured(self, monkeypatch):
        monkeypatch.setenv("WORKFLOW_SHARED_KEY", "abc123")
        monkeypatch.delenv("WORKFLOW_AUTH_DISABLED", raising=False)

        with pytest.raises(HTTPException) as no_key:
            api._validate_workflow_key(None)
        assert no_key.value.status_code == 401

        with pytest.raises(HTTPException) as wrong_key:
            api._validate_workflow_key("wrong")
        assert wrong_key.value.status_code == 401

        api._validate_workflow_key("abc123")

    def test_validate_workflow_key_default_deny_without_config(self, monkeypatch):
        monkeypatch.delenv("WORKFLOW_SHARED_KEY", raising=False)
        monkeypatch.delenv("WORKFLOW_AUTH_DISABLED", raising=False)

        with pytest.raises(HTTPException) as missing_config:
            api._validate_workflow_key(None)
        assert missing_config.value.status_code == 503

    def test_validate_workflow_key_allows_explicit_disable(self, monkeypatch):
        monkeypatch.delenv("WORKFLOW_SHARED_KEY", raising=False)
        monkeypatch.setenv("WORKFLOW_AUTH_DISABLED", "true")
        api._validate_workflow_key(None)


class TestWorkflowEndpoints:
    def test_platform_health_auth_enforced(self, monkeypatch):
        monkeypatch.setenv("WORKFLOW_SHARED_KEY", "abc123")
        monkeypatch.delenv("WORKFLOW_AUTH_DISABLED", raising=False)
        monkeypatch.setattr(
            api,
            "_get_logic_apps_platform_health",
            lambda: {"status": "healthy", "components": {"api": {"ready": True}}},
        )

        client = TestClient(api.app)

        unauthorized = client.get("/api/workflows/platform-health")
        assert unauthorized.status_code == 401

        authorized = client.get("/api/workflows/platform-health", headers={"x-workflow-key": "abc123"})
        assert authorized.status_code == 200
        assert authorized.json().get("status") == "healthy"

    def test_customer_packet_auth_enforced(self, monkeypatch):
        monkeypatch.setenv("WORKFLOW_SHARED_KEY", "abc123")
        monkeypatch.delenv("WORKFLOW_AUTH_DISABLED", raising=False)
        monkeypatch.setattr(
            api,
            "_build_logic_apps_customer_packet",
            lambda customer_id: {"customer_id": customer_id, "status": "success", "data": {}, "errors": []},
        )

        client = TestClient(api.app)

        unauthorized = client.get("/api/workflows/customer-packet/C0001")
        assert unauthorized.status_code == 401

        authorized = client.get(
            "/api/workflows/customer-packet/C0001",
            headers={"x-workflow-key": "abc123"},
        )
        assert authorized.status_code == 200
        assert authorized.json().get("customer_id") == "C0001"
