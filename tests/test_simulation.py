import pytest
from fastapi.testclient import TestClient
from main import app
from src.core.config import config

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["engine"] == "RICK 2.0 Multitenant"
    assert data["supabase_connected"] is True

def test_meta_webhook_verification_success(client):
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "987654321",
            "hub.verify_token": config.WHATSAPP_VERIFY_TOKEN
        }
    )
    assert response.status_code == 200
    assert response.text == "987654321"

def test_meta_webhook_verification_invalid_token(client):
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "987654321",
            "hub.verify_token": "wrong_token_here"
        }
    )
    assert response.status_code == 403

def test_chat_simulation_new_user_interview(client):
    import random
    test_phone = f"+57399{random.randint(1000000, 9999999)}"
    
    # Turno 1: Saludo inicial -> Rick recibe en el estudio y hace una sola pregunta viva
    resp = client.post("/api/chat-simulation", json={
        "phone_number": test_phone,
        "message": "Hola Rick, quiero empezar a crear contenido auténtico.",
        "display_name": "Tester Creativo"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data
    assert len(data["user_id"]) > 10
    assert len(data["reply"]) > 20
    # No debe tener encabezados markdown pesados ### ni separadores ---
    assert "###" not in data["reply"]
    assert "---" not in data["reply"]

    # Turno 2: Creador responde con su obsesión real
    resp2 = client.post("/api/chat-simulation", json={
        "phone_number": test_phone,
        "message": "Me obsesiona la automatización práctica y desmantelar el humo de que la IA te hace millonario sin trabajar."
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["reply"]) > 20
    assert "###" not in data2["reply"]

    # Turno 3: Creador trae una idea concreta de trinchera
    resp3 = client.post("/api/chat-simulation", json={
        "phone_number": test_phone,
        "message": "Tengo esta anécdota: un cliente gastó $5,000 en 10 suscripciones de IA que nadie usa, cuando un solo script en Python le resolvió la operación en 2 horas."
    })
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert len(data3["reply"]) > 30
