import re

import pytest
from app import app, reset_items
from metrics import (
    REQUEST_COUNT,
    REQUEST_DURATION,
    REQUEST_DURATION_MAX,
    REQUEST_DURATION_MIN,
    _extremes,
)

_ALL_METRICS = [
    REQUEST_COUNT,
    REQUEST_DURATION,
    REQUEST_DURATION_MAX,
    REQUEST_DURATION_MIN,
]


def _reset_collectors():
    """Clear all prometheus metric values between tests."""
    for metric in _ALL_METRICS:
        metric._metrics.clear()
    _extremes.clear()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        reset_items()
        _reset_collectors()
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_list_items_empty(client):
    resp = client.get("/items")
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_create_item(client):
    resp = client.post("/items", json={"name": "Write tests"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Write tests"
    assert data["done"] is False
    assert data["id"] == 1


def test_create_item_missing_name(client):
    resp = client.post("/items", json={})
    assert resp.status_code == 400


def test_update_item(client):
    client.post("/items", json={"name": "Task 1"})
    resp = client.patch("/items/1", json={"done": True})
    assert resp.status_code == 200
    assert resp.get_json()["done"] is True


def test_update_item_not_found(client):
    resp = client.patch("/items/999", json={"done": True})
    assert resp.status_code == 404


def test_delete_item(client):
    client.post("/items", json={"name": "To delete"})
    resp = client.delete("/items/1")
    assert resp.status_code == 204

    resp = client.get("/items")
    assert resp.get_json()["items"] == []


def test_delete_item_not_found(client):
    resp = client.delete("/items/999")
    assert resp.status_code == 404


def test_metrics_endpoint_returns_200(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/plain")


def test_metrics_contains_help_and_type(client):
    resp = client.get("/metrics")
    body = resp.data.decode()
    assert "# HELP" in body
    assert "# TYPE" in body


def test_metrics_tracks_request_count(client):
    client.get("/items")
    resp = client.get("/metrics")
    body = resp.data.decode()
    assert "http_requests_total{" in body
    assert 'endpoint="/items"' in body
    assert 'method="GET"' in body
    assert 'status="200"' in body


def test_metrics_tracks_request_duration(client):
    client.get("/items")
    resp = client.get("/metrics")
    body = resp.data.decode()
    assert "http_request_duration_seconds" in body
    assert 'endpoint="/items"' in body


def test_metrics_tracks_status_codes(client):
    client.post("/items", json={})
    resp = client.get("/metrics")
    body = resp.data.decode()
    assert 'status="400"' in body


def test_metrics_excludes_metrics_endpoint(client):
    # Hit /metrics a few times
    client.get("/metrics")
    client.get("/metrics")
    resp = client.get("/metrics")
    body = resp.data.decode()
    assert 'endpoint="/metrics"' not in body


def test_metrics_tracks_min_max_duration(client):
    client.get("/items")
    resp = client.get("/metrics")
    body = resp.data.decode()
    assert "http_request_duration_max_seconds" in body
    assert "http_request_duration_min_seconds" in body

    # Verify values are positive floats and min <= max
    max_match = re.search(
        r'http_request_duration_max_seconds\{.*endpoint="/items".*\}\s+([\d.e+-]+)',
        body,
    )
    min_match = re.search(
        r'http_request_duration_min_seconds\{.*endpoint="/items".*\}\s+([\d.e+-]+)',
        body,
    )
    assert max_match is not None, "max duration metric not found for /items"
    assert min_match is not None, "min duration metric not found for /items"
    max_val = float(max_match.group(1))
    min_val = float(min_match.group(1))
    assert max_val > 0, "max duration should be positive"
    assert min_val > 0, "min duration should be positive"
    assert min_val <= max_val, "min duration should be <= max duration"
