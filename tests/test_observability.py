import pytest
import time
import logging
from fastapi.testclient import TestClient

from main import app
from src.core.metrics import MetricsTracker, metrics_tracker
from src.core.observability import (
    generate_correlation_id,
    set_request_context,
    get_correlation_id,
    get_entry_point,
    get_user_id,
    log_event,
    trace_span,
)
from src.core.telemetry import TelemetryTracker, estimate_cost

@pytest.fixture
def client():
    return TestClient(app)

def test_correlation_id_generation():
    cid1 = generate_correlation_id("tg")
    cid2 = generate_correlation_id("tg")
    assert cid1.startswith("tg_")
    assert cid2.startswith("tg_")
    assert cid1 != cid2

def test_context_vars_propagation():
    set_request_context(correlation_id="corr_test_123", entry_point="whatsapp", user_id="user_test_999")
    assert get_correlation_id() == "corr_test_123"
    assert get_entry_point() == "whatsapp"
    assert get_user_id() == "user_test_999"

def test_log_event_redaction(caplog):
    logger = logging.getLogger("test.redaction")
    with caplog.at_level(logging.INFO):
        log_event(
            logger,
            logging.INFO,
            event="test_event",
            message="Mensaje de prueba",
            secret_token="super_secret_12345",
            api_key="sk-live-9999",
            safe_value="hola"
        )
    assert len(caplog.records) > 0
    rec = caplog.records[-1]
    extra = getattr(rec, "structured_extra", {})
    assert extra.get("secret_token") == "[REDACTED]"
    assert extra.get("api_key") == "[REDACTED]"
    assert extra.get("safe_value") == "hola"

def test_trace_span_success():
    logger = logging.getLogger("test.span")
    with trace_span("test_operation", logger=logger, foo="bar") as span:
        time.sleep(0.01)
    assert span["status"] == "success"
    assert span["duration_ms"] >= 10

def test_trace_span_failure():
    logger = logging.getLogger("test.span_fail")
    with pytest.raises(ValueError):
        with trace_span("failing_operation", logger=logger):
            raise ValueError("Something broke")

def test_metrics_tracker_calculations():
    tracker = MetricsTracker()
    tracker.record_request("telegram", duration_ms=100.0, is_error=False)
    tracker.record_request("telegram", duration_ms=200.0, is_error=False)
    tracker.record_request("whatsapp", duration_ms=300.0, is_error=True)
    tracker.record_tool_call("guardar_guion", duration_ms=50.0)

    summary = tracker.get_summary()
    assert summary["requests_total"] == 3
    assert summary["errors_total"] == 1
    assert summary["error_rate"] == round(1 / 3, 4)
    assert summary["latency_ms"]["avg"] == 200.0
    assert summary["latency_ms"]["min"] == 100.0
    assert summary["latency_ms"]["max"] == 300.0
    assert summary["by_channel"]["telegram"]["requests"] == 2
    assert summary["by_channel"]["whatsapp"]["errors"] == 1
    assert summary["by_tool"]["guardar_guion"]["calls"] == 1

def test_health_endpoint_includes_metrics(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "requests_total" in data["metrics"]
    assert "error_rate" in data["metrics"]
    assert "latency_ms" in data["metrics"]

def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "by_channel" in data

def test_middleware_injects_correlation_id(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-correlation-id" in response.headers
    assert len(response.headers["x-correlation-id"]) > 5

def test_telemetry_error_logging():
    telemetry = TelemetryTracker()
    cost = telemetry.log_turn(
        phase="routing",
        model_name="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=150,
        status="error",
        error_type="RateLimitError",
        error_message="Gemini quota exceeded"
    )
    assert cost > 0
