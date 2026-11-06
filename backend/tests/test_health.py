from fastapi.testclient import TestClient

from job_agent.main import app


def test_health_endpoint_reports_liveness() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
