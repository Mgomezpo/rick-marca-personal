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


def test_rick_node_direct_transition_when_scene_and_friction_provided():
    state = create_initial_state("user_1", "miguel_gomezpo")
    state["messages"].append(
        ConversationMessage(
            role="user",
            content="Ayer en la reunión con el cliente el error que cometí fue no validar la oferta.",
        )
    )
    state["current_intent"] = "extract_story"

    result_state = rick_strategist_node(state)
    assert result_state["current_intent"] == "generate_script"
    assert "guion" in result_state["final_response"].lower()


def test_rick_system_prompt_and_nodes_embody_internal_team_identity():
    # Prompt asserts internal team belonging
    assert "Head of Content" in RICK_CANONICAL_SYSTEM_PROMPT
    assert "nuestro canal" in RICK_CANONICAL_SYSTEM_PROMPT
    assert "revisemos" in RICK_CANONICAL_SYSTEM_PROMPT

    # Absence of cold external consultant or generic chatbot phrases
    banned_external_phrases = [
        "tu consultor", "servicio externo", "como IA", "como modelo de lenguaje",
        "mi cliente", "te entrego la consultoría"
    ]
    for banned in banned_external_phrases:
        assert banned not in RICK_CANONICAL_SYSTEM_PROMPT


def test_trench_inquiry_internal_team_voice():
    from src.agents.trench import generate_trench_inquiry
    msg = generate_trench_inquiry("miguel_dev")
    # Loop 3 identity: team member in the trenches
    assert "equipo" in msg.lower()
    assert "mover piezas" in msg.lower()
    assert "nota de voz" in msg.lower()
    assert "guion" in msg.lower()


def test_spark_whatsapp_internal_team_voice():
    from src.agents.spark import generate_proactive_spark, format_spark_whatsapp
    from src.graph.state import WinningPattern
    pattern = WinningPattern(
        pattern_id="wp_test",
        tipo_hook="revelacion_contraria",
        formato="Reel",
        emocion="intriga",
        rendimiento_relativo_promedio=2.5,
        piezas_respaldo=3,
        ejemplos=["Hook de prueba"],
    )
    spark = generate_proactive_spark(
        creator_handle="miguel_dev",
        creator_nicho="Sistemas",
        winning_pattern=pattern,
        creator_thesis="Menos agentes, más control determinístico",
        source_referent="@casidonovan",
    )
    msg = format_spark_whatsapp(spark, handle="miguel_dev")
    assert "radar del equipo" in msg.lower()
    assert "nuestra tesis" in msg.lower()
    assert "luz verde" in msg.lower()


def test_rick_node_blocked_creator_heavy_lifting():
    state = create_initial_state("user_1", "miguel_gomezpo")
    state["messages"].append(
        ConversationMessage(role="user", content="Tengo la mente en blanco, no sé qué decir.")
    )

    result_state = rick_strategist_node(state)
    response = result_state["final_response"]

    assert response is not None
    assert result_state["current_intent"] == "extract_story"
    # Heavy lifting: gives real options from receipts
    assert "tranquilo" in response.lower() or "no tienes que inventar" in response.lower()
    assert "1." in response and "2." in response


def test_rick_node_meta_question_handling():
    state = create_initial_state("user_1", "miguel_gomezpo")
    state["messages"].append(
        ConversationMessage(role="user", content="¿Por qué debería usarte a ti en vez de a ChatGPT?")
    )

    result_state = rick_strategist_node(state)
    response = result_state["final_response"]

    assert response is not None
    # Answers with wit and redirects
    assert "chatgpt" in response.lower() or "contexto" in response.lower()
    assert "¿" in response  # Smooth redirection question


