"""Adversarial Isolation and Anti-Hardcoding Audit Suite.

Verifies:
1. Strict Multitenant Isolation: New tenants never see founder receipts, fake metrics or lore.
2. Honest Empty State: Empty radars receive honest data requests, not fabricated posts or numbers.
3. Zero Founder Lore Leakage in Fallbacks: Mock completion and prompt routes are voice-aligned but lore-agnostic.
4. Production Integrity: External unconfigured services (Apify, WhatsApp Voice) return None/[] instead of simulating success.
5. Empirical Integrity: Fallback scripts do not fake empirical backing (piezas_respaldo == 0).
"""
import os
import pytest
from src.graph.state import (
    create_initial_state,
    ConversationMessage,
    CreatorProfile,
    StoryReceipt,
    WinningPattern,
)
from src.graph.engine import RickGraphEngine
from src.agents.rick import rick_strategist_node
from src.agents.routine import routine_reporter_node
from src.agents.guionista import guionista_node
from src.agents.evaluator import evaluator_node
from src.graph.formatter import format_script_whatsapp
from src.services.llm import llm_service
from src.services.instagram_scraper import InstagramScraperService
from src.services.voice import VoiceTranscriptionService
from src.db.repository import SupabaseRepository


def test_multitenant_new_user_gets_honest_report_prompt_without_fixture_leak(monkeypatch):
    """
    Verify that in non-test or new-user contexts, asking for a report with no ingested posts
    returns an honest message and does NOT leak fake posts, 32000 views, or 2.67x multipliers.
    """
    # Simulate a new production user
    state = create_initial_state("user_fresh_tenant_2026", "maria_growth")
    state["messages"].append(
        ConversationMessage(role="user", content="Muéstrame el reporte semanal de mi cuenta.")
    )

    result = routine_reporter_node(state)
    response = result["final_response"]

    assert response is not None
    assert "maria_growth" in response
    assert "Aún no tenemos suficientes reels registrados en tu radar" in response
    assert "32000" not in response
    assert "2.67" not in response
    assert "dos mil dólares" not in response
    assert len(result["learnings"]) == 0


def test_multitenant_new_user_blocked_creator_receives_honest_heavy_lifting_without_lore_leak():
    """
    Verify that a new tenant with an empty story bank who has writer's block receives
    two concrete niche/dogma angles for heavy lifting, with zero leakage of founder receipts.
    """
    state = create_initial_state("tenant_lawyer_01", "sofia_abogada")
    state["creator_profile"] = CreatorProfile(
        user_id="tenant_lawyer_01",
        instagram_handle="sofia_abogada",
        nicho="Legal y Corporativo",
    )
    state["messages"].append(
        ConversationMessage(role="user", content="Tengo la mente en blanco, no sé qué decir.")
    )

    result = rick_strategist_node(state)
    response = result["final_response"]

    assert response is not None
    assert "1." in response and "2." in response
    res_lower = response.lower()
    # Ensure zero founder lore leak
    assert "excel" not in res_lower
    assert "dental" not in res_lower
    assert "papá" not in res_lower
    assert "papa" not in res_lower
    assert "ayudasismo" not in res_lower
    assert "handoff" not in res_lower
    assert "bancolombia" not in res_lower


def test_llm_mock_completion_contains_zero_founder_lore():
    """
    Verify that the deterministic offline fallback completion does not leak
    founder private life events into any tenant message.
    """
    meta_response = llm_service._mock_completion("¿Por qué eres mejor que ChatGPT y Claude?")
    meta_lower = meta_response.lower()
    assert "excel" not in meta_lower
    assert "clínica" not in meta_lower
    assert "dental" not in meta_lower
    assert "ayudasismo" not in meta_lower
    assert "handoff" not in meta_lower
    assert "contexto" in meta_lower

    blocked_response = llm_service._mock_completion("Tengo la mente en blanco, estoy bloqueado.")
    blocked_lower = blocked_response.lower()
    assert "excel" not in blocked_lower
    assert "clínica" not in blocked_lower
    assert "dental" not in blocked_lower
    assert "playbooks" in blocked_lower

    script_response = llm_service._mock_completion("Escribe el guion para hoy.")
    script_lower = script_response.lower()
    assert "clínica dental" not in script_lower
    assert "excel" not in script_lower
    assert "papá" not in script_lower


def test_instagram_scraper_production_mode_does_not_simulate_mock_reels_when_unconfigured():
    """
    Verify that in production (is_test_env=False), missing Apify token returns
    empty results instead of pretending fake mock reels from Hormozi/Martell were scraped.
    """
    scraper = InstagramScraperService(token=None)
    scraper.is_test_env = False

    reels = scraper.search_niche_reels(["inteligencia", "artificial"])
    assert reels == []

    shared_row = scraper.scrape_shared_link("https://www.instagram.com/reel/C5def303/")
    assert shared_row is None


def test_voice_service_production_mode_does_not_simulate_audio_when_unconfigured():
    """
    Verify that in production (is_test_env=False), missing WhatsApp token returns
    None instead of simulating audio payload and fake transcription.
    """
    service = VoiceTranscriptionService()
    service.is_test_env = False
    service.whatsapp_token = None

    downloaded = service.download_whatsapp_media("media_id_99999")
    assert downloaded is None


def test_guionista_and_evaluator_do_not_fabricate_empirical_piezas_when_no_pattern():
    """
    Verify that when no empirical winning patterns exist, guionista_node and evaluator_node
    do not simulate backing (piezas_respaldo=0) and the formatted response states so honestly.
    """
    state = create_initial_state("usr_new_test", "creator_no_patterns")
    state["story_extracted"] = "Invertí semanas construyendo un feature que nadie me pidió."
    state["winning_patterns"] = []  # No patterns ingested

    state = guionista_node(state)
    draft = state.get("script_draft")
    assert draft is not None

    state = evaluator_node(state)
    evaluation = state.get("evaluation")
    assert evaluation is not None
    assert evaluation.piezas_respaldo == 0

    formatted = format_script_whatsapp(draft, evaluation)
    assert "Todavía no tengo videos de tus referentes que respalden este patrón" in formatted
    assert "calibré contra 5 videos" not in formatted


def test_repository_get_story_bank_isolated_in_production(monkeypatch):
    """
    Verify that in production environment, get_story_bank returns an empty bank for new users
    and does not auto-seed founder receipts even for 'miguel' or 'user_101'.
    """
    repo = SupabaseRepository()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    # In production, even legacy usernames start with empty bank unless explicitly saved in DB
    assert repo.get_story_bank("new_tenant_abc") == []
    assert repo.get_story_bank("miguel_gomezpo") == []


def test_send_whatsapp_message_in_production_unconfigured_does_not_fake_success(monkeypatch):
    """
    Verify that in production (APP_ENV=production), send_whatsapp_message returns False
    when tokens or phone IDs are placeholders or unconfigured, instead of pretending success.
    """
    from src.api.webhook import send_whatsapp_message
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_TOKEN", raising=False)

    result = send_whatsapp_message(
        to_phone="123456789",
        text="Hola",
        phone_number_id=None,
        token=None,
    )
    assert result is False


def test_repository_story_receipt_persists_to_supabase_episodic_memory(monkeypatch):
    """
    Verify that save_story_receipt persists receipts to Supabase table episodic_memory
    with kind='story_receipt' and deterministic UUIDs, and get_story_bank retrieves them.
    """
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    class MockTable:
        def __init__(self):
            self.rows = []

        def upsert(self, data, on_conflict="id"):
            self.rows = [r for r in self.rows if r.get("id") != data.get("id")]
            self.rows.append(data)
            return self

        def select(self, *args):
            return self

        def eq(self, col, val):
            return self

        def execute(self):
            class Resp:
                def __init__(self, data):
                    self.data = data
            return Resp(self.rows)

    class MockSupabase:
        def __init__(self):
            self.mock_table = MockTable()

        def table(self, name):
            assert name == "episodic_memory"
            return self.mock_table

    mock_db = MockSupabase()
    repo = SupabaseRepository(supabase_client=mock_db)

    receipt = StoryReceipt(
        id="rec_b2b_churn_01",
        summary="Perdimos 5 clientes por no tener onboarding claro",
        theme="fricción de retención en clientes nuevos",
        concrete_details=["churn 20%", "onboarding confuso"],
        punchline="El onboarding no es un tutorial, es el primer valor entregado.",
    )

    repo.save_story_receipt("user_b2b_saas", receipt)

    # Verify table received episodic_memory record
    assert len(mock_db.mock_table.rows) == 1
    saved_row = mock_db.mock_table.rows[0]
    assert saved_row["kind"] == "story_receipt"
    assert saved_row["title"] == "fricción de retención en clientes nuevos"
    assert saved_row["content"]["receipt_id"] == "rec_b2b_churn_01"

    # Invalidate in-memory cache to force DB retrieval
    repo._story_banks.clear()
    fetched = repo.get_story_bank("user_b2b_saas")
    assert len(fetched) == 1
    assert fetched[0].id == "rec_b2b_churn_01"
    assert fetched[0].theme == "fricción de retención en clientes nuevos"


