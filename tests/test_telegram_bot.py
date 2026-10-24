"""Tests for the unified RICK Multitenant Telegram Bot service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.telegram_bot import (
    markdown_to_telegram_html,
    chunk_message,
    RickTelegramBot,
)
from src.db.repository import SupabaseRepository


def test_markdown_to_telegram_html_formatting():
    """Validates markdown transformations to clean, safe Telegram HTML."""
    raw = (
        "# Título Principal\n\n"
        "Este es un texto con **negrita** y `código`.\n"
        "- Punto uno\n"
        "- Punto dos\n"
        "---\n"
        "Texto con <caracteres> & entidades peligrosas."
    )
    html = markdown_to_telegram_html(raw)

    assert "<b>Título Principal</b>" in html
    assert "<b>negrita</b>" in html
    assert "<code>código</code>" in html
    assert "• Punto uno" in html
    assert "&lt;caracteres&gt;" in html
    assert "&amp;" in html
    assert "---" not in html


def test_chunk_message_short_text():
    """Short text should remain a single chunk."""
    text = "Mensaje corto de prueba."
    chunks = chunk_message(text, max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_message_long_text_splits_cleanly():
    """Long paragraphs should be split across multiple chunks without exceeding max_chars."""
    para1 = "A" * 80
    para2 = "B" * 80
    long_text = f"{para1}\n\n{para2}"
    chunks = chunk_message(long_text, max_chars=100)

    assert len(chunks) == 2
    assert chunks[0] == para1
    assert chunks[1] == para2


@pytest.mark.asyncio
async def test_telegram_bot_reset_handler():
    """Validates /reset command cleans memory and replies with confirmation."""
    repo = SupabaseRepository()
    repo.save_message("tg_user_1", MagicMock(role="user", content="Hola", timestamp=""))
    assert len(repo.get_conversation("tg_user_1")) == 1

    bot = RickTelegramBot(token="12345:dummy_token", repo=repo)

    update = MagicMock()
    update.effective_user.id = "tg_user_1"
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    await bot.reset_handler(update, context)

    # Conversation should be reset
    assert len(repo.get_conversation("tg_user_1")) == 0
    # Confirmation message sent
    update.message.reply_text.assert_called_once()
    sent_text = update.message.reply_text.call_args[0][0]
    assert "Estudio reiniciado desde cero" in sent_text
    assert "/start" in sent_text


@pytest.mark.asyncio
async def test_telegram_bot_start_handler_triggers_onboarding():
    """Validates /start triggers process_user_turn and returns assistant response."""
    repo = SupabaseRepository()
    bot = RickTelegramBot(token="12345:dummy_token", repo=repo)

    update = MagicMock()
    update.effective_user.id = "tg_user_new"
    update.effective_user.username = "test_creator"
    update.effective_chat.id = 999
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()

    with patch("src.services.telegram_bot.process_user_turn") as mock_turn:
        mock_turn.return_value = "¡Ey! Soy RICK, el nuevo asistente de tu marca personal. Tu prueba corre por mi cuenta."

        await bot.start_handler(update, context)

        mock_turn.assert_called_once()
        args, kwargs = mock_turn.call_args
        assert args[0] == "tg_user_new"
        assert args[1] == "test_creator"
        assert args[2] == "/start"
        assert args[3] == "telegram"

        update.message.reply_text.assert_called_once()
        sent = update.message.reply_text.call_args[0][0]
        assert "Soy RICK, el nuevo asistente de tu marca personal" in sent
