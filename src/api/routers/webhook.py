import logging
from typing import Any, Dict
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response
from src.core.config import config
from src.db.supabase import DatabaseService
from src.services.whatsapp import WhatsAppClient
from src.engine.orchestrator import RickOrchestrator

logger = logging.getLogger("rick.webhook")

router = APIRouter()
db_service = DatabaseService()
whatsapp_client = WhatsAppClient()
orchestrator = RickOrchestrator(db_service)

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
    msg_type: str = "text"
):
    try:
        logger.info(f"🚀 [Background Task] Procesando mensaje de {sender_phone} ({sender_name}): '{body_text[:50]}...'")

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

        # 5. Ejecutar RICK Orchestrator
        rick_reply = orchestrator.process_message(
            user_message=body_text,
            user_id=user_id,
            channel="whatsapp",
            thread_id=thread_id
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
        logger.info(f"✨ Turno completado exitosamente para {sender_phone}")

    except Exception as e:
        logger.error(f"❌ Error crítico procesando mensaje de fondo: {e}", exc_info=True)
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
    try:
        data = await request.json()
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

                # Extraer cuerpo del texto
                body_text = ""
                if msg_type == "text":
                    body_text = msg.get("text", {}).get("body", "")
                elif msg_type == "audio":
                    body_text = "[Nota de voz enviada]"
                else:
                    body_text = f"[{msg_type} recibido]"

                # Despachar a tarea en segundo plano y responder HTTP 200 de inmediato
                background_tasks.add_task(
                    process_whatsapp_background_task,
                    sender_phone=sender_phone,
                    message_id=message_id,
                    body_text=body_text,
                    sender_name=sender_name,
                    msg_type=msg_type
                )

    return {"status": "ok"}
