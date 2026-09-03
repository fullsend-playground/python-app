import threading
import time

from flask import g, request
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

registry = CollectorRegistry()

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP request count",
    ["method", "endpoint", "status"],
    registry=registry,
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

REQUEST_DURATION_MAX = Gauge(
    "http_request_duration_max_seconds",
    "Maximum HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

REQUEST_DURATION_MIN = Gauge(
    "http_request_duration_min_seconds",
    "Minimum HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

# Thread-safe tracking of observed min/max values per (method, endpoint).
_extremes_lock = threading.Lock()
_extremes: dict[tuple[str, str], tuple[float, float]] = {}


def init_metrics(app):
    """Register Prometheus metrics hooks and /metrics endpoint on the app."""

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
        rule = request.url_rule
        endpoint = rule.rule if rule is not None else "unmatched"
        method = request.method
        status = str(response.status_code)

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

        key = (method, endpoint)
        with _extremes_lock:
            cur = _extremes.get(key)
            if cur is None:
                _extremes[key] = (duration, duration)
                REQUEST_DURATION_MAX.labels(method=method, endpoint=endpoint).set(
                    duration
                )
                REQUEST_DURATION_MIN.labels(method=method, endpoint=endpoint).set(
                    duration
                )
            else:
                cur_min, cur_max = cur
                new_min = min(cur_min, duration)
                new_max = max(cur_max, duration)
                _extremes[key] = (new_min, new_max)
                if new_max != cur_max:
                    REQUEST_DURATION_MAX.labels(method=method, endpoint=endpoint).set(
                        new_max
                    )
                if new_min != cur_min:
                    REQUEST_DURATION_MIN.labels(method=method, endpoint=endpoint).set(
                        new_min
                    )

        return response

    @app.route("/metrics")
    def metrics():
        return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}
