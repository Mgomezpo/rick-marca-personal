"""WhatsApp Cloud API Webhook handler with sub-200ms ACK and BackgroundTasks processing."""
import os
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, BackgroundTasks, HTTPException, Query

from src.graph.state import create_initial_state, ConversationMessage
from src.graph.engine import RickGraphEngine
from src.db.repository import SupabaseRepository

logger = logging.getLogger("rick.webhook")
router = APIRouter(prefix="/webhook", tags=["Webhook"])
repo = SupabaseRepository()
engine = RickGraphEngine()


def send_whatsapp_message(
    to_phone: str,
    text: str,
    phone_number_id: Optional[str] = None,
    token: Optional[str] = None,
) -> bool:
    """
    Dispatch text message to WhatsApp Cloud API.
    Returns True if delivered or simulated successfully.
    """
    phone_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    auth_token = token or os.getenv("WHATSAPP_TOKEN")

    if not phone_id or not auth_token:
        logger.info(f"[SIMULATED WHATSAPP OUTBOUND] To: {to_phone} | Message: {text[:60]}...")
        return True

    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }

    try:
        import httpx
        res = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        if res.status_code in (200, 201):
            logger.info(f"WhatsApp message dispatched to {to_phone} successfully.")
            return True
        else:
            logger.error(f"WhatsApp API returned error {res.status_code}: {res.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to dispatch WhatsApp message to {to_phone}: {e}")
        return False


def process_whatsapp_background(payload: Dict[str, Any]) -> None:
    """
    Background worker that runs the full RICK graph without blocking the HTTP ACK.
    Maintains conversation persistence across turns and dispatches outbound responses.
    """
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])

                for msg in messages:
                    sender_phone = msg.get("from", "unknown_user")
                    user_id = f"wa_{sender_phone}"
                    sender_name = contacts[0].get("profile", {}).get("name", sender_phone) if contacts else sender_phone

                    # Extract text or process audio voice note (Whisper-1 / Gemini)
                    text_body = ""
                    msg_type = msg.get("type")
                    if msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "")
                    elif msg_type == "audio":
                        audio_info = msg.get("audio", {})
                        media_id = audio_info.get("id")
                        if media_id:
                            from src.services.voice import voice_service
                            audio_bytes = voice_service.download_whatsapp_media(media_id)
                            if audio_bytes:
                                mime = audio_info.get("mime_type", "audio/ogg")
                                text_body = voice_service.transcribe_audio(audio_bytes, mime_type=mime)
                                logger.info(f"WhatsApp audio {media_id} transcribed: '{text_body[:50]}...'")

                    if not text_body:
                        continue

                    # Load or initialize state
                    profile = repo.get_creator_profile(user_id)
                    state = create_initial_state(user_id=user_id, handle=sender_name)
                    if profile:
                        state["creator_profile"] = profile
                        state["story_bank"] = profile.story_bank
                    else:
                        state["story_bank"] = repo.get_story_bank(user_id)

                    # Load previous learnings from Supabase
                    state["learnings"] = repo.get_learnings(user_id)

                    # Persist user message and load full conversation history
                    user_msg = ConversationMessage(
                        role="user",
                        content=text_body,
                        timestamp=str(msg.get("timestamp", "")),
                    )
                    repo.save_message(user_id, user_msg)
                    state["messages"] = repo.get_conversation(user_id)

                    # Run graph
                    final_state = engine.run(state)

                    # Save new learnings generated during the session
                    for learning in final_state.get("learnings", []):
                        repo.save_learning(learning)

                    # Save script piece if generated
                    draft = final_state.get("script_draft")
                    if draft:
                        repo.save_piece(user_id, draft)

                    # Persist assistant reply and dispatch outbound message to WhatsApp
                    final_response = final_state.get("final_response")
                    if final_response:
                        assistant_msg = ConversationMessage(
                            role="assistant",
                            content=final_response,
                        )
                        repo.save_message(user_id, assistant_msg)
                        send_whatsapp_message(to_phone=sender_phone, text=final_response)

                    logger.info(f"Processed message for {user_id}: response ready and dispatched.")
    except Exception as e:
        logger.error(f"Error in WhatsApp background processor: {e}")


@router.get("/whatsapp")
def verify_whatsapp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """
    Meta WhatsApp Cloud API Webhook challenge verification.
    """
    expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "rick_secret_verify_token_2026")

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return Response(content=hub_challenge or "", media_type="text/plain")

    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/whatsapp")
def receive_whatsapp_event(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
):
    """
    Receive WhatsApp webhook event.
    Returns ACK < 100ms and delegates execution to background task.
    """
    background_tasks.add_task(process_whatsapp_background, payload)
    return {"status": "received"}
