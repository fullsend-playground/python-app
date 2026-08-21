import pytest
from app import app, reset_items


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        reset_items()
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


def test_patch_unknown_fields_rejected(client):
    client.post("/items", json={"name": "widget"})
    resp = client.patch("/items/1", json={"warehouse_bin": "A-12"})
    assert resp.status_code == 400
    assert "warehouse_bin" in resp.get_json()["error"]


def test_patch_mixed_known_and_unknown_fields_rejected(client):
    client.post("/items", json={"name": "widget"})
    resp = client.patch("/items/1", json={"done": True, "warehouse_bin": "A-12"})
    assert resp.status_code == 400
    assert "warehouse_bin" in resp.get_json()["error"]


def test_patch_valid_fields_accepted(client):
    client.post("/items", json={"name": "widget"})
    resp = client.patch("/items/1", json={"name": "gadget", "done": True})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "gadget"
    assert data["done"] is True


def test_create_item_unknown_fields_rejected(client):
    resp = client.post("/items", json={"name": "widget", "warehouse_bin": "A-12"})
    assert resp.status_code == 400
    assert "warehouse_bin" in resp.get_json()["error"]


def test_create_item_valid_fields_accepted(client):
    resp = client.post("/items", json={"name": "widget"})
    assert resp.status_code == 201
    assert resp.get_json()["name"] == "widget"
