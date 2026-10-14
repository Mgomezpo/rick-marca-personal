import logging
import secrets
from typing import Any, Dict, List, Optional, Tuple
from supabase import create_client, Client
from src.core.config import config

logger = logging.getLogger("rick.db")

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY son requeridos")
        _supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_client

class DatabaseService:
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    # -------------------------------------------------------------------------
    # 1. Identidad y Onboarding Multi-tenant por WhatsApp
    # -------------------------------------------------------------------------
    def get_or_create_whatsapp_identity(
        self,
        phone_e164: str,
        wa_id: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any], bool]:
        """
        Retorna (user_id, identity_dict, is_new).
        Si el usuario es nuevo, crea la cuenta en auth.users (lo que dispara el
        trigger trial de Supabase), crea la identidad y su registro de memoria activa.
        """
        clean_phone = phone_e164.strip().replace(" ", "").replace("-", "")
        if not clean_phone.startswith("+"):
            clean_phone = f"+{clean_phone}"

        # 1. Buscar en whatsapp_identities
        res = self.client.table("whatsapp_identities").select("*").eq("phone_e164", clean_phone).execute()
        if res.data and len(res.data) > 0:
            identity = res.data[0]
            # Actualizar last_seen_at
            try:
                self.client.table("whatsapp_identities").update({
                    "last_seen_at": "now()",
                    "display_name": display_name or identity.get("display_name")
                }).eq("id", identity["id"]).execute()
            except Exception as e:
                logger.warning(f"Error actualizando last_seen_at: {e}")
            return identity["user_id"], identity, False

        # 2. Es un usuario nuevo: crear en auth.users via Admin API
        safe_num = clean_phone.replace("+", "")
        synthetic_email = f"wa_{safe_num}@ireal.internal"
        random_password = secrets.token_urlsafe(24)

        try:
            auth_user = self.client.auth.admin.create_user({
                "email": synthetic_email,
                "phone": clean_phone,
                "password": random_password,
                "email_confirm": True,
                "phone_confirm": True,
                "user_metadata": {
                    "source": "whatsapp",
                    "display_name": display_name or clean_phone,
                    "phone_e164": clean_phone,
                }
            })
            user_id = auth_user.user.id
            logger.info(f"✨ Usuario auth creado exitosamente para {clean_phone}: {user_id}")
        except Exception as e:
            logger.error(f"Error creando auth.user para {clean_phone}: {e}")
            # Si el correo ya existía (ej. creado previamente), intentamos buscarlo
            try:
                list_users = self.client.auth.admin.list_users()
                found = next((u for u in list_users if u.email == synthetic_email or u.phone == clean_phone), None)
                if found:
                    user_id = found.id
                else:
                    raise e
            except Exception:
                raise e

        # 3. Insertar en whatsapp_identities
        new_identity_data = {
            "user_id": user_id,
            "phone_e164": clean_phone,
            "wa_id": wa_id or safe_num,
            "display_name": display_name,
            "status": "active",
            "verified_at": "now()",
            "last_seen_at": "now()",
        }
        res_ident = self.client.table("whatsapp_identities").insert(new_identity_data).execute()
        new_identity = res_ident.data[0] if res_ident.data else new_identity_data

        # 4. Inicializar memoria activa Tier-1
        self.init_active_memory(user_id)

        return user_id, new_identity, True

    # -------------------------------------------------------------------------
    # 1.B Identidad y Onboarding Multi-tenant por Telegram
    # -------------------------------------------------------------------------
    def get_or_create_telegram_identity(
        self,
        telegram_id: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any], bool]:
        """
        Retorna (user_id, identity_dict, is_new).
        Si el usuario es nuevo, crea la cuenta en auth.users (lo que dispara el
        trigger trial de Supabase), crea la identidad y su registro de memoria activa.
        """
        tg_id_str = str(telegram_id).strip()

        # 1. Buscar en telegram_identities
        try:
            res = self.client.table("telegram_identities").select("*").eq("telegram_id", tg_id_str).execute()
            if res.data and len(res.data) > 0:
                identity = res.data[0]
                try:
                    self.client.table("telegram_identities").update({
                        "last_seen_at": "now()",
                        "username": username or identity.get("username"),
                        "first_name": first_name or identity.get("first_name")
                    }).eq("id", identity["id"]).execute()
                except Exception as e:
                    logger.warning(f"Error actualizando last_seen_at tg: {e}")
                return identity["user_id"], identity, False
        except Exception as e:
            logger.warning(f"Error buscando telegram_identities: {e}")

        # 2. Es nuevo: crear en auth.users
        synthetic_email = f"tg_{tg_id_str}@ireal.internal"
        random_password = secrets.token_urlsafe(24)

        try:
            auth_user = self.client.auth.admin.create_user({
                "email": synthetic_email,
                "password": random_password,
                "email_confirm": True,
                "user_metadata": {
                    "source": "telegram",
                    "telegram_id": tg_id_str,
                    "username": username,
                    "first_name": first_name or "Creador Telegram",
                }
            })
            user_id = auth_user.user.id
            logger.info(f"✨ Usuario auth creado exitosamente para Telegram {tg_id_str}: {user_id}")
        except Exception as e:
            logger.warning(f"Error creando auth.user para Telegram {tg_id_str}: {e}")
            try:
                list_users = self.client.auth.admin.list_users()
                found = next((u for u in list_users if u.email == synthetic_email), None)
                if found:
                    user_id = found.id
                else:
                    raise e
            except Exception:
                raise e

        # 3. Insertar en telegram_identities
        new_identity_data = {
            "user_id": user_id,
            "telegram_id": tg_id_str,
            "username": username,
            "first_name": first_name,
            "status": "active",
            "last_seen_at": "now()",
        }
        try:
            res_ident = self.client.table("telegram_identities").insert(new_identity_data).execute()
            new_identity = res_ident.data[0] if res_ident.data else new_identity_data
        except Exception as e:
            logger.warning(f"Error insertando telegram_identities: {e}")
            new_identity = new_identity_data

        # 4. Inicializar memoria activa Tier-1
        self.init_active_memory(user_id)

        return user_id, new_identity, True

    # -------------------------------------------------------------------------
    # 2. Memoria Activa (Tier-1 Scratchpad)
    # -------------------------------------------------------------------------
    def init_active_memory(self, user_id: str) -> Dict[str, Any]:
        initial_state = {
            "active_topic": None,
            "current_series": None,
            "scratchpad_notes": [],
        }
        try:
            res = self.client.table("rick_active_memory").upsert({
                "user_id": user_id,
                "state": initial_state,
                "summary": "Creador conectado a RICK."
            }).execute()
            return res.data[0] if res.data else {"user_id": user_id, "state": initial_state}
        except Exception as e:
            logger.error(f"Error inicializando memoria activa para {user_id}: {e}")
            return {"user_id": user_id, "state": initial_state}

    def get_active_memory(self, user_id: str) -> Dict[str, Any]:
        try:
            res = self.client.table("rick_active_memory").select("*").eq("user_id", user_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return self.init_active_memory(user_id)
        except Exception as e:
            logger.warning(f"Error consultando memoria activa para {user_id}: {e}")
            return {"user_id": user_id, "state": {}}

    def update_active_memory(self, user_id: str, state: Dict[str, Any], summary: Optional[str] = None) -> bool:
        payload: Dict[str, Any] = {"user_id": user_id, "state": state, "updated_at": "now()"}
        if summary is not None:
            payload["summary"] = summary
        try:
            self.client.table("rick_active_memory").upsert(payload).execute()
            return True
        except Exception as e:
            logger.error(f"Error actualizando memoria activa para {user_id}: {e}")
            return False

    # -------------------------------------------------------------------------
    # 3. Cerebro de Marca (brand_assets + user_profiles)
    # -------------------------------------------------------------------------
    def get_brand_assets(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        try:
            res = self.client.table("brand_assets").select("*").eq("user_id", user_id).execute()
            assets = {}
            for row in res.data or []:
                assets[row["slot_type"]] = row
            return assets
        except Exception as e:
            logger.warning(f"Error consultando brand_assets para {user_id}: {e}")
            return {}

    def upsert_brand_asset(
        self,
        user_id: str,
        slot_type: str,
        content: Dict[str, Any],
        summary: str,
        status: str = "ready",
        embedding: Optional[List[float]] = None
    ) -> bool:
        payload: Dict[str, Any] = {
            "user_id": user_id,
            "slot_type": slot_type,
            "status": status,
            "content": content,
            "summary": summary,
            "source": "rick_auto",
            "updated_at": "now()",
        }
        if embedding:
            payload["embedding"] = embedding
        try:
            self.client.table("brand_assets").upsert(payload, on_conflict="user_id, slot_type").execute()
            return True
        except Exception as e:
            logger.error(f"Error guardando brand_asset {slot_type} para {user_id}: {e}")
            return False

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.table("user_profiles").select("*").eq("user_id", user_id).execute()
            return res.data[0] if (res.data and len(res.data) > 0) else None
        except Exception as e:
            logger.warning(f"Error consultando user_profile para {user_id}: {e}")
            return None

    def upsert_user_profile(self, user_id: str, fields: Dict[str, Any]) -> bool:
        payload = {"user_id": user_id, **fields, "updated_at": "now()"}
        try:
            self.client.table("user_profiles").upsert(payload, on_conflict="user_id").execute()
            return True
        except Exception as e:
            logger.error(f"Error guardando user_profile para {user_id}: {e}")
            return False

    # -------------------------------------------------------------------------
    # 4. Piezas / Guiones (pieces)
    # -------------------------------------------------------------------------
    def save_script_piece(
        self,
        user_id: str,
        title: str,
        hook: str,
        body: str,
        copy: str = "",
        format: str = "reel",
        framework: str = "",
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "title": title,
            "content": body,
            "script": f"GANCHO:\n{hook}\n\nCUERPO:\n{body}",
            "copy": copy,
            "format": format,
            "strategy_tag": framework,
            "status": "draft",
            "approved": False,
            "thread_id": thread_id,
        }
        try:
            res = self.client.table("pieces").insert(payload).execute()
            return res.data[0] if res.data else payload
        except Exception as e:
            logger.error(f"Error guardando pieza en Supabase: {e}")
            return payload

    save_generated_script = save_script_piece

    def get_user_scripts(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            res = self.client.table("pieces").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error listando piezas de {user_id}: {e}")
            return []

    # -------------------------------------------------------------------------
    # 5. Memoria Episódica & RAG Vectorial (768d)
    # -------------------------------------------------------------------------
    def search_episodic_memory(self, user_id: str, query_embedding: List[float], match_count: int = 3) -> List[Dict[str, Any]]:
        try:
            res = self.client.rpc("match_episodic_memory", {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "p_user_id": user_id
            }).execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Error en match_episodic_memory RPC: {e}")
            return []

    def save_episodic_memory(
        self,
        user_id: str,
        kind: str,
        title: str,
        content: Dict[str, Any],
        context_blurb: str,
        embedding: Optional[List[float]] = None,
        importance: int = 5,
        pilar: Optional[str] = None,
        formato: Optional[str] = None
    ) -> bool:
        payload = {
            "user_id": user_id,
            "kind": kind,
            "title": title,
            "content": content,
            "context_blurb": context_blurb,
            "importance": importance,
            "pilar": pilar,
            "formato": formato,
        }
        if embedding:
            payload["embedding"] = embedding
        try:
            self.client.table("episodic_memory").insert(payload).execute()
            return True
        except Exception as e:
            logger.error(f"Error guardando memoria episódica: {e}")
            return False

    # -------------------------------------------------------------------------
    # 6. Hilos de Conversación y Mensajes de WhatsApp
    # -------------------------------------------------------------------------
    def get_or_create_whatsapp_thread(self, user_id: str) -> Dict[str, Any]:
        res = self.client.table("rick_threads").select("*").eq("user_id", user_id).eq("kind", "whatsapp").execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        new_thread = {
            "user_id": user_id,
            "kind": "whatsapp",
            "title": "Canal Directo WhatsApp con RICK",
            "transcript": [],
            "turn_count": 0,
        }
        res_new = self.client.table("rick_threads").insert(new_thread).execute()
        return res_new.data[0] if res_new.data else new_thread

    def get_or_create_telegram_thread(self, user_id: str) -> Dict[str, Any]:
        res = self.client.table("rick_threads").select("*").eq("user_id", user_id).eq("kind", "telegram").execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        new_thread = {
            "user_id": user_id,
            "kind": "telegram",
            "title": "Canal Directo Telegram con RICK",
            "transcript": [],
            "turn_count": 0,
        }
        res_new = self.client.table("rick_threads").insert(new_thread).execute()
        return res_new.data[0] if res_new.data else new_thread

    def append_thread_message(self, thread_id: str, role: str, content: str) -> None:
        try:
            thread_res = self.client.table("rick_threads").select("transcript, turn_count").eq("id", thread_id).execute()
            if thread_res.data and len(thread_res.data) > 0:
                transcript = thread_res.data[0].get("transcript") or []
                turn_count = thread_res.data[0].get("turn_count", 0) + 1
                transcript.append({"role": role, "content": content, "timestamp": "now()"})
                # Mantener los últimos 20 turnos en el transcript crudo
                if len(transcript) > 30:
                    transcript = transcript[-30:]
                self.client.table("rick_threads").update({
                    "transcript": transcript,
                    "turn_count": turn_count,
                    "updated_at": "now()",
                }).eq("id", thread_id).execute()
        except Exception as e:
            logger.warning(f"Error actualizando transcript del hilo {thread_id}: {e}")

    def is_message_processed(self, wa_message_id: str) -> bool:
        res = self.client.table("whatsapp_messages").select("id").eq("wa_message_id", wa_message_id).execute()
        return bool(res.data and len(res.data) > 0)

    def log_whatsapp_message(
        self,
        wa_message_id: str,
        user_id: Optional[str],
        direction: str,
        body: str,
        status: str = "received",
        msg_type: str = "text",
        thread_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        payload = {
            "wa_message_id": wa_message_id,
            "user_id": user_id,
            "direction": direction,
            "body": body,
            "status": status,
            "msg_type": msg_type,
            "thread_id": thread_id,
            "error": error,
        }
        try:
            self.client.table("whatsapp_messages").upsert(payload, on_conflict="wa_message_id").execute()
        except Exception as e:
            logger.warning(f"Error guardando log de whatsapp_messages: {e}")
