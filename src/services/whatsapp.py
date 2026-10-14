import logging
import httpx
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from src.core.config import config

logger = logging.getLogger("rick.service.whatsapp")

def format_whatsapp_text(text: str) -> str:
    """
    Adapta formato Markdown a WhatsApp:
    - Transforma **negrita** a *negrita* (WhatsApp usa un solo asterisco para negrita)
    - Remueve encabezados ### y líneas divisorias ---
    """
    import re
    cleaned = re.sub(r'^[-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    cleaned = re.sub(r'^(#{1,6})\s+(.+)$', r'*\2*', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\*\*(.+?)\*\*', r'*\1*', cleaned)
    cleaned = re.sub(r'^\s*[\*\-]\s+', '• ', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

class WhatsAppClient:
    """
    Cliente para la API de Meta WhatsApp Cloud.
    Maneja envío de mensajes, indicador de 'escribiendo...', fragmentación inteligente
    de guiones largos y transcripción multimodal de audios con Gemini.
    """
    def __init__(self):
        self.api_version = config.WHATSAPP_API_VERSION
        self.phone_number_id = config.WHATSAPP_PHONE_NUMBER_ID
        self.token = config.WHATSAPP_TOKEN
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    # -------------------------------------------------------------------------
    # 1. Fragmentación Inteligente de Mensajes (Chunking)
    # -------------------------------------------------------------------------
    def chunk_message(self, text: str, max_chars: int = 1500) -> List[str]:
        """
        Divide textos largos (ej. guiones de 5 actos) en bloques legibles para WhatsApp,
        respetando párrafos y encabezados para no cortar a mitad de una frase.
        """
        if not text:
            return []
        if len(text) <= max_chars:
            return [text]

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            # Si un párrafo individual excede max_chars, trocearlo de forma segura
            while len(p) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                split_idx = p.rfind("\n", 0, max_chars)
                if split_idx == -1 or split_idx < max_chars // 2:
                    split_idx = p.rfind(" ", 0, max_chars)
                if split_idx == -1 or split_idx < max_chars // 2:
                    split_idx = max_chars
                chunks.append(p[:split_idx].strip())
                p = p[split_idx:].strip()

            if not p:
                continue

            if len(current_chunk) + len(p) + 2 <= max_chars:
                current_chunk += (("\n\n" if current_chunk else "") + p)
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    # -------------------------------------------------------------------------
    # 2. Envío de Mensajes de Texto
    # -------------------------------------------------------------------------
    def send_text_message(self, to_phone: str, text: str) -> bool:
        clean_to = to_phone.replace("+", "").strip()
        formatted = format_whatsapp_text(text)

        # Si el token es de placeholder o estamos en test, simulamos el log
        if not self.token or "PLACEHOLDER" in self.token:
            logger.info(f"📱 [WhatsApp MOCK Send] To={clean_to} | Chunks={len(self.chunk_message(formatted))} | Preview='{formatted[:80]}...'")
            return True

        chunks = self.chunk_message(formatted)
        success = True

        with httpx.Client(timeout=10.0) as http:
            for idx, chunk in enumerate(chunks):
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": clean_to,
                    "type": "text",
                    "text": {"preview_url": False, "body": chunk},
                }
                try:
                    resp = http.post(f"{self.base_url}/messages", headers=self._headers(), json=payload)
                    if resp.status_code in (200, 201):
                        logger.info(f"✅ Mensaje WhatsApp enviado [{idx+1}/{len(chunks)}] a {clean_to}")
                    else:
                        logger.error(f"❌ Error enviando WhatsApp a {clean_to}: {resp.status_code} - {resp.text}")
                        success = False
                except Exception as e:
                    logger.error(f"Error de conexión enviando WhatsApp: {e}")
                    success = False

        return success

    # -------------------------------------------------------------------------
    # 3. Indicador de Lectura y Escribiendo (Typing Indicator)
    # -------------------------------------------------------------------------
    def mark_as_read(self, message_id: str) -> bool:
        if not self.token or "PLACEHOLDER" in self.token:
            return True

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        try:
            with httpx.Client(timeout=5.0) as http:
                resp = http.post(f"{self.base_url}/messages", headers=self._headers(), json=payload)
                return resp.status_code in (200, 201)
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # 4. Descarga de Media (Audio / Notas de Voz)
    # -------------------------------------------------------------------------
    def download_media_bytes(self, media_id: str) -> Optional[bytes]:
        """
        Descarga los bytes de un archivo multimedia (ej. audio) desde Meta Graph API.
        """
        if not self.token or "PLACEHOLDER" in self.token:
            return None
        try:
            with httpx.Client(timeout=15.0) as http:
                url_resp = http.get(f"https://graph.facebook.com/{self.api_version}/{media_id}", headers=self._headers())
                if url_resp.status_code != 200:
                    logger.error(f"Error obteniendo URL de audio de Meta: {url_resp.status_code} - {url_resp.text}")
                    return None
                media_url = url_resp.json().get("url")
                if not media_url:
                    return None
                download_resp = http.get(media_url, headers=self._headers())
                if download_resp.status_code == 200:
                    return download_resp.content
                logger.error(f"Error descargando bytes de audio desde Meta: {download_resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error descargando audio de WhatsApp: {e}")
            return None

    # -------------------------------------------------------------------------
    # 5. Transcripción de Notas de Voz (Gemini Multimodal)
    # -------------------------------------------------------------------------
    def transcribe_audio_bytes(self, audio_data: bytes, mime_type: str = "audio/ogg") -> str:
        """
        Usa Gemini multimodal para transcribir notas de voz de WhatsApp con máxima fidelidad.
        """
        logger.info(f"🎙️ [WhatsApp] Transcribiendo nota de voz ({len(audio_data)} bytes)...")
        try:
            response = self.client.models.generate_content(
                model=config.ORCHESTRATOR_MODEL,
                contents=[
                    types.Part.from_bytes(data=audio_data, mime_type=mime_type),
                    "Transcribe con total exactitud este audio de un creador. Devuelve ÚNICAMENTE el texto transcrito."
                ]
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error transcribiendo audio con Gemini: {e}")
            return "Nota de voz recibida (no se pudo transcribir el audio automáticamente)."
