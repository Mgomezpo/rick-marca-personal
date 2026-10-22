import logging
import asyncio
import time
import re
from typing import Optional, List
from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from google import genai
from google.genai import types

from src.core.config import config
from src.core.observability import (
    generate_correlation_id,
    set_request_context,
    get_correlation_id,
    log_event,
)
from src.db.supabase import DatabaseService
from src.engine.orchestrator import RickOrchestrator

logger = logging.getLogger("rick.telegram")

def markdown_to_telegram_html(text: str) -> str:
    """
    Convierte texto con markdown estándar a HTML seguro para Telegram:
    - Transforma **negrita** a <b>negrita</b>
    - Elimina encabezados (###), líneas separadoras (---) y viñetas feas
    - Escapa etiquetas HTML no deseadas antes de generar el marcado
    """
    # 1. Eliminar líneas divisorias --- o ***
    cleaned = re.sub(r'^[-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # 2. Limpiar viñetas (* item -> • item)
    cleaned = re.sub(r'^\s*[\*\-]\s+', '• ', cleaned, flags=re.MULTILINE)
    
    # 3. Escapar HTML entities ANTES de insertar etiquetas HTML para evitar romper el marcado
    cleaned = cleaned.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 4. Convertir encabezados markdown (### Titulo -> <b>Titulo</b>)
    cleaned = re.sub(r'^(#{1,6})\s+(.+)$', r'<b>\2</b>\n', cleaned, flags=re.MULTILINE)
    
    # 5. Convertir **texto** a <b>texto</b>
    cleaned = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', cleaned)
    
    # 6. Convertir `código` a <code>código</code>
    cleaned = re.sub(r'`([^`]+)`', r'<code>\1</code>', cleaned)
    
    # 7. Limpiar saltos de línea triples
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

class RickTelegramBot:
    def __init__(self):
        self.db = DatabaseService()
        self.orchestrator = RickOrchestrator(self.db)
        self.token = config.TELEGRAM_BOT_TOKEN
        self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.oa_client = None
        if config.OPENAI_API_KEY:
            try:
                import openai
                self.oa_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Error inicializando cliente OpenAI en TelegramBot: {e}")
        self.app: Optional[Application] = None

    def chunk_message(self, text: str, max_chars: int = 4000) -> List[str]:
        if not text:
            return []
        if len(text) <= max_chars:
            return [text]

        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for p in paragraphs:
            # Si un párrafo individual excede max_chars, trocearlo de forma segura
            while len(p) > max_chars:
                if current:
                    chunks.append(current)
                    current = ""
                split_idx = p.rfind("\n", 0, max_chars)
                if split_idx == -1 or split_idx < max_chars // 2:
                    split_idx = p.rfind(" ", 0, max_chars)
                if split_idx == -1 or split_idx < max_chars // 2:
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

    async def send_clean_message(self, update: Update, text: str):
        """
        Envía un mensaje formateado limpiamente en Telegram.
        Si falla el HTML por caracteres inesperados, envía texto plano sin markdown.
        """
        html_formatted = markdown_to_telegram_html(text)
        chunks = self.chunk_message(html_formatted)

        for chunk in chunks:
            try:
                await update.message.reply_text(chunk, parse_mode=constants.ParseMode.HTML)
            except Exception as e:
                logger.warning(f"Aviso parseando HTML en Telegram ({e}), enviando texto plano limpio.")
                # Eliminar etiquetas HTML y símbolos residuales de markdown
                clean_plain = re.sub(r'</?[^>]+>', '', chunk)
                clean_plain = re.sub(r'[\*#_`]', '', clean_plain)
                await update.message.reply_text(clean_plain)

    async def _dispatch_orchestrator_turn(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: str,
        thread_id: str,
        user_message: str,
        typing_interval: float = 3.5,
        correlation_id: Optional[str] = None,
    ):
        """
        Ejecuta el ciclo del orquestador en segundo plano, emite la acción de escribiendo
        en Telegram y envía la respuesta formateada al usuario de forma segura.
        """
        corr_id = correlation_id or generate_correlation_id("tg")
        set_request_context(correlation_id=corr_id, entry_point="telegram", user_id=user_id)
        chat = update.effective_chat

        log_event(
            logger,
            logging.INFO,
            event="telegram_turn_dispatched",
            message=f"Despachando turno Telegram para user={user_id}",
            user_id=user_id,
            chat_id=chat.id if chat else None,
            thread_id=thread_id
        )

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(
            None,
            self.orchestrator.process_message,
            user_message,
            user_id,
            "telegram",
            thread_id,
            corr_id
        )

        while not task.done():
            if chat:
                await context.bot.send_chat_action(chat_id=chat.id, action=constants.ChatAction.TYPING)
            await asyncio.sleep(typing_interval)

        reply = await task

        if "interferencia en la mesa" not in reply:
            self.db.append_thread_message(thread_id, "assistant", reply)

        await self.send_clean_message(update, reply)

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        if not user or not chat:
            return

        corr_id = generate_correlation_id("tg_start")
        set_request_context(correlation_id=corr_id, entry_point="telegram", user_id=str(user.id))
        log_event(
            logger,
            logging.INFO,
            event="telegram_start_received",
            message=f"🚀 Telegram /start recibido de {user.id} (@{user.username})",
            user_id=str(user.id),
            username=user.username or ""
        )
        user_id, identity, is_new = self.db.get_or_create_telegram_identity(
            telegram_id=str(user.id),
            username=user.username,
            first_name=user.first_name or "Creador"
        )

        thread = self.db.get_or_create_telegram_thread(user_id)
        thread_id = thread.get("id")

        # REINICIAR el transcript del hilo para que un nuevo /start arranque una conversación limpia
        try:
            self.db.client.table("rick_threads").update({"transcript": [], "turn_count": 0}).eq("id", thread_id).execute()
        except Exception as e:
            log_event(
                logger,
                logging.WARNING,
                event="telegram_reset_transcript_failed",
                message=f"Error reseteando transcript en /start: {e}",
                error_message=str(e)
            )

        # Si el creador aún no ha completado el onboarding, reiniciar memoria activa a paso 0
        profile = self.db.get_user_profile(user_id)
        is_onboarded = (profile.get("onboarding_status") == "completed") if profile else False
        if not is_onboarded:
            self.db.init_active_memory(user_id)

        # Procesar bienvenida de forma dinámica y viva a través del orquestador de RICK
        await self._dispatch_orchestrator_turn(
            update=update,
            context=context,
            user_id=user_id,
            thread_id=thread_id,
            user_message="/start",
            typing_interval=2.0,
            correlation_id=corr_id
        )

    async def reset_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Limpia el estado y perfil para probar el onboarding de cero."""
        user = update.effective_user
        if not user:
            return
        corr_id = generate_correlation_id("tg_reset")
        set_request_context(correlation_id=corr_id, entry_point="telegram", user_id=str(user.id))
        log_event(
            logger,
            logging.INFO,
            event="telegram_reset_received",
            message=f"🔄 Telegram /reset recibido de {user.id} (@{user.username})",
            user_id=str(user.id)
        )
        user_id, identity, _ = self.db.get_or_create_telegram_identity(
            telegram_id=str(user.id),
            username=user.username,
            first_name=user.first_name or "Creador"
        )
        thread = self.db.get_or_create_telegram_thread(user_id)
        thread_id = thread.get("id")

        try:
            self.db.client.table("rick_threads").update({"transcript": [], "turn_count": 0}).eq("id", thread_id).execute()
            self.db.client.table("brand_assets").delete().eq("user_id", user_id).execute()
            self.db.client.table("user_profiles").delete().eq("user_id", user_id).execute()
            self.db.init_active_memory(user_id)
        except Exception as e:
            log_event(
                logger,
                logging.ERROR,
                event="telegram_reset_db_error",
                message=f"Error reiniciando estudio: {e}",
                error_message=str(e)
            )

        reply = (
            "🔄 **Estudio reiniciado desde cero.**\n\n"
            "Se ha limpiado tu perfil y memoria activa en la base de datos. "
            "Escribe `/start` para arrancar el onboarding limpio como nuevo creador."
        )
        await self.send_clean_message(update, reply)

    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        if not user or not chat or not message or not message.text:
            return

        text = message.text.strip()
        corr_id = generate_correlation_id("tg_msg")
        set_request_context(correlation_id=corr_id, entry_point="telegram", user_id=str(user.id))
        log_event(
            logger,
            logging.INFO,
            event="telegram_text_received",
            message=f"📩 Telegram mensaje de {user.id} (@{user.username}): '{text[:50]}...'",
            user_id=str(user.id),
            username=user.username or "",
            text_length=len(text)
        )

        try:
            # 1. Resolver usuario multitenant
            user_id, identity, is_new = self.db.get_or_create_telegram_identity(
                telegram_id=str(user.id),
                username=user.username,
                first_name=user.first_name or "Creador"
            )

            # 2. Hilo de conversación
            thread = self.db.get_or_create_telegram_thread(user_id)
            thread_id = thread.get("id")
            self.db.append_thread_message(thread_id, "user", text)

            # 3. Procesar en el orquestador principal de RICK
            await self._dispatch_orchestrator_turn(
                update=update,
                context=context,
                user_id=user_id,
                thread_id=thread_id,
                user_message=text,
                typing_interval=3.5,
                correlation_id=corr_id
            )
        except Exception as e:
            logger.exception(f"Error procesando mensaje de texto de {user.id}: {e}")
            await update.message.reply_text(
                "Disculpa, hubo una interferencia técnica en la mesa. ¿Podrías reenviar tu mensaje?"
            )

    async def voice_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        if not user or not chat or not message:
            return

        voice = message.voice or message.audio
        if not voice:
            return

        corr_id = generate_correlation_id("tg_voice")
        set_request_context(correlation_id=corr_id, entry_point="telegram", user_id=str(user.id))
        log_event(
            logger,
            logging.INFO,
            event="telegram_voice_received",
            message=f"🎙️ Telegram nota de voz recibida de {user.id}...",
            user_id=str(user.id),
            duration_seconds=getattr(voice, "duration", 0)
        )
        await context.bot.send_chat_action(chat_id=chat.id, action=constants.ChatAction.RECORD_VOICE)

        try:
            # 1. Descargar audio
            voice_file = await context.bot.get_file(voice.file_id)
            audio_bytearray = await voice_file.download_as_bytearray()
            audio_bytes = bytes(audio_bytearray)

            # 2. Transcribir nota de voz (Whisper primario, Gemini fallback)
            transcribed_text = ""
            transcription_start = time.time()
            if self.oa_client:
                try:
                    import io
                    audio_file = io.BytesIO(audio_bytes)
                    audio_file.name = "voice.ogg"
                    transcript = self.oa_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="es"
                    )
                    transcribed_text = (transcript.text or "").strip()
                    trans_dur = int((time.time() - transcription_start) * 1000)
                    log_event(
                        logger,
                        logging.INFO,
                        event="telegram_voice_transcribed",
                        message=f"📝 Transcripción Whisper ({trans_dur}ms): '{transcribed_text[:60]}...'",
                        engine="whisper-1",
                        duration_ms=trans_dur,
                        char_count=len(transcribed_text)
                    )
                except Exception as whisper_err:
                    log_event(
                        logger,
                        logging.WARNING,
                        event="telegram_whisper_fallback",
                        message=f"Aviso Whisper ({whisper_err}). Probando Gemini...",
                        error_message=str(whisper_err)
                    )

            if not transcribed_text and config.GEMINI_API_KEY:
                try:
                    mime = getattr(voice, "mime_type", None) or "audio/ogg"
                    resp = self.gemini_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                            "Transcribe con total exactitud esta nota de voz en español. Devuelve ÚNICAMENTE el texto transcrito."
                        ]
                    )
                    transcribed_text = (resp.text or "").strip()
                    trans_dur = int((time.time() - transcription_start) * 1000)
                    log_event(
                        logger,
                        logging.INFO,
                        event="telegram_voice_transcribed",
                        message=f"📝 Transcripción Gemini ({trans_dur}ms): '{transcribed_text[:60]}...'",
                        engine="gemini-2.5-flash",
                        duration_ms=trans_dur,
                        char_count=len(transcribed_text)
                    )
                except Exception as gem_err:
                    log_event(
                        logger,
                        logging.ERROR,
                        event="telegram_voice_transcription_failed",
                        message=f"Error transcribiendo audio con Gemini: {gem_err}",
                        error_message=str(gem_err)
                    )

            if not transcribed_text:
                await update.message.reply_text(
                    "🎙️ No alcancé a captar audio en esa nota de voz (parece que no tenía sonido o llegó en silencio). ¿Podrías volver a grabarla o escribírmela?"
                )
                return

            # 3. Resolver identidad y procesar con RICK
            user_id, identity, is_new = self.db.get_or_create_telegram_identity(
                telegram_id=str(user.id),
                username=user.username,
                first_name=user.first_name or "Creador"
            )
            thread = self.db.get_or_create_telegram_thread(user_id)
            thread_id = thread.get("id")
            self.db.append_thread_message(thread_id, "user", f"[Nota de voz]: {transcribed_text}")

            await self._dispatch_orchestrator_turn(
                update=update,
                context=context,
                user_id=user_id,
                thread_id=thread_id,
                user_message=transcribed_text,
                typing_interval=3.5,
                correlation_id=corr_id
            )
        except Exception as e:
            logger.exception(f"Error procesando nota de voz de {user.id}: {e}")
            await update.message.reply_text(
                "🎙️ Tuve una interferencia técnica al procesar tu nota de voz. Por favor intenta enviarla de nuevo o déjamelo por escrito."
            )

    def run_polling(self):
        if not self.token or "PLACEHOLDER" in self.token:
            print("\n❌ ERROR: Falta configurar TELEGRAM_BOT_TOKEN en el archivo .env")
            return

        print("\n=======================================================")
        print("  🤖 Iniciando RICK en Telegram (Modo Long Polling)")
        print("=======================================================")
        from telegram.request import HTTPXRequest

        async def on_telegram_error(update: object, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"⚠️ [Telegram Error] {context.error}", exc_info=context.error)
            if isinstance(update, Update) and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "Disculpa, ocurrió un error inesperado al procesar tu solicitud. Por favor intenta de nuevo en unos momentos."
                    )
                except Exception:
                    pass

        request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0)
        self.app = Application.builder().token(self.token).request(request).build()

        self.app.add_handler(CommandHandler("start", self.start_handler))
        self.app.add_handler(CommandHandler("reset", self.reset_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        self.app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self.voice_handler))
        self.app.add_error_handler(on_telegram_error)

        print("✅ RICK está escuchando mensajes en Telegram. ¡Escríbele a tu bot!")
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    bot = RickTelegramBot()
    bot.run_polling()
