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


def test_hero_image_is_served() -> None:
    response = client.get("/static/images/hero-parent-child-activities.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 1_000


def test_recommendation_contract() -> None:
    response = client.post("/api/v1/recommendations", json=valid_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["ranking_mode"] == "deterministic"
    assert body["degraded"] is True
    assert len(body["recommendations"]) == 6
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


def test_chat_uses_materials_with_current_filters() -> None:
    context = valid_payload()
    response = client.post(
        "/api/v1/chat",
        json={"message": "What can we do with plastic cups?", "context": context},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_mode"] == "catalogue"
    assert "Cup Tower Lab" in body["suggested_activities"]


def test_chat_uses_age_mentioned_in_the_message() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "What can I do with my 4 year old boy?", "context": valid_payload()},
    )

    assert response.status_code == 200
    assert "4-year-old" in response.json()["reply"]


def test_chat_explains_training_schedule() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "Does model training happen regularly?", "context": valid_payload()},
    )

    assert response.status_code == 200
    assert "not retrained continuously" in response.json()["reply"]


def test_model_info_does_not_claim_an_unloaded_model() -> None:
    response = client.get("/api/v1/model-info")

    assert response.status_code == 200
    assert response.json()["ranking_mode"] == "deterministic"
    assert response.json()["trained_model_loaded"] is False
