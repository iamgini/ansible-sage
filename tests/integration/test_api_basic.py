"""
Basic integration tests for Ansible Maya API.

These tests verify the API server starts and responds correctly.
Run with: pytest tests/integration/test_api_basic.py -v -m integration
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from ansible_maya.api.server import app

    return TestClient(app)


@pytest.mark.integration
def test_health_check(client):
    """Test that health check endpoint works."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "ok"]


@pytest.mark.integration
def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data or "message" in data


@pytest.mark.integration
def test_api_docs_available(client):
    """Test that OpenAPI docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


@pytest.mark.integration
def test_openapi_spec(client):
    """Test that OpenAPI spec is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert "openapi" in spec
    assert "info" in spec
    assert spec["info"]["title"] == "Ansible Maya API"


@pytest.mark.integration
def test_invalid_endpoint_404(client):
    """Test that invalid endpoints return 404."""
    response = client.get("/this-does-not-exist")
    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.skip(reason="Requires LLM API key - enable when needed")
def test_event_generation_endpoint_structure(client):
    """Test event generation endpoint accepts correct structure (mocked)."""
    # This would require mocking the LLM provider
    # Add when you want to test with real API keys
    payload = {
        "event_id": "test-001",
        "event_type": "disk_full",
        "description": "Test disk full event",
        "host": "test-server-01",
        "severity": "high",
        "metadata": {"partition": "/var", "usage_percent": 95},
    }

    # This will fail without proper setup, but tests the structure
    response = client.post("/api/v1/events/generate", json=payload)

    # We expect either success or 500 (if LLM not configured)
    # The key is it doesn't return 422 (validation error)
    assert response.status_code in [200, 500, 503]
