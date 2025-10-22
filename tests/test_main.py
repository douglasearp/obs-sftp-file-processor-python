"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from src.obs_sftp_file_processor.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_health_endpoint(client):
    """Test detailed health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_openapi_docs(client):
    """Test OpenAPI documentation endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json(client):
    """Test OpenAPI JSON endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "OBS SFTP File Processor"
