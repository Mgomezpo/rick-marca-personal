"""Tests for Cognitive Reasoning, Dual-Model Routing, Feedback-Driven Rewrite Loop, and Window Compression."""
import os
import pytest
from src.graph.state import (
    create_initial_state,
    ConversationMessage,
    StoryReceipt,
    ScriptDraft,
    ScriptBlock,
    WinningPattern,
    StrategistReasoning,
)
from src.services.llm import LLMService, llm_service
from src.agents.rick import rick_strategist_node
from src.agents.guionista import generate_script_draft, guionista_node
from src.agents.evaluator import evaluate_script_quality, evaluator_node
from src.services.session_runner import compress_conversation_window


def test_dual_model_configuration():
    """Verify LLMService reads orchestrator and writer models from environment."""
    os.environ["ORCHESTRATOR_MODEL"] = "gemini-2.5-flash-lite"
    os.environ["WRITER_MODEL"] = "gemini-2.5-pro"
    service = LLMService()
    assert service.orchestrator_model == "gemini-2.5-flash-lite"
    assert service.writer_model == "gemini-2.5-pro"


def test_strategist_reasoning_generation_and_storage():
    """Verify StrategistReasoning is generated and saved in state['reasoning_trace']."""
    state = create_initial_state(user_id="user_test_cognition", handle="miguel_gomezpo")
    state["story_bank"] = [
        StoryReceipt(
            id="rec_excel_test",
            summary="Automatización de Excel para clínica dental",
            theme="Alivio humano supera software inflado",
            concrete_details=["Excel", "30 minutos", "VBA"],
            punchline="Devolver tiempo real al cliente",
        )
    ]
    state["messages"] = [
        ConversationMessage(role="user", content="Tengo la mente en blanco, no sé qué grabar hoy.")
    ]

    result_state = rick_strategist_node(state)

    trace = result_state.get("reasoning_trace")
    assert trace is not None
    assert isinstance(trace, StrategistReasoning)
    assert trace.user_subtext != ""
    assert trace.cliche_trap_to_avoid != ""
    assert trace.contrarian_angle != ""
    assert trace.routed_intent in ["blocked_creator", "extract_story"]
    assert trace.selected_receipt_id is not None


def test_feedback_driven_rewrite_clears_slop_and_passes():
    """Verify that when evaluator rejects a draft with slop/plagiarism in iteration 1,
    guionista_node receives the feedback in iteration 2 and corrects it until passing."""
    referent_text = "le pagué dos mil dólares a una agencia para delegar clientes"
    state = create_initial_state(user_id="user_loop", handle="miguel_gomezpo")
    state["story_extracted"] = "Perdí tres meses por delegar anuncios sin entender mi propia oferta."
    state["referents_context"] = [{"text": referent_text}]
    state["winning_patterns"] = [
        WinningPattern(
            pattern_id="pat_1",
            tipo_hook="confesion_error",
            formato="historia_personal",
            emocion="vulnerabilidad",
            rendimiento_relativo_promedio=2.2,
            piezas_respaldo=4,
        )
    ]

    # Iteration 1: Create a flawed draft containing slop phrases and plagiarized text
    flawed_draft = ScriptDraft(
        titulo="Borrador con Slop",
        formato="Reel",
        duracion_objetivo=45,
        hook=ScriptBlock(
            texto=f"Hola a todos. {referent_text} y en este mundo cambiante descubrí el secreto.",
            intencion="Enganche con fallas",
            camara="Plano general",
            visual_text="En este mundo cambiante",
        ),
        desarrollo=ScriptBlock(
            texto="Hoy en día todos buscan la fórmula mágica sin precedentes para revolucionar su vida.",
            intencion="Desarrollo con clichés",
            camara="Plano medio",
        ),
        cierre=ScriptBlock(
            texto="En conclusión, desata tu potencial ahora mismo.",
            intencion="Cierre con slop",
            camara="Corte a negro",
        ),
        visual_hook="En este mundo cambiante",
        spoken_hook=f"Hola a todos. {referent_text}",
    )
    state["script_draft"] = flawed_draft
    state["iteration_count"] = 1

    # Run evaluator on iteration 1: MUST FAIL
    eval_state = evaluator_node(state)
    assert eval_state["evaluation"] is not None
    assert eval_state["evaluation"].passed is False
    assert eval_state["evaluation"].score < 8.0
    feedback = eval_state["evaluation"].feedback
    assert "cliché" in feedback.lower() or "plagio" in feedback.lower() or "saludo" in feedback.lower()

    # Iteration 2: guionista_node executes rewrite using feedback
    rewritten_state = guionista_node(eval_state)
    assert rewritten_state["iteration_count"] == 2
    corrected_draft = rewritten_state["script_draft"]
    assert corrected_draft is not None

    # Verify that forbidden slop phrases were removed
    full_text = f"{corrected_draft.hook.texto} {corrected_draft.desarrollo.texto} {corrected_draft.cierre.texto}".lower()
    assert "en este mundo cambiante" not in full_text
    assert "descubre el secreto" not in full_text
    assert "fórmula mágica" not in full_text
    assert "hola a todos" not in full_text
    assert referent_text.lower() not in full_text

    # Run evaluator on iteration 2: MUST PASS
    final_eval_state = evaluator_node(rewritten_state)
    assert final_eval_state["evaluation"].passed is True
    assert final_eval_state["evaluation"].score >= 8.0


def test_compress_conversation_window_limits_tokens():
    """Verify that conversations exceeding 12 turns are compressed into a compact window."""
    # Generate 24 turns
    messages = []
    for i in range(24):
        role = "user" if i % 2 == 0 else "assistant"
        content = f"Mensaje número {i+1} de la conversación sobre estrategia de contenidos y ganchos."
        messages.append(ConversationMessage(role=role, content=content))

    assert len(messages) == 24

    compressed = compress_conversation_window(messages, max_recent=10, threshold=12)

    # Must contain 1 synthetic summary message + 10 recent messages = 11 total
    assert len(compressed) == 11
    assert compressed[0].role == "system"
    assert "Contexto de conversación previa comprimido (14 mensajes)" in compressed[0].content
    # The last message must match the last original message
    assert compressed[-1].content == messages[-1].content
