"""Tests for the proactive worker service."""
import pytest
from unittest.mock import patch, MagicMock
from src.services.proactive_worker import run_proactive_cycle_for_tenant
from src.graph.state import CreatorProfile, WinningPattern


def test_proactive_worker_executes_spark_cycle():
    profile = CreatorProfile(
        user_id="user_tenant_01",
        instagram_handle="miguel_dev",
        nicho="Ingeniería de Software",
    )

    pattern = WinningPattern(
        pattern_id="p_win",
        tipo_hook="revelacion_contraria",
        formato="Reel",
        emocion="intriga",
        rendimiento_relativo_promedio=2.4,
        piezas_respaldo=3,
        ejemplos=["La verdad que nadie cuenta..."],
    )

    context = {
        "hours_since_last_ping": 30.0,
        "current_local_hour": 11,
        "silence_streak": 0,
        "confidence": 0.92,
        "winning_pattern": pattern,
        "source_referent": "@casidonovan",
        "thesis": "Los agentes determinísticos superan al caos",
    }

    result = run_proactive_cycle_for_tenant(
        user_id="user_tenant_01",
        trigger_type="market_spark",
        creator_profile=profile,
        proactive_context=context,
    )

    assert result["dispatched"] is True
    assert result["governor_allowed"] is True
    assert "@casidonovan" in result["message"]
    assert "2.4x" in result["message"]


def test_proactive_worker_suppresses_when_under_cooldown():
    profile = CreatorProfile(
        user_id="user_tenant_02",
        instagram_handle="miguel_dev",
    )

    context = {
        "hours_since_last_ping": 8.0,  # Under 24h cooldown
        "current_local_hour": 14,
        "silence_streak": 0,
        "confidence": 0.95,
    }

    result = run_proactive_cycle_for_tenant(
        user_id="user_tenant_02",
        trigger_type="brand_health_audit",
        creator_profile=profile,
        proactive_context=context,
    )

    assert result["dispatched"] is False
    assert result["governor_allowed"] is False
    assert "cooldown activo" in result["reason"].lower()
