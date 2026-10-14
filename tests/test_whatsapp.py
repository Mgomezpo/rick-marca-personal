import pytest
from src.services.whatsapp import WhatsAppClient, format_whatsapp_text

def test_format_whatsapp_text_formatting():
    raw = "### Título en Markdown\nTexto con **negrita** y lista:\n- Elemento 1\n* Elemento 2\n---\n"
    formatted = format_whatsapp_text(raw)
    assert "*Título en Markdown*" in formatted
    assert "*negrita*" in formatted
    assert "• Elemento 1" in formatted
    assert "• Elemento 2" in formatted
    assert "---" not in formatted

def test_whatsapp_client_chunk_message_short():
    client = WhatsAppClient()
    text = "Hola creador, este es un mensaje corto."
    chunks = client.chunk_message(text, max_chars=1500)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_whatsapp_client_chunk_message_long():
    client = WhatsAppClient()
    paragraphs = [f"Párrafo {i}: " + ("Texto extenso de guion para probar corte limpio. " * 10) for i in range(10)]
    full_text = "\n\n".join(paragraphs)
    chunks = client.chunk_message(full_text, max_chars=500)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 500

def test_whatsapp_client_mock_send():
    client = WhatsAppClient()
    # In test environment without Meta token, it should safely log and return True
    success = client.send_text_message(to_phone="+573001234567", text="Mensaje de prueba")
    assert success is True

def test_whatsapp_client_mock_mark_as_read():
    client = WhatsAppClient()
    success = client.mark_as_read(message_id="wamid.test1234")
    assert success is True
