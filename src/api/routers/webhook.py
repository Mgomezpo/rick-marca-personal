import hmac
import hashlib
import json
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response
from src.core.config import config
from src.core.observability import (
    generate_correlation_id,
    set_request_context,
    get_correlation_id,
    log_event,
)
from src.db.supabase import DatabaseService
from src.services.whatsapp import WhatsAppClient
from src.engine.orchestrator import RickOrchestrator

logger = logging.getLogger("rick.webhook")

router = APIRouter()
db_service = DatabaseService()
whatsapp_client = WhatsAppClient()
orchestrator = RickOrchestrator(db_service)

def verify_meta_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
    """
    Verifica la firma criptográfica HMAC-SHA256 de Meta (X-Hub-Signature-256)
    usando META_APP_SECRET para prevenir suplantación (spoofing) de webhooks.
    """
    if not config.META_APP_SECRET:
        return True  # Si no está configurado (modo local o desarrollo), se omite la verificación
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected_hash = hmac.new(
        config.META_APP_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    received_hash = signature_header.split("sha256=")[1]
    return hmac.compare_digest(expected_hash, received_hash)

# -----------------------------------------------------------------------------
# 1. GET /webhook — Verificación de Meta Challenge
# -----------------------------------------------------------------------------
@router.get("/webhook")
async def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    logger.info(f"🔍 Meta Webhook Verification Request: mode={hub_mode}, token={hub_verify_token}")
    if hub_mode == "subscribe" and hub_verify_token == config.WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ Meta Webhook verificado exitosamente!")
        return Response(content=hub_challenge, media_type="text/plain")
    
    logger.warning("❌ Token de verificación inválido")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

# -----------------------------------------------------------------------------
# 2. Worker de Procesamiento en Segundo Plano (<200ms ACK Pattern)
# -----------------------------------------------------------------------------
async def process_whatsapp_background_task(
    sender_phone: str,
    message_id: str,
    body_text: str,
    sender_name: str,
    msg_type: str = "text",
    media_id: str = None
):
    corr_id = f"wa_{message_id}" if message_id else generate_correlation_id("wa")
    set_request_context(correlation_id=corr_id, entry_point="whatsapp", user_id=sender_phone)

    try:
        log_event(
            logger,
            logging.INFO,
            event="whatsapp_task_started",
            message=f"🚀 [Background Task] Procesando mensaje de {sender_phone} ({sender_name}): tipo={msg_type}...",
            sender_phone=sender_phone,
            sender_name=sender_name,
            msg_type=msg_type,
            wa_message_id=message_id
        )

        # 0. Si es nota de voz o audio, descargar y transcribir
        if msg_type == "audio" and media_id:
            try:
                audio_bytes = whatsapp_client.download_media_bytes(media_id)
                if audio_bytes:
                    transcribed = whatsapp_client.transcribe_audio_bytes(audio_bytes)
                    if transcribed and "no se pudo transcribir" not in transcribed.lower():
                        body_text = f"[Nota de voz]: {transcribed}"
                        log_event(
                            logger,
                            logging.INFO,
                            event="whatsapp_audio_transcribed",
                            message=f"🎙️ [WhatsApp] Audio transcrito: '{body_text[:60]}...'",
                            char_count=len(transcribed)
                        )
                    else:
                        body_text = "[Nota de voz enviada (audio inaudible o error en transcripción)]"
                else:
                    body_text = "[Nota de voz enviada (no se pudo descargar el archivo de Meta)]"
            except Exception as audio_err:
                log_event(
                    logger,
                    logging.ERROR,
                    event="whatsapp_audio_error",
                    message=f"Error procesando audio de WhatsApp: {audio_err}",
                    error_message=str(audio_err)
                )
                body_text = "[Nota de voz enviada]"

        # 1. Obtener o crear tenant (auto-provisioning de usuario y trial)
        user_id, identity, is_new = db_service.get_or_create_whatsapp_identity(
            phone_e164=sender_phone,
            display_name=sender_name
        )

        # 2. Hilo de conversación
        thread = db_service.get_or_create_whatsapp_thread(user_id)
        thread_id = thread.get("id")

        # 3. Registrar mensaje entrante y marcar leído en WhatsApp
        db_service.log_whatsapp_message(
            wa_message_id=message_id,
            user_id=user_id,
            direction="in",
            body=body_text,
            status="processing",
            msg_type=msg_type,
            thread_id=thread_id
        )
        whatsapp_client.mark_as_read(message_id)

        # 4. Guardar turno del usuario en transcript
        db_service.append_thread_message(thread_id, "user", body_text)

        # 5. Ejecutar RICK Orchestrator con correlation_id
        rick_reply = orchestrator.process_message(
            user_message=body_text,
            user_id=user_id,
            channel="whatsapp",
            thread_id=thread_id,
            correlation_id=corr_id
        )

        # 6. Despachar respuesta hacia WhatsApp
        whatsapp_client.send_text_message(to_phone=sender_phone, text=rick_reply)

        # 7. Guardar turno de RICK en transcript y actualizar estado del mensaje
        db_service.append_thread_message(thread_id, "assistant", rick_reply)
        db_service.log_whatsapp_message(
            wa_message_id=message_id,
            user_id=user_id,
            direction="in",
            body=body_text,
            status="done",
            msg_type=msg_type,
            thread_id=thread_id
        )
        log_event(
            logger,
            logging.INFO,
            event="whatsapp_task_completed",
            message=f"✨ Turno completado exitosamente para {sender_phone}",
            user_id=user_id,
            sender_phone=sender_phone
        )

    except Exception as e:
        log_event(
            logger,
            logging.ERROR,
            event="whatsapp_task_failed",
            message=f"❌ Error crítico procesando mensaje de fondo: {e}",
            error_type=type(e).__name__,
            error_message=str(e),
            sender_phone=sender_phone
        )
        db_service.log_whatsapp_message(
            wa_message_id=message_id,
            user_id=None,
            direction="in",
            body=body_text,
            status="failed",
            error=str(e)
        )

# -----------------------------------------------------------------------------
# 3. POST /webhook — Ingest Inmediato con ACK < 200ms
# -----------------------------------------------------------------------------
@router.post("/webhook")
async def receive_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256")
    if not verify_meta_signature(raw_body, sig_header):
        logger.warning("❌ Firma Meta X-Hub-Signature-256 inválida o ausente")
        raise HTTPException(status_code=403, detail="Invalid Meta webhook signature")

    try:
        data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        return {"status": "ignored", "reason": "invalid_json"}

    # Extraer mensajes del payload de Meta
    entries = data.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            for msg in messages:
                message_id = msg.get("id")
                sender_phone = msg.get("from")
                msg_type = msg.get("type", "text")

                # Obtener nombre del contacto si existe
                sender_name = "Creador"
                if contacts and len(contacts) > 0:
                    sender_name = contacts[0].get("profile", {}).get("name", "Creador")

                # Deduplicación inmediata (Idempotencia)
                if db_service.is_message_processed(message_id):
                    logger.info(f"🔁 Mensaje duplicado omitido: {message_id}")
                    return {"status": "ok", "detail": "duplicate_skipped"}

                # Extraer cuerpo del texto y media_id
                body_text = ""
                media_id = None
                if msg_type == "text":
                    body_text = msg.get("text", {}).get("body", "")
                elif msg_type == "audio":
                    body_text = "[Nota de voz enviada]"
                    media_id = msg.get("audio", {}).get("id")
                else:
                    body_text = f"[{msg_type} recibido]"

                # Despachar a tarea en segundo plano y responder HTTP 200 de inmediato
                background_tasks.add_task(
                    process_whatsapp_background_task,
                    sender_phone=sender_phone,
                    message_id=message_id,
                    body_text=body_text,
                    sender_name=sender_name,
                    msg_type=msg_type,
                    media_id=media_id
                )

    return {"status": "ok"}
