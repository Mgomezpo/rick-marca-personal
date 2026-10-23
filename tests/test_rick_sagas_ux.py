"""Tests for RICK conversational orchestration: multi-point detection, saga suggestion, and creator choice (Fase 4)."""
import pytest
from src.graph.state import (
    create_initial_state,
    ConversationMessage,
    SeriesMetadata,
)
from src.agents.rick import (
    classify_intent,
    rick_strategist_node,
)
from src.graph.engine import RickGraphEngine


def test_classify_intent_saga_and_single_choice():
    state = create_initial_state("user_1", "miguel_gomezpo")
    state["current_intent"] = "extract_story"

    # User choosing single piece
    assert classify_intent("Hagamos una sola pieza al grano.", state) == "generate_script"
    assert classify_intent("Una sola", state) == "generate_script"
    assert classify_intent("Al grano", state) == "generate_script"

    # User choosing saga
    assert classify_intent("Armemos una saga de 2 partes.", state) == "generate_script"
    assert classify_intent("En 2 partes mejor", state) == "generate_script"
    assert classify_intent("Miniserie", state) == "generate_script"


def test_rick_suggests_saga_on_multipoint_dense_story():
    state = create_initial_state("user_1", "miguel_gomezpo")
    state["current_intent"] = "extract_story"
    # Story with two distinct errors / multiple points
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="En la reunión de apertura vi dos errores graves: el error de delegar las ventas y el error de no medir el CAC.",
        )
    )

    result_state = rick_strategist_node(state)
    response = result_state["final_response"]

    assert response is not None
    # RICK suggests peer choice without imposing
    assert "¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?" in response
    assert result_state["current_intent"] == "extract_story"


def test_user_chooses_single_piece_generates_standalone():
    engine = RickGraphEngine()
    state = create_initial_state("user_1", "miguel_gomezpo")

    # Step 1: User brings dense story
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="En la reunión vi dos errores graves: delegar ventas y no medir el CAC.",
        )
    )
    state = engine.run(state)
    assert "¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?" in state["final_response"]

    # Step 2: User responds "una sola"
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="Una sola al grano por favor.",
        )
    )
    state = engine.run(state)

    draft = state.get("script_draft")
    assert draft is not None
    assert draft.series is None
    assert "HOOK" in state["final_response"]


def test_user_chooses_saga_generates_series_metadata():
    engine = RickGraphEngine()
    state = create_initial_state("user_1", "miguel_gomezpo")

    # Step 1: User brings dense story
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="En la oficina vi dos errores graves: delegar ventas y no medir el CAC.",
        )
    )
    state = engine.run(state)
    assert "¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?" in state["final_response"]

    # Step 2: User responds "saga de 2 partes"
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="Armemos la saga de 2 partes.",
        )
    )
    state = engine.run(state)

    draft = state.get("script_draft")
    assert draft is not None
    assert draft.series is not None
    assert draft.series.episode_index == 1
    assert draft.series.total_episodes == 2
    assert "parte 2" in draft.cierre.texto.lower()
