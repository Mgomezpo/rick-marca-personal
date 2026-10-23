"""Tests for proactive loop nodes: Brand Health, Proactive Spark, and Trench Inquiry."""
import pytest
from src.graph.state import (
    create_initial_state,
    update_state,
    WinningPattern,
    GovernorDecision,
)
from src.agents.brand_health import (
    analyze_brand_health,
    brand_health_node,
    format_brand_health_whatsapp,
)
from src.agents.spark import (
    generate_proactive_spark,
    proactive_spark_node,
    format_spark_whatsapp,
)
from src.agents.trench import (
    generate_trench_inquiry,
    trench_inquiry_node,
)


def test_analyze_brand_health_detects_deserted_pillar():
    recent_posts = [
        {"topic": "Anécdota de fracaso", "pillar": "Casos Reales y Aprendizajes"},
        {"topic": "Cómo casi pierdo un cliente", "pillar": "Casos Reales y Aprendizajes"},
        {"topic": "Lección de vida", "pillar": "Casos Reales y Aprendizajes"},
        {"topic": "Reflexión del domingo", "pillar": "Casos Reales y Aprendizajes"},
    ]
    declared_pillars = [
        {"name": "Casos Reales y Aprendizajes", "target_pct": 50.0},
        {"name": "Arquitectura de Sistemas", "target_pct": 50.0},
    ]

    report = analyze_brand_health(
        user_id="usr_01",
        recent_posts=recent_posts,
        declared_pillars=declared_pillars,
    )

    assert report.overall_score < 7.0
    assert report.voice_drift_detected is True
    assert any(p.pillar_name == "Arquitectura de Sistemas" and p.status == "deserted" for p in report.pillars)
    formatted = format_brand_health_whatsapp(report, handle="miguel_dev")
    assert "Arquitectura de Sistemas" in formatted
    assert "demostración técnica" in formatted.lower() or "mecanismo" in formatted.lower()


def test_brand_health_node_integration():
    state = create_initial_state("usr_01", "miguel_dev")
    state = update_state(
        state,
        trigger_type="brand_health_audit",
        governor_decision=GovernorDecision(
            allowed=True,
            reason="Aprobado",
            hours_since_last_ping=30.0,
            current_local_hour=11,
        ),
        proactive_context={
            "recent_posts": [
                {"topic": "Charla general", "pillar": "Estilo de Vida"},
            ],
            "declared_pillars": [
                {"name": "Ingeniería de Agentes", "target_pct": 70.0},
                {"name": "Estilo de Vida", "target_pct": 30.0},
            ],
        },
    )

    result_state = brand_health_node(state)
    assert result_state.get("brand_health_report") is not None
    assert result_state.get("final_response") is not None
    assert "miguel_dev" in result_state.get("final_response")


def test_generate_proactive_spark_with_market_anomaly():
    pattern = WinningPattern(
        pattern_id="pat_01",
        tipo_hook="revelacion_contraria",
        formato="Reel",
        emocion="intriga",
        rendimiento_relativo_promedio=2.6,
        piezas_respaldo=4,
        ejemplos=["La gran mentira que te dijeron sobre crear software..."],
    )

    spark = generate_proactive_spark(
        creator_handle="miguel_dev",
        creator_nicho="Sistemas de IA y Automatización",
        winning_pattern=pattern,
        creator_thesis="Un state graph bien orquestado supera a 10 agentes desordenados",
        source_referent="@casidonovan",
    )

    assert spark.relative_performance == 2.6
    assert "@casidonovan" in spark.source_referent
    assert spark.suggested_hook != ""
    assert "state graph" in spark.adapted_angle.lower() or "agente" in spark.adapted_angle.lower()

    msg = format_spark_whatsapp(spark, handle="miguel_dev")
    assert "@casidonovan" in msg
    assert "2.6x" in msg
    assert "guion" in msg.lower()


def test_proactive_spark_node_integration():
    state = create_initial_state("usr_01", "miguel_dev")
    pattern = WinningPattern(
        pattern_id="pat_02",
        tipo_hook="demostracion_mecanismo",
        formato="Reel",
        emocion="curiosidad",
        rendimiento_relativo_promedio=2.2,
        piezas_respaldo=3,
        ejemplos=["Te muestro en 30 segundos cómo funciona por dentro..."],
    )
    state = update_state(
        state,
        trigger_type="market_spark",
        governor_decision=GovernorDecision(
            allowed=True,
            reason="Aprobado",
            hours_since_last_ping=28.0,
            current_local_hour=14,
        ),
        proactive_context={
            "winning_pattern": pattern,
            "source_referent": "@casidonovan",
            "thesis": "Arquitectura determinística sobre prompts caóticos",
        },
    )

    result_state = proactive_spark_node(state)
    assert result_state.get("proactive_spark") is not None
    assert result_state.get("final_response") is not None
    assert "2.2x" in result_state.get("final_response")


def test_generate_trench_inquiry_and_node():
    inquiry = generate_trench_inquiry(handle="miguel_dev", inactive_days=4)
    assert "¿" in inquiry
    assert "nota de voz" in inquiry.lower() or "frustrante" in inquiry.lower()

    state = create_initial_state("usr_01", "miguel_dev")
    state = update_state(
        state,
        trigger_type="trench_inquiry",
        governor_decision=GovernorDecision(
            allowed=True,
            reason="Aprobado",
            hours_since_last_ping=72.0,
            current_local_hour=16,
        ),
        proactive_context={"inactive_days": 4},
    )

    result_state = trench_inquiry_node(state)
    assert result_state.get("final_response") is not None
    assert "¿" in result_state.get("final_response")
