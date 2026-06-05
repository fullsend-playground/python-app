from flask import Flask, jsonify, request
from datetime import datetime, timezone

app = Flask(__name__)

VERSION = "0.1.0"


@app.route("/health")
def health():
    return jsonify(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=VERSION,
    )


@app.route("/items", methods=["GET"])
def list_items():
    return jsonify(items=_get_items())


@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify(error="name is required"), 400

    item = {
        "id": _new_id(),
        "name": data["name"],
        "done": False,
    }
    _get_items().append(item)
    return jsonify(item), 201


@app.route("/items/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    items = _get_items()
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        return jsonify(error="item not found"), 404

    data = request.get_json()
    if "done" in data:
        item["done"] = data["done"]
    if "name" in data:
        item["name"] = data["name"]

    return jsonify(item)


@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    items = _get_items()
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        return jsonify(error="item not found"), 404

    items.remove(item)
    return "", 204


_items_store = []
_next_id = 1


def _new_id():
    global _next_id
    current = _next_id
    _next_id += 1
    return current


def _get_items():
    return _items_store


def reset_items():
    """Reset the in-memory store (used by tests)."""
    global _next_id
    _items_store.clear()
    _next_id = 1


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
