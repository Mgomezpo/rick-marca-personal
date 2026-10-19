"""Integration tests for the RickGraphEngine with proactive loops."""
import pytest
from src.graph.engine import RickGraphEngine
from src.graph.state import (
    create_initial_state,
    update_state,
    WinningPattern,
)


def test_graph_engine_runs_proactive_spark_flow():
    engine = RickGraphEngine()
    state = create_initial_state(user_id="user_spk", handle="miguel_brand")

    pattern = WinningPattern(
        pattern_id="wp_001",
        tipo_hook="revelacion_contraria",
        formato="Reel",
        emocion="intriga",
        rendimiento_relativo_promedio=2.5,
        piezas_respaldo=4,
        ejemplos=["Lo que nadie te dice sobre cómo funciona..."],
    )

    state = update_state(
        state,
        trigger_type="market_spark",
        proactive_context={
            "hours_since_last_ping": 36.0,
            "current_local_hour": 14,
            "silence_streak": 0,
            "confidence": 0.93,
            "winning_pattern": pattern,
            "source_referent": "@casidonovan",
            "thesis": "Menos agentes, más control determinístico",
        },
    )

    final_state = engine.run(state)
    assert final_state.get("governor_decision") is not None
    assert final_state["governor_decision"].allowed is True
    assert final_state.get("proactive_spark") is not None
    assert "@casidonovan" in final_state.get("final_response", "")
    assert "2.5x" in final_state.get("final_response", "")


def test_graph_engine_suppresses_spark_when_governor_rejects():
    engine = RickGraphEngine()
    state = create_initial_state(user_id="user_spk", handle="miguel_brand")

    state = update_state(
        state,
        trigger_type="market_spark",
        proactive_context={
            "hours_since_last_ping": 5.0,  # Under cooldown
            "current_local_hour": 14,
            "silence_streak": 0,
            "confidence": 0.93,
        },
    )

    final_state = engine.run(state)
    assert final_state.get("governor_decision") is not None
    assert final_state["governor_decision"].allowed is False
    assert final_state.get("proactive_spark") is None
    assert final_state.get("final_response") is None  # Suppressed


def test_graph_engine_runs_brand_health_audit_flow():
    engine = RickGraphEngine()
    state = create_initial_state(user_id="user_bh", handle="miguel_brand")

    state = update_state(
        state,
        trigger_type="brand_health_audit",
        proactive_context={
            "hours_since_last_ping": 48.0,
            "current_local_hour": 10,
            "silence_streak": 0,
            "confidence": 0.95,
            "recent_posts": [
                {"topic": "Reflexión", "pillar": "Historias"},
                {"topic": "Mi viaje", "pillar": "Historias"},
            ],
            "declared_pillars": [
                {"name": "Historias", "target_pct": 50.0},
                {"name": "Mecanismo Técnico", "target_pct": 50.0},
            ],
        },
    )

    final_state = engine.run(state)
    assert final_state.get("brand_health_report") is not None
    assert "Mecanismo Técnico" in final_state.get("final_response", "")


def test_graph_engine_runs_trench_inquiry_flow():
    engine = RickGraphEngine()
    state = create_initial_state(user_id="user_tr", handle="miguel_brand")

    state = update_state(
        state,
        trigger_type="trench_inquiry",
        proactive_context={
            "hours_since_last_ping": 72.0,
            "current_local_hour": 18,
            "silence_streak": 0,
            "confidence": 0.90,
            "inactive_days": 4,
        },
    )

    final_state = engine.run(state)
    assert "¿" in (final_state.get("final_response") or "")
    assert "nota de voz" in (final_state.get("final_response") or "").lower()
