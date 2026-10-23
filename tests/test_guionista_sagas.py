"""Tests for narrative continuity and cliffhangers in episodic sagas (Fase 3)."""
import pytest
from src.graph.state import (
    WinningPattern,
    CreatorProfile,
    SeriesMetadata,
    ScriptDraft,
)
from src.agents.guionista import generate_script_draft


@pytest.fixture
def base_pattern():
    return WinningPattern(
        pattern_id="pat_confesion",
        tipo_hook="confesion_error",
        formato="historia_personal",
        emocion="vulnerabilidad",
        rendimiento_relativo_promedio=2.4,
        piezas_respaldo=5,
    )


@pytest.fixture
def profile():
    return CreatorProfile(
        user_id="u_miguel",
        instagram_handle="miguel_gomezpo",
        nicho="Estrategia",
    )


def test_standalone_piece_clean_autoconclusive(base_pattern, profile):
    """Piece without series maintains standard 3-block autoconclusive structure."""
    story = "Le pagué 2000 dólares a una agencia para delegar clientes y casi fundo la empresa."
    draft = generate_script_draft(story=story, pattern=base_pattern, profile=profile)

    assert draft.series is None
    # No forced episodic words in hook or cierre
    assert "episodio" not in draft.hook.texto.lower()
    assert "parte 2" not in draft.cierre.texto.lower()
    assert "siguiente episodio" not in draft.cierre.texto.lower()
    assert "Antes de invertir" in draft.cierre.texto


def test_saga_episode_1_cliffhanger(base_pattern, profile):
    """Episode 1 of a saga includes a cliffhanger to episode 2 in the closing."""
    series = SeriesMetadata(
        series_id="saga_agencia_2026",
        series_title="La Trampa de las Agencias",
        episode_index=1,
        total_episodes=2,
    )
    story = "Le pagué 2000 dólares a una agencia para delegar clientes y casi fundo la empresa."

    draft = generate_script_draft(
        story=story,
        pattern=base_pattern,
        profile=profile,
        series=series,
    )

    assert draft.series is not None
    assert draft.series.episode_index == 1
    # Cierre has cliffhanger towards episode 2
    assert "parte 2" in draft.cierre.texto.lower() or "episodio 2" in draft.cierre.texto.lower()
    assert "cliffhanger" in draft.cierre.intencion.lower()


def test_saga_episode_2_continuity_hook(base_pattern, profile):
    """Episode 2 of a saga includes continuity hook referencing the previous episode."""
    series = SeriesMetadata(
        series_id="saga_agencia_2026",
        series_title="La Trampa de las Agencias",
        episode_index=2,
        total_episodes=2,
        previous_piece_id="piece_ep1_id",
    )
    story = "El segundo error fue no tener un proceso de ventas claro antes de contratar."

    draft = generate_script_draft(
        story=story,
        pattern=base_pattern,
        profile=profile,
        series=series,
    )

    assert draft.series is not None
    assert draft.series.episode_index == 2
    # Hook links to previous delivery
    hook_lower = draft.hook.texto.lower()
    assert "ayer" in hook_lower or "parte" in hook_lower or "episodio" in hook_lower
    assert "continuidad" in draft.hook.intencion.lower()
