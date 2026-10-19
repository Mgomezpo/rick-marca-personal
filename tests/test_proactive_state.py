"""Tests for proactive loop models and state schema extensions."""
import pytest
from src.graph.state import (
    BrandPillarDistribution,
    BrandHealthReport,
    ProactiveSpark,
    GovernorDecision,
    GraphState,
    create_initial_state,
    update_state,
)


def test_brand_pillar_distribution_validation():
    pillar = BrandPillarDistribution(
        pillar_name="Arquitectura de Sistemas",
        target_percentage=40.0,
        actual_percentage=15.0,
        post_count=2,
        status="deserted",
    )
    assert pillar.status == "deserted"
    assert pillar.post_count == 2
    assert pillar.actual_percentage == 15.0


def test_brand_health_report_structure():
    pillar1 = BrandPillarDistribution(
        pillar_name="Sistemas",
        target_percentage=50.0,
        actual_percentage=20.0,
        post_count=2,
        status="deserted",
    )
    pillar2 = BrandPillarDistribution(
        pillar_name="Anécdotas Personales",
        target_percentage=50.0,
        actual_percentage=80.0,
        post_count=8,
        status="over_indexed",
    )

    report = BrandHealthReport(
        user_id="user_123",
        overall_score=6.5,
        pillars=[pillar1, pillar2],
        voice_drift_detected=True,
        voice_drift_notes="La comunicación se inclinó a historias personales perdiendo profundidad técnica.",
        key_recommendation="Equilibrar con 2 piezas demostrando el mecanismo de sistemas.",
        suggested_action="crear_demostracion_mecanismo",
    )
    assert report.user_id == "user_123"
    assert report.voice_drift_detected is True
    assert len(report.pillars) == 2


def test_proactive_spark_model():
    spark = ProactiveSpark(
        spark_id="spark_001",
        source_referent="@casidonovan",
        referent_hook_text="La mentira que te dijeron sobre programar...",
        relative_performance=2.8,
        adapted_angle="El mito de que necesitas 10 agentes cuando un solo state graph resuelve el 90%",
        suggested_hook="Te vendieron la fantasía de 10 agentes trabajando juntos. La verdad es más simple y dolorosa.",
        target_pillar="Arquitectura de Sistemas",
        confidence=0.92,
    )
    assert spark.relative_performance == 2.8
    assert spark.confidence >= 0.85


def test_governor_decision_model():
    decision = GovernorDecision(
        allowed=True,
        reason="Ventana horaria y cooldown cumplidos",
        hours_since_last_ping=26.5,
        current_local_hour=11,
        silence_streak=0,
        backoff_cooldown_hours=24.0,
    )
    assert decision.allowed is True
    assert decision.hours_since_last_ping > 24.0


def test_graph_state_proactive_fields_integration():
    state = create_initial_state(user_id="creator_test_01", handle="miguel_dev")
    assert state.get("trigger_type") == "user_message"
    assert state.get("brand_health_report") is None

    # Functional update with proactive spark
    spark = ProactiveSpark(
        spark_id="sp_99",
        source_referent="@test_ref",
        referent_hook_text="Hook de prueba",
        relative_performance=2.1,
        adapted_angle="Ángulo adaptado de prueba",
        suggested_hook="Gancho sugerido",
        target_pillar="General",
        confidence=0.88,
    )

    updated = update_state(
        state,
        trigger_type="market_spark",
        proactive_spark=spark,
    )

    assert updated["trigger_type"] == "market_spark"
    assert updated["proactive_spark"].spark_id == "sp_99"
    # Ensure immutability of original state
    assert state.get("trigger_type") == "user_message"
