"""Tests for core state schema and data models (Task 2)."""
import pytest
from pydantic import ValidationError

from src.graph.state import (
    ScriptBlock,
    ScriptDraft,
    CreatorProfile,
    EvaluationResult,
    WinningPattern,
    LearningItem,
    ConversationMessage,
    GraphState,
    create_initial_state,
    update_state,
)


def test_script_block_and_draft_validation():
    hook = ScriptBlock(
        texto="Le pagué dos mil dólares a una agencia y casi me quiebran.",
        intencion="Desarmar objeción y capturar dolor",
        camara="Primer plano directo al lente",
    )
    desarrollo = ScriptBlock(
        texto="El error no fue de ellos, fue mío por delegar la venta.",
        intencion="Vulnerabilidad y quiebre de creencia",
        camara="Plano medio relajado",
    )
    cierre = ScriptBlock(
        texto="Antes de escalar, aprende a vender tú solo.",
        intencion="Fijar regla de oro",
        camara="Pausa de 1 segundo antes de corte",
    )

    draft = ScriptDraft(
        titulo="Lección de Agencia",
        formato="Reel",
        duracion_objetivo=45,
        hook=hook,
        desarrollo=desarrollo,
        cierre=cierre,
    )

    assert draft.titulo == "Lección de Agencia"
    assert draft.hook.texto.startswith("Le pagué")
    assert draft.duracion_objetivo == 45


def test_script_block_missing_fields_raises_error():
    with pytest.raises(ValidationError):
        ScriptBlock(texto="Solo texto sin intencion ni camara")


def test_creator_profile_and_learnings():
    profile = CreatorProfile(
        user_id="user_123",
        instagram_handle="miguel_gomezpo",
        nicho="Estrategia y Negocios",
        mediana_views=12500.0,
        referentes=["casidonovan", "alexhormozi"],
    )
    assert profile.user_id == "user_123"
    assert profile.referentes == ["casidonovan", "alexhormozi"]

    learning = LearningItem(
        user_id="user_123",
        statement="Las confesiones de errores en tu negocio te dan 2.2x más retención.",
        applies_when="Planificación de guiones semanales",
        confidence=0.92,
    )
    assert learning.confidence == 0.92
    assert "2.2x" in learning.statement


def test_winning_pattern_and_evaluation_result():
    pattern = WinningPattern(
        pattern_id="pat_01",
        tipo_hook="Confesión de error",
        formato="Historia personal",
        emocion="Vulnerabilidad",
        rendimiento_relativo_promedio=2.3,
        piezas_respaldo=5,
        ejemplos=["Video 1", "Video 2"],
    )
    assert pattern.rendimiento_relativo_promedio == 2.3

    eval_result = EvaluationResult(
        score=9.2,
        passed=True,
        feedback="Tono auténtico y sin jerga de gurú.",
        plagio_detectado=False,
        max_palabras_coincidentes=3,
        simulacion_estimacion="Alta",
        piezas_respaldo=5,
    )
    assert eval_result.passed is True
    assert eval_result.score == 9.2
    assert eval_result.max_palabras_coincidentes <= 4


def test_create_initial_state_and_functional_update():
    initial_state = create_initial_state(user_id="user_999", handle="miguel_gomezpo")
    assert initial_state["user_id"] == "user_999"
    assert initial_state["creator_profile"] is not None
    assert initial_state["creator_profile"].instagram_handle == "miguel_gomezpo"
    assert initial_state["current_intent"] == "chat"
    assert initial_state["iteration_count"] == 0
    assert isinstance(initial_state["messages"], list)

    # Inmutable update: returns a new state dictionary
    updated = update_state(
        initial_state,
        current_intent="generate_script",
        iteration_count=1,
    )
    assert updated["current_intent"] == "generate_script"
    assert updated["iteration_count"] == 1
    # Original remains untouched
    assert initial_state["current_intent"] == "chat"
    assert initial_state["iteration_count"] == 0


def test_state_json_serializability():
    draft = ScriptDraft(
        titulo="Guion Test",
        formato="TikTok",
        duracion_objetivo=30,
        hook=ScriptBlock(texto="Hook!", intencion="Intención", camara="Frontal"),
        desarrollo=ScriptBlock(texto="Desarrollo!", intencion="Historia", camara="Lateral"),
        cierre=ScriptBlock(texto="Cierre!", intencion="Llamado", camara="Pausa"),
    )
    draft_dict = draft.model_dump()
    assert draft_dict["titulo"] == "Guion Test"
    assert draft_dict["hook"]["texto"] == "Hook!"
    json_str = draft.model_dump_json()
    assert "Guion Test" in json_str

