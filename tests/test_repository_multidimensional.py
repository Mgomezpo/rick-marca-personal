"""Tests for SupabaseRepository multidimensional content mapping and isolation (Fase 2)."""
import pytest
from src.graph.state import (
    ScriptBlock,
    ScriptDraft,
    SeriesMetadata,
)
from src.db.repository import SupabaseRepository


@pytest.fixture
def repo():
    return SupabaseRepository()


def test_save_piece_standalone_clean_mapping(repo):
    """Standalone piece with no series, no pilar, no plan_id."""
    hook = ScriptBlock(texto="Hook!", intencion="Captura", camara="Primer plano")
    desarrollo = ScriptBlock(texto="Desarrollo!", intencion="Cuerpo", camara="Plano medio")
    cierre = ScriptBlock(texto="Cierre!", intencion="Llamado", camara="Pausa")

    draft = ScriptDraft(
        titulo="Pieza Suelta",
        hook=hook,
        desarrollo=desarrollo,
        cierre=cierre,
    )

    piece_id = repo.save_piece("user_solo", draft)
    assert piece_id is not None

    pieces = repo.get_pieces("user_solo")
    assert len(pieces) == 1
    p = pieces[0]
    assert p["id"] == piece_id
    assert p["user_id"] == "user_solo"
    assert p["strategy_tag"] is None
    assert p["plan_id"] is None
    assert p["idea_fields"] == {}


def test_save_piece_multidimensional_mapping(repo):
    """Piece with pillar, plan_id, and series metadata."""
    hook = ScriptBlock(texto="Hook!", intencion="Captura", camara="Primer plano")
    desarrollo = ScriptBlock(texto="Desarrollo!", intencion="Cuerpo", camara="Plano medio")
    cierre = ScriptBlock(texto="Cierre!", intencion="Llamado", camara="Pausa")

    series = SeriesMetadata(
        series_id="saga_scale_up",
        series_title="Cómo Escalar a $50k",
        episode_index=1,
        total_episodes=3,
    )

    draft = ScriptDraft(
        titulo="Episodio 1: La Trampa de la Agencia",
        hook=hook,
        desarrollo=desarrollo,
        cierre=cierre,
        pilar="Estrategia",
        plan_id="plan_q4_2026",
        series=series,
    )

    piece_id = repo.save_piece("user_multi", draft)
    assert piece_id is not None

    pieces = repo.get_pieces("user_multi")
    assert len(pieces) == 1
    p = pieces[0]
    assert p["strategy_tag"] == "Estrategia"
    assert p["plan_id"] == "plan_q4_2026"
    assert "series" in p["idea_fields"]
    assert p["idea_fields"]["series"]["series_id"] == "saga_scale_up"
    assert p["idea_fields"]["series"]["episode_index"] == 1


def test_get_series_pieces_sorting_and_isolation(repo):
    """Verify get_series_pieces returns ordered episodes strictly scoped to user_id."""
    hook = ScriptBlock(texto="H", intencion="I", camara="C")
    desarrollo = ScriptBlock(texto="D", intencion="I", camara="C")
    cierre = ScriptBlock(texto="C", intencion="I", camara="C")

    # User 1 creates 3 episodes out of order
    for idx in [3, 1, 2]:
        series = SeriesMetadata(
            series_id="saga_alpha",
            series_title="Saga Alpha",
            episode_index=idx,
            total_episodes=3,
        )
        draft = ScriptDraft(
            titulo=f"Episodio {idx}",
            hook=hook,
            desarrollo=desarrollo,
            cierre=cierre,
            series=series,
        )
        repo.save_piece("user_1", draft)

    # User 2 creates a piece with the SAME series_id to test isolation
    series_user2 = SeriesMetadata(
        series_id="saga_alpha",
        series_title="Saga de Otro",
        episode_index=1,
        total_episodes=1,
    )
    draft_u2 = ScriptDraft(
        titulo="Episodio de User 2",
        hook=hook,
        desarrollo=desarrollo,
        cierre=cierre,
        series=series_user2,
    )
    repo.save_piece("user_2", draft_u2)

    # User 1 queries saga_alpha: must get 3 episodes in order 1, 2, 3
    user1_series = repo.get_series_pieces("user_1", "saga_alpha")
    assert len(user1_series) == 3
    indices = [p["idea_fields"]["series"]["episode_index"] for p in user1_series]
    assert indices == [1, 2, 3]
    for p in user1_series:
        assert p["user_id"] == "user_1"

    # User 2 queries saga_alpha: must get only 1 episode
    user2_series = repo.get_series_pieces("user_2", "saga_alpha")
    assert len(user2_series) == 1
    assert user2_series[0]["user_id"] == "user_2"
    assert user2_series[0]["title"] == "Episodio de User 2"

    # User 3 queries saga_alpha: must get empty list
    user3_series = repo.get_series_pieces("user_3", "saga_alpha")
    assert user3_series == []


def test_get_pillar_pieces_and_isolation(repo):
    """Verify get_pillar_pieces filters by strategy_tag strictly scoped to user_id."""
    hook = ScriptBlock(texto="H", intencion="I", camara="C")
    desarrollo = ScriptBlock(texto="D", intencion="I", camara="C")
    cierre = ScriptBlock(texto="C", intencion="I", camara="C")

    # User A creates pieces in different pillars
    repo.save_piece("user_A", ScriptDraft(titulo="V1", hook=hook, desarrollo=desarrollo, cierre=cierre, pilar="Mentalidad"))
    repo.save_piece("user_A", ScriptDraft(titulo="V2", hook=hook, desarrollo=desarrollo, cierre=cierre, pilar="Mentalidad"))
    repo.save_piece("user_A", ScriptDraft(titulo="V3", hook=hook, desarrollo=desarrollo, cierre=cierre, pilar="Ventas"))

    # User B creates a piece in "Mentalidad"
    repo.save_piece("user_B", ScriptDraft(titulo="VB1", hook=hook, desarrollo=desarrollo, cierre=cierre, pilar="Mentalidad"))

    # User A gets 2 pieces for "Mentalidad"
    user_a_mentalidad = repo.get_pillar_pieces("user_A", "Mentalidad")
    assert len(user_a_mentalidad) == 2
    for p in user_a_mentalidad:
        assert p["user_id"] == "user_A"
        assert p["strategy_tag"] == "Mentalidad"

    # User A gets 1 piece for "Ventas"
    user_a_ventas = repo.get_pillar_pieces("user_A", "Ventas")
    assert len(user_a_ventas) == 1

    # User B gets 1 piece for "Mentalidad"
    user_b_mentalidad = repo.get_pillar_pieces("user_B", "Mentalidad")
    assert len(user_b_mentalidad) == 1
    assert user_b_mentalidad[0]["user_id"] == "user_B"

    # User B has 0 pieces in "Ventas"
    assert repo.get_pillar_pieces("user_B", "Ventas") == []
