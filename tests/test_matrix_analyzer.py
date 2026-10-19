"""Tests for matrix models, winning patterns extractor, and dual market radar (Task 4)."""
import pytest
from src.matrix.models import MatrixRow
from src.matrix.analyzer import find_winning_patterns, MarketRadar


def test_matrix_row_validation_10_columns():
    row = MatrixRow(
        post_id="post_001",
        account_handle="casidonovan",
        views=45000,
        account_median=18000.0,
        relative_performance=2.5,
        hook_text="Si hoy empezara de cero, no abriría otra agencia.",
        hook_type="confesion_error",
        format="historia_personal",
        emotion="vulnerabilidad",
        duration_seconds=42,
    )
    assert row.post_id == "post_001"
    assert row.account_handle == "casidonovan"
    assert row.views == 45000
    assert row.account_median == 18000.0
    assert row.relative_performance == 2.5
    assert row.hook_type == "confesion_error"
    assert row.format == "historia_personal"
    assert row.emotion == "vulnerabilidad"
    assert row.duration_seconds == 42


def test_matrix_row_from_raw_calculates_r():
    raw_data = {
        "post_id": "raw_123",
        "account_handle": "miguel_gomezpo",
        "views": 30000,
        "hook_text": "Dejé de buscar clientes y empecé a buscar problemas reales.",
        "hook_type": "quiebre_creencia",
        "format": "leccion_de_trinchera",
        "emotion": "autoridad",
        "duration_seconds": 50,
    }
    row = MatrixRow.from_raw(raw_data, account_median=15000.0)
    assert row.relative_performance == 2.0


def test_find_winning_patterns_groups_and_averages():
    rows = [
        # Group A (Winner): confesion_error + historia_personal + vulnerabilidad
        MatrixRow(
            post_id="p1",
            account_handle="casidonovan",
            views=30000,
            account_median=15000.0,
            relative_performance=2.0,
            hook_text="Hook 1",
            hook_type="confesion_error",
            format="historia_personal",
            emotion="vulnerabilidad",
            duration_seconds=40,
        ),
        MatrixRow(
            post_id="p2",
            account_handle="casidonovan",
            views=45000,
            account_median=15000.0,
            relative_performance=3.0,
            hook_text="Hook 2",
            hook_type="confesion_error",
            format="historia_personal",
            emotion="vulnerabilidad",
            duration_seconds=45,
        ),
        # Group B (Winner, 1 piece): quiebre_creencia + leccion + autoridad
        MatrixRow(
            post_id="p3",
            account_handle="other_creator",
            views=25000,
            account_median=10000.0,
            relative_performance=2.5,
            hook_text="Hook 3",
            hook_type="quiebre_creencia",
            format="leccion",
            emotion="autoridad",
            duration_seconds=50,
        ),
        # Non-winner: R < 1.5
        MatrixRow(
            post_id="p4",
            account_handle="low_creator",
            views=8000,
            account_median=10000.0,
            relative_performance=0.8,
            hook_text="Hook 4",
            hook_type="tutorial",
            format="pantalla",
            emotion="neutral",
            duration_seconds=30,
        ),
    ]

    patterns = find_winning_patterns(rows, min_multiplier=1.5)
    assert len(patterns) == 2

    top_pattern = patterns[0]
    assert top_pattern.tipo_hook == "confesion_error"
    assert top_pattern.piezas_respaldo == 2
    assert top_pattern.rendimiento_relativo_promedio == 2.5
    assert len(top_pattern.ejemplos) == 2


def test_market_radar_dual_source_and_fallback():
    radar = MarketRadar()

    referent_rows = [
        MatrixRow(
            post_id="ref1",
            account_handle="casidonovan",
            views=60000,
            account_median=20000.0,
            relative_performance=3.0,
            hook_text="Mi mayor error de 2025",
            hook_type="confesion_error",
            format="historia_personal",
            emotion="vulnerabilidad",
            duration_seconds=45,
        )
    ]
    discovery_rows = [
        MatrixRow(
            post_id="disc1",
            account_handle="trending_niche",
            views=100000,
            account_median=25000.0,
            relative_performance=4.0,
            hook_text="Nadie te dice esto sobre retención",
            hook_type="quiebre_creencia",
            format="demostracion_mecanismo",
            emotion="curiosidad",
            duration_seconds=38,
        )
    ]

    results = radar.analyze_dual_radar(
        referents_rows=referent_rows,
        discovery_rows=discovery_rows,
    )
    assert len(results["referents_patterns"]) == 1
    assert len(results["discovery_patterns"]) == 1
    assert results["top_pattern"].rendimiento_relativo_promedio == 4.0

    # Fallback with empty rows returns cached/safe defaults without crashing
    fallback = radar.analyze_dual_radar(referents_rows=[], discovery_rows=[])
    assert len(fallback["top_patterns"]) >= 1
    assert fallback["is_fallback"] is True
