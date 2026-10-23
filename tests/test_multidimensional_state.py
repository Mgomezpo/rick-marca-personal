"""Tests for multidimensional content state models (Sagas, Pillars, Plans, Standalone)."""
import pytest
from pydantic import ValidationError
from src.graph.state import (
    ScriptBlock,
    ScriptDraft,
    SeriesMetadata,
)


def test_series_metadata_validation():
    series = SeriesMetadata(
        series_id="saga_agencia_2026",
        series_title="Los 3 Errores al Delegar Ventas",
        episode_index=1,
        total_episodes=3,
    )
    assert series.series_id == "saga_agencia_2026"
    assert series.series_title == "Los 3 Errores al Delegar Ventas"
    assert series.episode_index == 1
    assert series.total_episodes == 3
    assert series.previous_piece_id is None
    assert series.next_piece_id is None

    # Test JSON serialization
    dumped = series.model_dump()
    assert dumped["series_id"] == "saga_agencia_2026"
    assert dumped["episode_index"] == 1


def test_script_draft_with_multidimensional_fields():
    hook = ScriptBlock(texto="Hook texto", intencion="Intención", camara="Primer plano")
    desarrollo = ScriptBlock(texto="Desarrollo texto", intencion="Intención", camara="Plano medio")
    cierre = ScriptBlock(texto="Cierre texto", intencion="Intención", camara="Pausa")

    series = SeriesMetadata(
        series_id="saga_01",
        series_title="Saga de Prueba",
        episode_index=2,
        total_episodes=2,
        previous_piece_id="piece_ep1",
    )

    # Full multidimensional piece: has pillar, plan_id, and series
    draft = ScriptDraft(
        titulo="Episodio 2",
        formato="Reel",
        duracion_objetivo=45,
        hook=hook,
        desarrollo=desarrollo,
        cierre=cierre,
        pilar="Ventas B2B",
        series=series,
        plan_id="plan_octubre_2026",
    )

    assert draft.pilar == "Ventas B2B"
    assert draft.plan_id == "plan_octubre_2026"
    assert draft.series is not None
    assert draft.series.episode_index == 2
    assert draft.series.previous_piece_id == "piece_ep1"

    # Test serialization
    dumped = draft.model_dump()
    assert dumped["pilar"] == "Ventas B2B"
    assert dumped["plan_id"] == "plan_octubre_2026"
    assert dumped["series"]["series_id"] == "saga_01"


def test_script_draft_backward_compatibility_standalone():
    """Ensure standalone piece without series, pilar, or plan_id defaults cleanly to None."""
    hook = ScriptBlock(texto="Hook texto", intencion="Intención", camara="Primer plano")
    desarrollo = ScriptBlock(texto="Desarrollo texto", intencion="Intención", camara="Plano medio")
    cierre = ScriptBlock(texto="Cierre texto", intencion="Intención", camara="Pausa")

    draft = ScriptDraft(
        titulo="Pieza Única de Autoridad",
        hook=hook,
        desarrollo=desarrollo,
        cierre=cierre,
    )

    assert draft.pilar is None
    assert draft.series is None
    assert draft.plan_id is None

    dumped = draft.model_dump()
    assert dumped["pilar"] is None
    assert dumped["series"] is None
    assert dumped["plan_id"] is None
