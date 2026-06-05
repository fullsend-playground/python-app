from flask import Flask, g, jsonify, request
from datetime import datetime, timezone
import time

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP request count",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

REQUEST_DURATION_MAX = Gauge(
    "http_request_duration_max_seconds",
    "Maximum HTTP request duration in seconds",
    ["method", "endpoint"],
)

REQUEST_DURATION_MIN = Gauge(
    "http_request_duration_min_seconds",
    "Minimum HTTP request duration in seconds",
    ["method", "endpoint"],
)


@app.before_request
def _start_timer():
    if request.path == "/metrics":
        return
    g.start_time = time.monotonic()


@app.after_request
def _record_metrics(response):
    if request.path == "/metrics":
        return response

    start = g.pop("start_time", None)
    if start is None:
        return response

    duration = time.monotonic() - start
    endpoint = request.path
    method = request.method
    status = str(response.status_code)

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    max_gauge = REQUEST_DURATION_MAX.labels(method=method, endpoint=endpoint)
    min_gauge = REQUEST_DURATION_MIN.labels(method=method, endpoint=endpoint)

    current_max = max_gauge._value.get()
    if current_max == 0.0 or duration > current_max:
        max_gauge.set(duration)

    current_min = min_gauge._value.get()
    if current_min == 0.0 or duration < current_min:
        min_gauge.set(duration)

    return response


VERSION = "0.1.0"


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


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
        "id": len(_get_items()) + 1,
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


def _get_items():
    return _items_store


def reset_items():
    """Reset the in-memory store (used by tests)."""
    _items_store.clear()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
