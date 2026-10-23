"""Tests for technical script writer node (Task 6)."""
import pytest
from src.graph.state import (
    create_initial_state,
    CreatorProfile,
    WinningPattern,
    ScriptDraft,
)
from src.agents.guionista import (
    generate_script_draft,
    guionista_node,
)


def test_generate_script_draft_canonical_structure():
    profile = CreatorProfile(
        user_id="u1",
        instagram_handle="miguel_gomezpo",
        nicho="Estrategia y Negocios",
        tono_voz="directo y de trinchera",
    )
    pattern = WinningPattern(
        pattern_id="pat_confesion",
        tipo_hook="confesion_error",
        formato="historia_personal",
        emocion="vulnerabilidad",
        rendimiento_relativo_promedio=2.4,
        piezas_respaldo=5,
        ejemplos=["Le pagué a una agencia y casi me quiebran."],
    )
    story = "Le pagué 2000 dólares a una agencia para delegar clientes y casi fundo la empresa porque no entendía mi propuesta."

    draft = generate_script_draft(story=story, pattern=pattern, profile=profile)

    assert isinstance(draft, ScriptDraft)
    assert draft.titulo is not None and len(draft.titulo) > 0
    assert draft.formato == "Reel"
    assert draft.duracion_objetivo > 0

    # Block 1: HOOK
    assert draft.hook.texto is not None and len(draft.hook.texto) > 10
    assert draft.hook.intencion is not None
    assert draft.hook.camara is not None
    # No greetings in hook
    assert "Hola a todos" not in draft.hook.texto
    assert "Bienvenidos a mi perfil" not in draft.hook.texto

    # Block 2: DESARROLLO
    assert draft.desarrollo.texto is not None and len(draft.desarrollo.texto) > 20
    assert draft.desarrollo.intencion is not None
    assert draft.desarrollo.camara is not None

    # Block 3: CIERRE
    assert draft.cierre.texto is not None and len(draft.cierre.texto) > 10
    assert draft.cierre.intencion is not None
    assert draft.cierre.camara is not None


def test_guionista_node_in_graph_state():
    state = create_initial_state("user_100", "miguel_gomezpo")
    state["story_extracted"] = "Perdí tres meses tratando de optimizar anuncios en vez de hablar con 10 clientes."
    state["winning_patterns"] = [
        WinningPattern(
            pattern_id="pat_quiebre",
            tipo_hook="quiebre_creencia",
            formato="historia_personal",
            emocion="autoridad",
            rendimiento_relativo_promedio=2.1,
            piezas_respaldo=4,
        )
    ]

    new_state = guionista_node(state)

    assert new_state["script_draft"] is not None
    draft = new_state["script_draft"]
    assert draft.hook.texto is not None
    assert draft.desarrollo.texto is not None
    assert draft.cierre.texto is not None
    assert new_state["iteration_count"] == 1


def test_generate_script_draft_dual_coding_contrast():
    profile = CreatorProfile(user_id="u1", instagram_handle="miguel_gomezpo")
    pattern = WinningPattern(
        pattern_id="pat_quiebre",
        tipo_hook="quiebre_creencia",
        formato="historia_personal",
        emocion="autoridad",
        rendimiento_relativo_promedio=2.2,
        piezas_respaldo=4,
    )
    draft = generate_script_draft("Construí software que nadie quería.", pattern, profile)

    assert draft.visual_hook is not None
    assert len(draft.visual_hook) > 0
    assert draft.spoken_hook is not None
    assert len(draft.spoken_hook) > 0
    assert draft.friction_step is not None

