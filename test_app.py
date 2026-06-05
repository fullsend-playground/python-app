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


def test_no_id_collision_after_delete(client):
    """IDs must never be reused after deletion."""
    resp1 = client.post("/items", json={"name": "A"})
    resp2 = client.post("/items", json={"name": "B"})
    id_a = resp1.get_json()["id"]
    id_b = resp2.get_json()["id"]

    # Delete first item
    client.delete(f"/items/{id_a}")

    # Create a new item — should NOT collide with B's id
    resp3 = client.post("/items", json={"name": "C"})
    id_c = resp3.get_json()["id"]
    assert id_c != id_b, "New item ID collides with existing item"

    # Verify both remaining items exist in the list
    all_items = client.get("/items").get_json()["items"]
    all_ids = [item["id"] for item in all_items]
    assert id_b in all_ids
    assert id_c in all_ids
    assert len(all_items) == 2


def test_no_id_reuse_after_multiple_deletes(client):
    """IDs stay unique after several deletions followed by several creates."""
    # Create three items
    ids = []
    for name in ("X", "Y", "Z"):
        resp = client.post("/items", json={"name": name})
        ids.append(resp.get_json()["id"])

    # Delete all three
    for item_id in ids:
        client.delete(f"/items/{item_id}")

    # Create two more items — their IDs must not collide with any prior ID
    new_ids = []
    for name in ("P", "Q"):
        resp = client.post("/items", json={"name": name})
        new_ids.append(resp.get_json()["id"])

    all_assigned = ids + new_ids
    assert len(all_assigned) == len(set(all_assigned)), "ID reuse detected"
