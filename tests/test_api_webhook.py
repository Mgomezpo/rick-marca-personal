"""Tests for Supabase multitenant repository and FastAPI WhatsApp webhook (Task 10)."""
import time
import pytest
from fastapi.testclient import TestClient

from src.graph.state import (
    CreatorProfile,
    LearningItem,
    ScriptDraft,
    ScriptBlock,
    ConversationMessage,
)
from src.db.repository import SupabaseRepository
from src.api.app import app, repo
from src.api.webhook import send_whatsapp_message


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


def test_supabase_conversation_persistence_and_isolation():
    repo = SupabaseRepository()

    # User 1 sends a message
    msg1 = ConversationMessage(role="user", content="Hola RICK")
    repo.save_message("user_101", msg1)

    # User 2 sends a message
    msg2 = ConversationMessage(role="user", content="Qué tal")
    repo.save_message("user_102", msg2)

    conv_1 = repo.get_conversation("user_101")
    conv_2 = repo.get_conversation("user_102")

    assert len(conv_1) == 1
    assert conv_1[0].content == "Hola RICK"

    assert len(conv_2) == 1
    assert conv_2[0].content == "Qué tal"

    # Save assistant reply for user 1
    reply1 = ConversationMessage(role="assistant", content="Buen día.")
    repo.save_message("user_101", reply1)

    conv_1_updated = repo.get_conversation("user_101")
    assert len(conv_1_updated) == 2
    assert conv_1_updated[1].role == "assistant"

    # User 2 conversation remains strictly 1 message
    assert len(repo.get_conversation("user_102")) == 1


def test_outbound_whatsapp_message_dispatcher(monkeypatch):
    # Test dispatch when credentials are set
    posted_data = {}

    class MockResponse:
        status_code = 200
        def json(self):
            return {"messages": [{"id": "wamid.mock123"}]}

    def mock_post(url, headers=None, json=None, timeout=None):
        posted_data["url"] = url
        posted_data["headers"] = headers
        posted_data["json"] = json
        return MockResponse()

    import httpx
    monkeypatch.setattr(httpx, "post", mock_post)

    success = send_whatsapp_message(
        to_phone="54911223344",
        text="Mira, aquí tienes el guion listo.",
        phone_number_id="100200300",
        token="test_token_xyz",
    )

    assert success is True
    assert "100200300/messages" in posted_data["url"]
    assert posted_data["headers"]["Authorization"] == "Bearer test_token_xyz"
    assert posted_data["json"]["to"] == "54911223344"
    assert posted_data["json"]["text"]["body"] == "Mira, aquí tienes el guion listo."


def test_webhook_multi_turn_session_flow(client, monkeypatch):
    """Verify that multiple consecutive webhooks for the same phone maintain conversation context."""
    dispatched = []

    def mock_send(to_phone, text, phone_number_id=None, token=None):
        dispatched.append({"to": to_phone, "text": text})
        return True

    from src.api import webhook
    monkeypatch.setattr(webhook, "send_whatsapp_message", mock_send)

    phone = "54911998877"

    def make_webhook_payload(body):
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WABA_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "100200300"},
                                "contacts": [{"wa_id": phone, "profile": {"name": "Miguel"}}],
                                "messages": [
                                    {
                                        "from": phone,
                                        "id": f"wamid.{time.time()}",
                                        "type": "text",
                                        "text": {"body": body},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

    # Turn 1: Greeting
    res1 = client.post("/webhook/whatsapp", json=make_webhook_payload("Hola RICK"))
    assert res1.status_code == 200

    # Turn 2: Vague anecdote
    res2 = client.post(
        "/webhook/whatsapp",
        json=make_webhook_payload("Ayer tuve un problema grave con un cliente que canceló."),
    )
    assert res2.status_code == 200

    # Turn 3: Scene details
    res3 = client.post(
        "/webhook/whatsapp",
        json=make_webhook_payload("En la reunión me reclamó por las 4 horas de retraso y me desesperé."),
    )
    assert res3.status_code == 200

    # Verify conversation history was persisted for this user
    user_id = f"wa_{phone}"
    stored_msgs = webhook.repo.get_conversation(user_id)
    assert len(stored_msgs) >= 3
    # Check that messages include both user and assistant roles
    roles = [m.role for m in stored_msgs]
    assert "user" in roles
    assert "assistant" in roles


def test_api_proactive_tick_endpoint(client):
    payload = {
        "user_id": "test_creator_api",
        "trigger_type": "market_spark",
        "phone_number": "+573001112233",
        "proactive_context": {
            "hours_since_last_ping": 35.0,
            "current_local_hour": 14,
            "silence_streak": 0,
            "confidence": 0.94,
            "source_referent": "@casidonovan",
            "thesis": "Arquitectura determinística sobre prompts caóticos",
        },
    }

    response = client.post("/api/proactive/tick", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["dispatched"] is True
    assert data["governor_allowed"] is True
    assert data["message"] is not None
    assert "@casidonovan" in data["message"]

    # Verify multi-turn retention in repository
    history = repo.get_conversation("test_creator_api")
    assert len(history) > 0
    assert history[-1].role == "assistant"
    assert "@casidonovan" in history[-1].content


def test_whatsapp_webhook_audio_voice_note_processing(client):
    from src.api import webhook
    phone = "573119998877"
    audio_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "12345", "phone_number_id": "12345"},
                            "contacts": [{"profile": {"name": "Test Audio Creator"}, "wa_id": phone}],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": "wamid.AUDIO_MSG_123",
                                    "timestamp": "1771234567",
                                    "type": "audio",
                                    "audio": {
                                        "id": "media_audio_id_999",
                                        "mime_type": "audio/ogg; codecs=opus",
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    res = client.post("/webhook/whatsapp", json=audio_payload)
    assert res.status_code == 200

    user_id = f"wa_{phone}"
    stored_msgs = webhook.repo.get_conversation(user_id)
    assert len(stored_msgs) >= 1
    assert "user" in [m.role for m in stored_msgs]
    user_msg_content = [m.content for m in stored_msgs if m.role == "user"][0]
    assert len(user_msg_content) > 10


