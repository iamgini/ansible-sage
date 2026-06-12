"""
Integration tests for Docker Compose setup.

These tests verify the Docker Compose stack works correctly.
Run with: pytest tests/integration/test_docker_compose.py -v -m integration

Note: Requires docker-compose to be running.
"""

import os

import httpx
import pytest


def is_docker_compose_running():
    """Check if docker-compose services are accessible."""
    try:
        response = httpx.get("http://localhost:8000/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.skipif(
    not is_docker_compose_running(),
    reason="Docker Compose not running - start with 'docker-compose up'",
)
def test_docker_compose_api_accessible():
    """Test that API is accessible via Docker Compose."""
    response = httpx.get("http://localhost:8000/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.integration
@pytest.mark.skipif(
    not is_docker_compose_running(),
    reason="Docker Compose not running",
)
def test_docker_compose_api_docs():
    """Test that API docs are accessible in Docker."""
    response = httpx.get("http://localhost:8000/docs")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipping Docker Compose tests in CI",
)
def test_docker_compose_postgres_connection():
    """Test that PostgreSQL is accessible (if configured)."""
    # This would require testing the database connection
    # Add when database integration is fully implemented
    pytest.skip("Database integration tests not yet implemented")


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipping Docker Compose tests in CI",
)
def test_docker_compose_redis_connection():
    """Test that Redis is accessible (if configured)."""
    # This would require testing the Redis connection
    # Add when Redis integration is fully implemented
    pytest.skip("Redis integration tests not yet implemented")
