"""Tests for Graph Engine compilation and WhatsApp conversational formatter (Task 9)."""
import pytest
from src.graph.state import (
    create_initial_state,
    ConversationMessage,
    ScriptDraft,
    ScriptBlock,
    EvaluationResult,
    WinningPattern,
)
from src.graph.formatter import format_script_whatsapp
from src.graph.engine import RickGraphEngine


def test_format_script_whatsapp_clean_delivery():
    draft = ScriptDraft(
        titulo="Error de Agencia",
        formato="Reel",
        duracion_objetivo=45,
        hook=ScriptBlock(
            texto="Le pagué dos mil dólares a una agencia para que me salvara el negocio... y casi me lo quiebra.",
            intencion="Desarmar objeción y capturar dolor",
            camara="Primer plano, directo al lente",
        ),
        desarrollo=ScriptBlock(
            texto="El error no fue de ellos. Fue mío, por querer comprar clientes con dinero en vez de entenderlos con tiempo.",
            intencion="Construir autoridad y vulnerabilidad",
            camara="Tono de café, como hablándole a un socio",
        ),
        cierre=ScriptBlock(
            texto="Antes de pagar para escalar, asegúrate de que tienes algo que funciona cuando estás tú solo.",
            intencion="Fijar regla de oro",
            camara="Pausa antes de cortar",
        ),
    )
    eval_result = EvaluationResult(
        score=9.4,
        passed=True,
        feedback="Aprobado",
        simulacion_estimacion="Alta",
        piezas_respaldo=5,
    )

    formatted = format_script_whatsapp(draft, eval_result)

    assert "HOOK" in formatted
    assert "DESARROLLO" in formatted
    assert "CIERRE" in formatted
    assert "Le pagué dos mil dólares" in formatted
    assert "(Cámara: Primer plano, directo al lente)" in formatted
    assert "9.4/10" in formatted or "5 videos" in formatted
    # Clean check: no markdown table delimiters or code blocks
    assert "|---|---|" not in formatted
    assert "```" not in formatted


def test_graph_engine_run_script_flow():
    engine = RickGraphEngine()
    initial_state = create_initial_state("user_101", "miguel_gomezpo")
    initial_state["messages"].append(
        ConversationMessage(
            role="user",
            content="Armemos el guion sobre el error que cometí contratando una agencia cara.",
        )
    )
    initial_state["story_extracted"] = "Le pagué dos mil dólares a una agencia y casi quiebro el negocio."

    final_state = engine.run(initial_state)

    assert final_state["script_draft"] is not None
    assert final_state["evaluation"] is not None
    assert final_state["evaluation"].passed is True
    assert final_state["final_response"] is not None
    assert "HOOK" in final_state["final_response"]
    assert "DESARROLLO" in final_state["final_response"]
    assert "CIERRE" in final_state["final_response"]


def test_graph_engine_run_report_flow():
    engine = RickGraphEngine()
    initial_state = create_initial_state("user_101", "miguel_gomezpo")
    initial_state["messages"].append(
        ConversationMessage(
            role="user",
            content="Muéstrame el reporte semanal de mi cuenta y mis métricas.",
        )
    )

    final_state = engine.run(initial_state)

    assert final_state["final_response"] is not None
    assert "Reporte" in final_state["final_response"] or "vistas" in final_state["final_response"]
    assert len(final_state["learnings"]) >= 1
