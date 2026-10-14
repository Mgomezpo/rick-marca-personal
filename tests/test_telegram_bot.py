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
