"""End-to-End Multi-turn conversational UX simulation and tuning (Task 11).

Simulates a real conversation between creator @miguel_gomezpo and RICK,
referencing benchmark patterns from @casidonovan.
"""
import pytest
from src.graph.state import (
    create_initial_state,
    ConversationMessage,
    WinningPattern,
    CreatorProfile,
)
from src.graph.engine import RickGraphEngine
from src.matrix.analyzer import MarketRadar
from src.matrix.models import MatrixRow


def test_multiturn_conversational_ux_flow():
    engine = RickGraphEngine()

    # Setup profile for @miguel_gomezpo referencing @casidonovan
    state = create_initial_state("user_miguel_01", "miguel_gomezpo")
    state["creator_profile"] = CreatorProfile(
        user_id="user_miguel_01",
        instagram_handle="miguel_gomezpo",
        nicho="Estrategia y Negocios",
        mediana_views=12000.0,
        referentes=["casidonovan"],
    )

    # Ingest benchmark pattern from referent @casidonovan
    state["winning_patterns"] = [
        WinningPattern(
            pattern_id="pat_casi_01",
            tipo_hook="confesion_error",
            formato="historia_personal",
            emocion="vulnerabilidad",
            rendimiento_relativo_promedio=2.8,
            piezas_respaldo=5,
            ejemplos=["Le pagué dos mil dólares a una agencia y casi me quiebran."],
        )
    ]

    # --- Turn 1: Saludo inicial ---
    state["messages"].append(ConversationMessage(role="user", content="Hola RICK, cómo andas?"))
    state = engine.run(state)

    res1 = state["final_response"]
    assert res1 is not None
    assert len(res1.split()) <= 60  # Level 1 concise
    assert "¿" in res1  # Invites conversation

    # --- Turn 2: Creador trae una anécdota vaga ---
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="Ayer me fue mal con un lanzamiento de producto y no sé qué decir en redes.",
        )
    )
    state = engine.run(state)

    res2 = state["final_response"]
    assert res2 is not None
    # Level 2 Rubin rule: asks 1 question (La Escena)
    assert res2.count("?") == 1
    assert "escena" in res2.lower() or "pasó" in res2.lower() or "momento" in res2.lower()

    # --- Turn 3: Creador detalla la escena ---
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="En la reunión de apertura no entró ninguna venta en 4 horas y me desesperé.",
        )
    )
    state = engine.run(state)

    res3 = state["final_response"]
    assert res3 is not None
    # Asks for the real friction
    assert res3.count("?") == 1
    assert "fricción" in res3.lower() or "error" in res3.lower()

    # --- Turn 4 & 5: Creador detalla el error real y pide guion ---
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="El error real fue que construí la oferta sin validar si resolvía un dolor real. Armemos el guion.",
        )
    )
    state = engine.run(state)

    res4 = state["final_response"]
    assert res4 is not None
    # Script generated in canonical 3 blocks
    assert "HOOK" in res4
    assert "DESARROLLO" in res4
    assert "CIERRE" in res4
    assert "Cámara:" in res4
    assert "calibré contra 5 videos" in res4 or "probabilidad" in res4
    # Zero artificial slop or markdown code blocks
    assert "```" not in res4
    assert "|---|" not in res4

    # --- Turn 6: Consulta de auditoría de cuenta propia ---
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="¿Cómo van las métricas de mi cuenta de Instagram esta semana?",
        )
    )
    state = engine.run(state)

    res5 = state["final_response"]
    assert res5 is not None
    assert "miguel_gomezpo" in res5
    assert "Reporte" in res5
    assert "views" in res5.lower() or "vistas" in res5.lower() or "mediana" in res5.lower()


def test_scraping_failure_graceful_degradation():
    """
    Verify that if external network/scraping fails or times out,
    the radar falls back gracefully to cached winning patterns without breaking UX.
    """
    radar = MarketRadar()

    # Empty inputs simulate an Apify / network timeout
    results = radar.analyze_dual_radar(referents_rows=[], discovery_rows=[])

    assert results["is_fallback"] is True
    assert len(results["top_patterns"]) >= 1

    top = results["top_pattern"]
    assert top.rendimiento_relativo_promedio >= 1.5
    assert top.tipo_hook is not None
