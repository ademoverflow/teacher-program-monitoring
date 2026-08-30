from core.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health() -> None:
    """Test health endpoint (mounted under /api)."""
    response = client.get("/api/health")
    status_code = 200
    assert response.status_code == status_code
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime" in data
    assert data["uptime"] > 0
    assert "version" in data


def test_health_not_served_without_api_prefix() -> None:
    """The API only lives under /api (what the Vite proxy forwards)."""
    response = client.get("/health")
    not_found = 404
    assert response.status_code == not_found
