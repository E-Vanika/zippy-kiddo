from fastapi.testclient import TestClient

from zippy_kiddo.main import app


client = TestClient(app)


def valid_payload() -> dict[str, object]:
    return {
        "age": 6,
        "duration_minutes": 30,
        "setting": "indoor",
        "supervision": "nearby",
        "energy": "moderate",
        "materials": [],
    }


def test_health_and_degraded_readiness() -> None:
    assert client.get("/healthz").json() == {"status": "ok"}

    readiness = client.get("/readyz")
    assert readiness.status_code == 200
    assert readiness.json()["fallback_ready"] is True
    assert readiness.json()["activity_count"] >= 30


def test_recommendation_contract() -> None:
    response = client.post("/api/v1/recommendations", json=valid_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["ranking_mode"] == "deterministic"
    assert body["degraded"] is True
    assert len(body["recommendations"]) == 3
    assert response.headers["X-Request-ID"]


def test_rejects_out_of_range_age_and_unknown_fields() -> None:
    payload = valid_payload()
    payload["age"] = 2
    payload["child_name"] = "must not be collected"

    response = client.post("/api/v1/recommendations", json=payload)

    assert response.status_code == 422


def test_metrics_are_exposed_for_internal_monitoring() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "zippy_http_requests_total" in response.text
