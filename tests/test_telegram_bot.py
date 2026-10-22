import pytest
from src.services.telegram_bot import markdown_to_telegram_html, RickTelegramBot

def test_markdown_to_telegram_html_headers():
    text = "### Titulo de Estudio\nTexto normal"
    html = markdown_to_telegram_html(text)
    assert "<b>Titulo de Estudio</b>" in html
    assert "&lt;b&gt;" not in html

def test_markdown_to_telegram_html_bold_and_code():
    text = "Texto con **negrita potente** y `variable_codigo`."
    html = markdown_to_telegram_html(text)
    assert "<b>negrita potente</b>" in html
    assert "<code>variable_codigo</code>" in html

def test_markdown_to_telegram_html_raw_html_escaping():
    text = "Cuidado con <script>alert('xss')</script> y las comparaciones a < b & c > d"
    html = markdown_to_telegram_html(text)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp;" in html

def test_markdown_to_telegram_html_bullets_and_dividers():
    text = "---\n* Primer punto\n- Segundo punto\n***"
    html = markdown_to_telegram_html(text)
    assert "---" not in html
    assert "***" not in html
    assert "• Primer punto" in html
    assert "• Segundo punto" in html

def test_chunk_message_short():
    bot = RickTelegramBot.__new__(RickTelegramBot)
    chunks = bot.chunk_message("Mensaje corto", 4000)
    assert len(chunks) == 1
    assert chunks[0] == "Mensaje corto"

def test_chunk_message_empty():
    bot = RickTelegramBot.__new__(RickTelegramBot)
    chunks = bot.chunk_message("", 4000)
    assert chunks == []

def test_chunk_message_oversized_paragraph():
    bot = RickTelegramBot.__new__(RickTelegramBot)
    # Párrafo individual de 6000 caracteres
    long_paragraph = ("Este es un párrafo muy largo que simula un guion extenso. " * 100).strip()
    assert len(long_paragraph) > 5000

    chunks = bot.chunk_message(long_paragraph, max_chars=1000)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 1000
    assert "guion extenso" in "".join(chunks)

def test_chunk_message_multiple_paragraphs():
    bot = RickTelegramBot.__new__(RickTelegramBot)
    p1 = "Párrafo 1 con contenido normal."
    p2 = "Párrafo 2 con contenido normal."
    text = f"{p1}\n\n{p2}"
    chunks = bot.chunk_message(text, max_chars=4000)
    assert len(chunks) == 1
    assert p1 in chunks[0]
    assert p2 in chunks[0]

@pytest.mark.asyncio
async def test_voice_handler_empty_audio_notifies_user():
    bot = RickTelegramBot.__new__(RickTelegramBot)
    bot.oa_client = None
    bot.gemini_client = None
    bot.db = None

    class MockVoice:
        file_id = "test_file_id"
        duration = 10
        mime_type = "audio/ogg"

    class MockMessage:
        voice = MockVoice()
        audio = None
        reply_texts = []
        async def reply_text(self, text, **kwargs):
            self.reply_texts.append(text)

    class MockChat:
        id = 12345

    class MockUser:
        id = 999
        username = "testcreator"
        first_name = "Creator"

    class MockFile:
        async def download_as_bytearray(self):
            return bytearray(b"dummy_silent_audio")

    class MockBot:
        async def send_chat_action(self, **kwargs):
            pass
        async def get_file(self, file_id):
            return MockFile()

    class MockContext:
        bot = MockBot()

    class MockUpdate:
        effective_user = MockUser()
        effective_chat = MockChat()
        message = MockMessage()

    update = MockUpdate()
    context = MockContext()

    await bot.voice_handler(update, context)
    assert len(update.message.reply_texts) == 1
    assert "No alcancé a captar audio" in update.message.reply_texts[0]

@pytest.mark.asyncio
async def test_voice_handler_exception_graceful_recovery():
    bot = RickTelegramBot.__new__(RickTelegramBot)

    class MockVoice:
        file_id = "broken_file"
        duration = 5
        mime_type = "audio/ogg"

    class MockMessage:
        voice = MockVoice()
        audio = None
        reply_texts = []
        async def reply_text(self, text, **kwargs):
            self.reply_texts.append(text)

    class MockUpdate:
        effective_user = type("User", (), {"id": 1, "username": "u", "first_name": "f"})()
        effective_chat = type("Chat", (), {"id": 10})()
        message = MockMessage()

    class BrokenBot:
        async def send_chat_action(self, **kwargs):
            pass
        async def get_file(self, file_id):
            raise RuntimeError("Telegram network drop")

    class MockContext:
        bot = BrokenBot()

    update = MockUpdate()
    context = MockContext()

    await bot.voice_handler(update, context)
    assert len(update.message.reply_texts) == 1
    assert "interferencia técnica" in update.message.reply_texts[0]

