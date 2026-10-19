"""Unit tests for the Anti-Spam Governor and Cadence Controller."""
import pytest
from src.graph.governor import evaluate_governor, governor_node
from src.graph.state import create_initial_state, update_state


def test_user_initiated_message_always_allowed():
    decision = evaluate_governor(
        user_id="user_01",
        trigger_type="user_message",
        hours_since_last_ping=0.5,
        current_local_hour=2,  # 2 AM
        silence_streak=5,
        confidence=0.5,
    )
    assert decision.allowed is True
    assert "iniciado por el usuario" in decision.reason.lower()


def test_proactive_rejected_in_quiet_hours_night():
    decision = evaluate_governor(
        user_id="user_01",
        trigger_type="market_spark",
        hours_since_last_ping=30.0,
        current_local_hour=23,  # 11 PM
        silence_streak=0,
        confidence=0.92,
    )
    assert decision.allowed is False
    assert "fuera de ventana" in decision.reason.lower()


def test_proactive_rejected_under_cooldown():
    decision = evaluate_governor(
        user_id="user_01",
        trigger_type="market_spark",
        hours_since_last_ping=12.0,  # Only 12 hours since last ping
        current_local_hour=14,  # 2 PM (daytime)
        silence_streak=0,
        confidence=0.92,
    )
    assert decision.allowed is False
    assert "cooldown activo" in decision.reason.lower()


def test_proactive_rejected_low_confidence():
    decision = evaluate_governor(
        user_id="user_01",
        trigger_type="market_spark",
        hours_since_last_ping=25.0,
        current_local_hour=11,  # 11 AM
        silence_streak=0,
        confidence=0.75,  # Below 0.85 threshold
    )
    assert decision.allowed is False
    assert "confianza insuficiente" in decision.reason.lower()


def test_proactive_backoff_on_silence_streak():
    # User ignored previous ping (silence_streak = 1), backoff requires 48h
    decision = evaluate_governor(
        user_id="user_01",
        trigger_type="trench_inquiry",
        hours_since_last_ping=30.0,  # 30h is > 24h, but < 48h
        current_local_hour=15,
        silence_streak=1,
        confidence=0.90,
    )
    assert decision.allowed is False
    assert decision.backoff_cooldown_hours == 48.0
    assert "backoff" in decision.reason.lower() or "cooldown" in decision.reason.lower()


def test_proactive_approved_when_all_criteria_met():
    decision = evaluate_governor(
        user_id="user_01",
        trigger_type="brand_health_audit",
        hours_since_last_ping=48.5,
        current_local_hour=10,  # 10 AM
        silence_streak=0,
        confidence=0.95,
    )
    assert decision.allowed is True
    assert decision.hours_since_last_ping >= 24.0


def test_governor_node_in_graph_state():
    state = create_initial_state(user_id="user_01")
    state = update_state(
        state,
        trigger_type="market_spark",
        proactive_context={
            "hours_since_last_ping": 28.0,
            "current_local_hour": 14,
            "silence_streak": 0,
            "confidence": 0.91,
        },
    )

    new_state = governor_node(state)
    decision = new_state.get("governor_decision")
    assert decision is not None
    assert decision.allowed is True


def test_trench_inquiry_rejected_under_42_hours():
    # Attempt trench inquiry at 18:00 (inside window) but with only 36h silence (< 42h)
    decision = evaluate_governor(
        user_id="user_01",
        trigger_type="trench_inquiry",
        hours_since_last_ping=36.0,
        current_local_hour=18,
        silence_streak=0,
        confidence=0.90,
    )
    assert decision.allowed is False
    assert decision.backoff_cooldown_hours == 42.0
    assert "cooldown activo" in decision.reason.lower() or "42" in decision.reason


def test_trench_inquiry_rejected_outside_evening_window():
    # Case A: silence >= 42h (50h), but hour is 14:00 (before 17:00)
    decision_early = evaluate_governor(
        user_id="user_01",
        trigger_type="trench_inquiry",
        hours_since_last_ping=50.0,
        current_local_hour=14,
        silence_streak=0,
        confidence=0.90,
    )
    assert decision_early.allowed is False
    assert "17:00 a 19:30" in decision_early.reason

    # Case B: silence >= 42h (50h), but hour is 19:45 (after 19:30)
    decision_late = evaluate_governor(
        user_id="user_01",
        trigger_type="trench_inquiry",
        hours_since_last_ping=50.0,
        current_local_hour=19,
        silence_streak=0,
        confidence=0.90,
        current_local_minute=45,
    )
    assert decision_late.allowed is False
    assert "17:00 a 19:30" in decision_late.reason


def test_trench_inquiry_approved_within_evening_window_and_42h():
    # Approved: silence >= 42h (45.0h), hour is 18:15 (within 17:00-19:30)
    decision = evaluate_governor(
        user_id="user_01",
        trigger_type="trench_inquiry",
        hours_since_last_ping=45.0,
        current_local_hour=18,
        silence_streak=0,
        confidence=0.90,
        current_local_minute=15,
    )
    assert decision.allowed is True
    assert decision.backoff_cooldown_hours == 42.0

