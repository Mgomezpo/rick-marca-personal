"""Tests for Supabase multitenant repository and FastAPI WhatsApp webhook (Task 10)."""
import time
import pytest
from fastapi.testclient import TestClient

from src.graph.state import (
    CreatorProfile,
    LearningItem,
    ScriptDraft,
    ScriptBlock,
)
from src.db.repository import SupabaseRepository
from src.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "database" in data


def test_whatsapp_webhook_get_challenge_verification(client):
    # Valid challenge verification
    response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "rick_secret_verify_token_2026",
            "hub.challenge": "1158201234",
        },
    )
    assert response.status_code == 200
    assert response.text == "1158201234"

    # Invalid token -> 403 Forbidden
    bad_response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "1158201234",
        },
    )
    assert bad_response.status_code == 403


def test_whatsapp_webhook_post_ack_latency_under_200ms(client):
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "100200300"},
                            "contacts": [{"wa_id": "54911223344", "profile": {"name": "Miguel"}}],
                            "messages": [
                                {
                                    "from": "54911223344",
                                    "id": "wamid.123456789",
                                    "timestamp": "1730000000",
                                    "type": "text",
                                    "text": {"body": "Hola RICK, armemos el guion sobre el error de la agencia."},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    start = time.perf_counter()
    response = client.post("/webhook/whatsapp", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    assert response.json()["status"] == "received"
    # Strict latency assertion: must return ACK under 200ms!
    assert elapsed_ms < 200, f"Webhook ACK took {elapsed_ms:.1f}ms, exceeding 200ms SLA"


def test_supabase_multitenant_isolation():
    repo = SupabaseRepository()

    # User A data
    profile_a = CreatorProfile(
        user_id="user_A",
        instagram_handle="creator_a",
        nicho="Finanzas",
        mediana_views=25000.0,
    )
    repo.upsert_creator_profile(profile_a)

    learning_a = LearningItem(
        user_id="user_A",
        statement="Las anécdotas de pérdidas financieras generan 3.1x retención.",
        applies_when="Guiones semanales",
    )
    repo.save_learning(learning_a)

    # User B data
    profile_b = CreatorProfile(
        user_id="user_B",
        instagram_handle="creator_b",
        nicho="Fitness",
        mediana_views=8000.0,
    )
    repo.upsert_creator_profile(profile_b)

    # Check isolation: User B must NEVER see User A's learnings or profile
    learnings_b = repo.get_learnings(user_id="user_B")
    assert len(learnings_b) == 0

    learnings_a = repo.get_learnings(user_id="user_A")
    assert len(learnings_a) == 1
    assert learnings_a[0].statement == learning_a.statement

    retrieved_b = repo.get_creator_profile(user_id="user_B")
    assert retrieved_b.instagram_handle == "creator_b"
    assert retrieved_b.user_id == "user_B"
