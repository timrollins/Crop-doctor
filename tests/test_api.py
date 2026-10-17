from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_diagnose_without_provider_is_safe() -> None:
    response = client.post("/api/diagnose", json={"question": "Leaves are curling"})
    assert response.status_code == 200
    assert "not configured" in response.json()["answer"]


def test_frontend_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Crop Doctor" in response.text
