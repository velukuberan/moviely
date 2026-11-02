from fastapi.testclient import TestClient

from moviely.main import app


def test_health_returns_success() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "moviely",
    }


def test_health_returns_json_content_type() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.headers["content-type"] == "application/json"
