"""Tests for RICK Strategist Node, Rubin mayeutic inquiry, and intent routing (Task 5)."""
import pytest
from src.graph.state import (
    create_initial_state,
    ConversationMessage,
    update_state,
)
from src.agents.rick import (
    classify_intent,
    rick_strategist_node,
    extract_story_elements,
)
from src.agents.prompts import RICK_CANONICAL_SYSTEM_PROMPT


def test_rick_canonical_prompt_contains_rubin_principles():
    assert "Rick Rubin" in RICK_CANONICAL_SYSTEM_PROMPT or "The Creative Act" in RICK_CANONICAL_SYSTEM_PROMPT
    assert "HOOOK" not in RICK_CANONICAL_SYSTEM_PROMPT
    assert "HOOK" in RICK_CANONICAL_SYSTEM_PROMPT
    assert "DESARROLLO" in RICK_CANONICAL_SYSTEM_PROMPT
    assert "CIERRE" in RICK_CANONICAL_SYSTEM_PROMPT
    assert "Cero relleno" in RICK_CANONICAL_SYSTEM_PROMPT or "economía de palabras" in RICK_CANONICAL_SYSTEM_PROMPT


def test_classify_intent_matrix():
    state = create_initial_state("user_1", "miguel_gomezpo")

    # Intent: chat
    assert classify_intent("Hola RICK, qué tal?", state) == "chat"
    assert classify_intent("Buenas tardes", state) == "chat"

    # Intent: extract_story
    assert classify_intent("Ayer tuve un problema grave con un cliente que canceló.", state) == "extract_story"
    assert classify_intent("Se me ocurrió una anécdota de cuando fundé mi primera empresa.", state) == "extract_story"

    # Intent: generate_script
    assert classify_intent("Armemos el guion para este reel ya.", state) == "generate_script"
    assert classify_intent("Escribe el guion con esta historia.", state) == "generate_script"

    # Intent: view_report
    assert classify_intent("¿Cómo van las métricas de mi cuenta de Instagram?", state) == "view_report"
    assert classify_intent("Muéstrame el reporte semanal y los learnings.", state) == "view_report"


def test_extract_story_elements_accumulates_scene_and_friction():
    state = create_initial_state("user_1", "miguel_gomezpo")

    # Turn 1: user brings an idea
    state["messages"].append(
        ConversationMessage(role="user", content="Contraté una agencia cara y casi me funden.")
    )
    story1 = extract_story_elements(state)
    assert "agencia" in story1.lower()

    # Turn 2: user details the scene and friction
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="En la reunión me mostraron métricas vanidosas pero cero ventas reales.",
        )
    )
    story2 = extract_story_elements(state)
    assert "reunión" in story2.lower() or "ventas" in story2.lower()


def test_rick_node_chat_level1_word_count_and_tone():
    state = create_initial_state("user_1", "miguel_gomezpo")
    state["messages"].append(ConversationMessage(role="user", content="Hola RICK, listo para trabajar."))
    state["current_intent"] = "chat"

    result_state = rick_strategist_node(state)
    response = result_state["final_response"]

    assert response is not None
    assert len(response.split()) <= 70  # Nivel 1 limit: concise, no fluff
    # No robotic greetings
    assert "Como modelo de lenguaje" not in response
    assert "¡Por supuesto!" not in response
    assert "¡Hola! Estoy aquí para ayudarte" not in response


def test_rick_node_inquiry_asks_one_question():
    state = create_initial_state("user_1", "miguel_gomezpo")
    state["messages"].append(
        ConversationMessage(role="user", content="Quiero hablar sobre cuando quebró mi primer negocio.")
    )
    state["current_intent"] = "extract_story"

    result_state = rick_strategist_node(state)
    response = result_state["final_response"]

    assert response is not None
    # Level 2 rule: 1 single question per turn
    question_marks = response.count("?")
    assert question_marks == 1
    assert result_state["story_extracted"] is not None
