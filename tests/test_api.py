import pytest
from fastapi.testclient import TestClient

from map_app.failure import RandomFailurePolicy
from map_app.main import create_app
from map_app.repository import MarkerRepository


def make_client(failure_rate: float = 0) -> TestClient:
    return TestClient(create_app(MarkerRepository(), RandomFailurePolicy(failure_rate, lambda: 1)))


def marker_payload(score: int = 3) -> dict:
    return {"coordinates": {"lng": 30.52, "lat": 50.45}, "score": score}


def test_create_list_update_and_delete_marker() -> None:
    client = make_client()
    response = client.post("/api/markers", json=marker_payload())
    assert response.status_code == 201
    marker = response.json()
    assert marker["score"] == 3

    listed = client.get("/api/markers")
    assert listed.status_code == 200
    assert listed.json() == [marker]

    updated = client.patch(f"/api/markers/{marker['id']}", json={"score": 5, "coordinates": {"lng": 31, "lat": 51}})
    assert updated.status_code == 200
    assert updated.json()["score"] == 5
    assert updated.json()["coordinates"] == {"lng": 31, "lat": 51}

    assert client.delete(f"/api/markers/{marker['id']}").status_code == 204
    assert client.get("/api/markers").json() == []


def test_create_can_fail_without_persisting() -> None:
    client = TestClient(create_app(MarkerRepository(), RandomFailurePolicy(1, lambda: 0)))
    response = client.post("/api/markers", json=marker_payload())
    assert response.status_code == 503
    assert client.get("/api/markers").json() == []


def test_invalid_coordinates_and_score_are_rejected() -> None:
    client = make_client()
    assert client.post("/api/markers", json={"coordinates": {"lng": 181, "lat": 50}, "score": 0}).status_code == 422
    assert client.post("/api/markers", json={"coordinates": {"lng": 30, "lat": 50}, "score": 6}).status_code == 422


def test_empty_or_null_update_is_rejected_without_server_error() -> None:
    client = make_client()
    marker = client.post("/api/markers", json=marker_payload()).json()
    marker_id = marker["id"]

    assert client.patch(f"/api/markers/{marker_id}", json={}).status_code == 422
    assert client.patch(f"/api/markers/{marker_id}", json={"score": None}).status_code == 422
    assert client.get("/api/markers").json()[0] == marker


def test_missing_marker_returns_404() -> None:
    client = make_client()
    missing = "00000000-0000-0000-0000-000000000001"
    assert client.patch(f"/api/markers/{missing}", json={"score": 2}).status_code == 404
    assert client.delete(f"/api/markers/{missing}").status_code == 404


def test_frontend_is_served() -> None:
    response = make_client().get("/")
    assert response.status_code == 200
    assert "Pinboard" in response.text


def test_health_and_runtime_config_endpoints() -> None:
    client = make_client()
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/config").status_code == 200


def test_invalid_failure_rate_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKER_FAILURE_RATE", "not-a-number")
    with pytest.raises(RuntimeError, match="MARKER_FAILURE_RATE"):
        create_app(MarkerRepository())
