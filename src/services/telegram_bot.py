"""Production-grade Telegram Bot Service unified with RICK Multitenant Engine."""
import os
import io
import re
import logging
import asyncio
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.db.repository import SupabaseRepository
from src.services.session_runner import process_user_turn
from src.services.voice import voice_service

logger = logging.getLogger("rick.services.telegram")


def markdown_to_telegram_html(text: str) -> str:
    """
    Transforms markdown into Telegram-safe HTML without breaking tags.
    - Preserves bold, code, bullet points.
    - Escapes raw XML characters before replacing formatting.
    """
    if not text:
        return ""

    # 1. Clean divider lines
    cleaned = re.sub(r'^[-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 2. Convert bullet points
    cleaned = re.sub(r'^\s*[\*\-]\s+', '• ', cleaned, flags=re.MULTILINE)

    # 3. Escape XML entities safely
    cleaned = cleaned.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # 4. Headers: convert markdown headers to bold
    cleaned = re.sub(r'^(#{1,6})\s+(.+)$', r'<b>\2</b>\n', cleaned, flags=re.MULTILINE)

    # 5. Bold: **text** -> <b>text</b>
    cleaned = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', cleaned)

    # 6. Inline code: `text` -> <code>text</code>
    cleaned = re.sub(r'`([^`]+)`', r'<code>\1</code>', cleaned)

    # 7. Normalize multiple newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned


def chunk_message(text: str, max_chars: int = 4000) -> List[str]:
    """Split message into Telegram-compliant chunks under 4096 characters."""
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for p in paragraphs:
        while len(p) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            split_idx = p.rfind("\n", 0, max_chars)
            if split_idx == -1 or split_idx < max_chars // 2:
                split_idx = p.rfind(" ", 0, max_chars)
            if split_idx == -1:
                split_idx = max_chars
            chunks.append(p[:split_idx].strip())
            p = p[split_idx:].strip()

        if not p:
            continue

        if len(current) + len(p) + 2 <= max_chars:
            current += (("\n\n" if current else "") + p)
        else:
            if current:
                chunks.append(current)
            current = p

    if current:
        chunks.append(current)

    return chunks


class RickTelegramBot:
    """
    Unified Telegram Bot worker running against the canonical RICK Multitenant Engine.
    Channel: telegram
    Shared backend: SupabaseRepository + RickGraphEngine (process_user_turn).
    """

    def __init__(
        self,
        token: Optional[str] = None,
        repo: Optional[SupabaseRepository] = None,
    ):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.repo = repo or SupabaseRepository()
        self.app: Optional[Application] = None

    async def send_clean_message(self, update: Update, text: str):
        """Sends formatted message with fallback to plain text if HTML parsing fails."""
        if not update.message or not text:
            return

        html_formatted = markdown_to_telegram_html(text)
        chunks = chunk_message(html_formatted)

        for chunk in chunks:
            try:
                await update.message.reply_text(chunk, parse_mode=constants.ParseMode.HTML)
            except Exception as e:
                logger.warning(f"HTML parsing failed ({e}), falling back to plain text.")
                clean_plain = re.sub(r'</?[^>]+>', '', chunk)
                clean_plain = re.sub(r'[\*#_`]', '', clean_plain)
                await update.message.reply_text(clean_plain)

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command: triggers clean onboarding with RICK's canonical welcome."""
        user = update.effective_user
        if not user or not update.message:
            return

        user_id = str(user.id)
        handle = user.username or user.first_name or f"creador_{user_id[-4:]}"

        logger.info(f"🚀 Telegram /start received from {user_id} (@{handle})")

        if update.effective_chat:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=constants.ChatAction.TYPING
            )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            process_user_turn,
            user_id,
            handle,
            "/start",
            "telegram",
            None,
            self.repo,
            None,
        )

        await self.send_clean_message(update, response)

    async def reset_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /reset command: completely resets user state and profile."""
        user = update.effective_user
        if not user or not update.message:
            return

        user_id = str(user.id)
        logger.info(f"🔄 Telegram /reset received from {user_id}")

        self.repo.reset_user(user_id)

        reply = (
            "🔄 **Estudio reiniciado desde cero.**\n\n"
            "Se ha limpiado tu perfil y memoria activa en la base de datos. "
            "Escribe `/start` para arrancar el onboarding limpio como nuevo creador."
        )
        await self.send_clean_message(update, reply)

    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for freeform text messages: routes through RICK multitenant engine."""
        user = update.effective_user
        msg = update.message
        if not user or not msg or not msg.text:
            return

        user_id = str(user.id)
        handle = user.username or user.first_name or f"creador_{user_id[-4:]}"
        user_text = msg.text.strip()

        logger.info(f"📩 Telegram text from {user_id} (@{handle}): '{user_text[:50]}...'")

        if update.effective_chat:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=constants.ChatAction.TYPING
            )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            process_user_turn,
            user_id,
            handle,
            user_text,
            "telegram",
            None,
            self.repo,
            None,
        )

        await self.send_clean_message(update, response)

    async def voice_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for Telegram voice notes and audio: transcribes audio and routes to RICK."""
        user = update.effective_user
        msg = update.message
        if not user or not msg:
            return

        voice = msg.voice or msg.audio
        if not voice:
            return

        user_id = str(user.id)
        handle = user.username or user.first_name or f"creador_{user_id[-4:]}"

        if update.effective_chat:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=constants.ChatAction.RECORD_VOICE
            )

        try:
            tg_file = await voice.get_file()
            audio_bytes = bytes(await tg_file.download_as_bytearray())

            logger.info(f"🎙️ Downloaded voice note from {user_id} ({len(audio_bytes)} bytes). Transcribing...")

            transcription = voice_service.transcribe_audio(
                audio_bytes=audio_bytes,
                mime_type="audio/ogg",
                filename="voice.ogg",
            )

            if not transcription:
                await msg.reply_text("Disculpa, no pude escuchar con claridad el audio. ¿Me lo envías de nuevo o me cuentas por texto?")
                return

            logger.info(f"📝 Transcription for {user_id}: '{transcription[:60]}...'")

            if update.effective_chat:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action=constants.ChatAction.TYPING
                )

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                process_user_turn,
                user_id,
                handle,
                transcription,
                "telegram",
                None,
                self.repo,
                None,
            )

            await self.send_clean_message(update, response)

        except Exception as e:
            logger.error(f"Error handling Telegram voice note for {user_id}: {e}", exc_info=True)
            await msg.reply_text("Hubo un error procesando tu nota de voz. Por favor intenta de nuevo.")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler for Telegram polling."""
        logger.error(f"Telegram polling error: {context.error}")

    def build_application(self) -> Application:
        """Constructs Application with configured command and message handlers."""
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured.")

        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start_handler))
        app.add_handler(CommandHandler("reset", self.reset_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self.voice_handler))
        app.add_error_handler(self.error_handler)
        self.app = app
        return app

    def run(self):
        """Runs the bot in Long Polling mode (drop_pending_updates=True)."""
        app = self.build_application()
        print("=======================================================")
        print("  🤖 Iniciando RICK Multitenant en Telegram (Long Polling)")
        print("=======================================================")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    bot = RickTelegramBot()
    bot.run()
