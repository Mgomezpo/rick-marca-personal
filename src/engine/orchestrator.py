import logging
import json
import time
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from src.core.config import config
from src.core.telemetry import TelemetryTracker
from src.core.observability import set_request_context, get_correlation_id, get_entry_point, log_event
from src.core.metrics import metrics_tracker
from src.db.supabase import DatabaseService
from src.engine.vfs import VirtualFileSystem
from src.engine.tools import OPENAI_TOOLS, execute_tool_call
from src.engine.skills_loader import skills_loader

logger = logging.getLogger("rick.orchestrator")

def load_master_system_prompt() -> str:
    """
    Carga el cerebro completo de RICK:
    1. Canon maestro unificado de AGENTS.md.
    2. Principios de filosofía de Rick Rubin (reduction, beginner_mind, synthesis).
    3. Árbol de decisión heurístico de estudio (decision_tree.md).
    """
    base = ""
    for filename in ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]:
        target = config.ROOT_DIR / filename
        if target.exists():
            base = target.read_text(encoding="utf-8")
            break
    if not base:
        base = "Te llamas RICK. Eres el Head of Content y productor creativo."

    return base

class RickOrchestrator:
    def __init__(self, db: DatabaseService):
        self.db = db
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.telemetry = TelemetryTracker(self.db.client)
        self.vfs = VirtualFileSystem(self.db)
        self.base_system_prompt = load_master_system_prompt()
        self.oa_client = None
        if config.OPENAI_API_KEY:
            try:
                import openai
                self.oa_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Error inicializando cliente OpenAI en RickOrchestrator: {e}")

    def process_message(
        self,
        user_message: str,
        user_id: str,
        channel: str = "whatsapp",
        thread_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Ejecuta el ciclo de RICK como Head of Content:
        - Si el creador no ha completado el onboarding socrático (onboarding_status != 'completed'),
          opera bajo la skill de creator-interview con herramientas (investigar_huella_creador, completar_onboarding_creador).
        - Si ya está consolidado en el estudio (onboarding_status == 'completed'), opera en modo producción activa
          con pipeline de guiones (redactar_guion_formato_oficial) y memoria viva.
        Todo fluye a través del motor unificado de Function Calling de OpenAI (con fallback a Gemini).
        """
        if correlation_id:
            set_request_context(correlation_id=correlation_id, entry_point=channel, user_id=user_id)
        start_time = time.time()
        log_event(
            logger,
            logging.INFO,
            event="orchestrator_turn_started",
            message=f"🎙️ [RICK Orchestrator] Mensaje de usuario {user_id}: '{user_message[:60]}...'",
            channel=channel,
            user_id=user_id,
            thread_id=thread_id or ""
        )

        # 1. Estado de memoria y perfil en BD
        profile = self.db.get_user_profile(user_id) or {}
        is_onboarded = (profile.get("onboarding_status") == "completed")
        known_handle = profile.get("analytics_username") or profile.get("instagram_handle") or ""

        voice_dna_md = self.vfs.read_file("creator/identity/voice_dna.md", user_id)
        positioning_md = self.vfs.read_file("creator/identity/positioning.md", user_id)
        lore_md = self.vfs.read_file("creator/lore/origin_stories.md", user_id)
        active_ctx_md = self.vfs.read_file("memorias/active_context.md", user_id)
        recent_scripts_md = self.vfs.read_file("produccion/scripts", user_id)

        # Construcción de la memoria base del creador (SIEMPRE DISPONIBLE PARA EL ARNES)
        creator_name = profile.get("creator_name") or ""
        main_niche = profile.get("main_niche") or ""
        passion = profile.get("passion") or ""
        unique_angle = profile.get("unique_angle") or ""
        backstory = profile.get("backstory") or ""

        creator_summary_parts = []
        if known_handle:
            creator_summary_parts.append(f"- **Handle en redes:** @{known_handle}")
        if creator_name:
            creator_summary_parts.append(f"- **Nombre del Creador:** {creator_name}")
        if main_niche:
            creator_summary_parts.append(f"- **Nicho:** {main_niche}")
        if passion:
            creator_summary_parts.append(f"- **Obsesión / Pasión:** {passion}")
        if unique_angle:
            creator_summary_parts.append(f"- **Enemigo Común / Ángulo Único:** {unique_angle}")
        if backstory:
            creator_summary_parts.append(f"- **Huella / Backstory Verificado:**\n{backstory}")

        creator_identity_block = "\n".join(creator_summary_parts) if creator_summary_parts else "Aún no hay datos adicionales registrados."

        # Bloque de memoria viva acumulada (inyección continua sin amnesia)
        persistent_memory_block = (
            f"### RADIOGRAFÍA Y LORE DEL CREADOR (PERFIL EN SUPABASE):\n{creator_identity_block}\n\n"
            f"### LORE DETALLADO (VFS):\n{lore_md}\n\n"
            f"### ADN DE VOZ Y POSICIONAMIENTO:\n{voice_dna_md}\n\n{positioning_md}\n\n"
            f"### MEMORIA ACTIVA Y ESTADO ACTUAL:\n{active_ctx_md}\n\n"
            f"### GUIONES Y PIEZAS EN LA MESA:\n{recent_scripts_md}\n"
        )

        # 2. Inyección dinámica según estado del binario en BD
        if not is_onboarded:
            handle_status = f"Usuario de Instagram ya registrado: @{known_handle}" if known_handle else "Aún no ha proporcionado su usuario de redes."
            context_block = (
                f"{persistent_memory_block}\n"
                f"### ESTADO DEL CREADOR: CONOCIENDO AL CREADOR\n"
                f"{handle_status}\n"
                f"- Si es el primer contacto: preséntate con cercanía y autoridad como su Head of Content ('¡Ey! Soy RICK, tu nuevo Head of Content. Hago crecer tu audiencia analizando lo que publicas y estructurando el contenido...'), y pídele su @usuario de Instagram o una breve nota de voz contándote qué construye.\n"
                f"- Si comparte su cuenta: revisa su huella con `investigar_huella_creador`, comenta lo que ves con naturalidad y sigan conversando.\n"
                f"- Conversa libremente: CERO cuestionarios rígidos, CERO preguntas de plantilla numeradas, CERO fórmulas robóticas como 'Entiendo, [Nombre]' o 'Listo, [Nombre]'. Hablen como dos colegas creativos.\n"
                f"- Cuando ya tengas claro su nicho y visión, completa el onboarding con `completar_onboarding_creador` y pasen a pelotear ideas o armar guiones."
            )
        else:
            context_block = (
                f"{persistent_memory_block}\n"
                f"### ESTADO DEL CREADOR: EN PRODUCCIÓN ACTIVA\n"
                f"El creador ya tiene su perfil en el estudio. Habla con cercanía desde su contexto real."
            )

        system_instruction = (
            f"{self.base_system_prompt}\n\n"
            f"---\n"
            f"{context_block}\n\n"
            f"### PAUTAS DE TRABAJO DE RICK:\n"
            f"1. Conversación real y libre: Hablas de tú a tú por chat de forma relajada, directa y sin filtros corporativos. Cero rodeos, cero discursos y cero muletillas de robot ('Entiendo, [Nombre]', 'Comprendo', 'Listo, [Nombre]').\n"
            f"2. Peloteo de ideas y estrategia: Si el creador quiere pensar ideas, debatir conceptos, revisar qué hace la competencia o explorar ángulos, PELOTEA CON ÉL. Propón 2 o 3 ángulos concretos, filosos y con criterio en pocas líneas. No asumas que hablar de una idea significa escribir un guion de inmediato.\n"
            f"3. Redacción de guiones: Solo cuando el creador te pida redactar el guion o ya hayan acordado la idea a grabar, llama a la herramienta `redactar_guion_formato_oficial(brief=...)` para armar la pieza.\n"
            f"4. Uso de herramientas: Si necesitas ver sus publicaciones usa `consultar_posts_instagram`, si necesitas guiones previos usa `consultar_piezas_creador`, si necesitas actualizar datos usa `guardar_identidad_creador` o `actualizar_memoria_activa`. Jamás menciones nombres técnicos de herramientas ni APIs al creador.\n"
            f"5. Cero cuarta pared: Eres el director de contenido de su canal; nunca digas que eres una IA ni des excusas técnicas.\n"
            f"6. Cero preguntas tímidas de permiso: Nunca cierres con preguntas de permiso serviles como '¿Te gustaría que...?' o '¿Quieres que...?'. Haz propuestas directas o preguntas de criterio."
        )

        try:
            # Recuperar últimos mensajes del hilo (ventana contextual amplia de hasta 30 mensajes)
            history_messages = []
            if thread_id:
                try:
                    th = self.db.client.table("rick_threads").select("transcript").eq("id", thread_id).execute()
                    if th.data and th.data[0].get("transcript"):
                        raw_transcript = th.data[0]["transcript"]
                        # Si el último mensaje del transcript ya es el mensaje actual del usuario (agregado previamente por el bot),
                        # lo excluimos del historial previo para no duplicarlo al enviarlo como user_message.
                        if raw_transcript and raw_transcript[-1].get("role") == "user" and raw_transcript[-1].get("content", "").strip() == user_message.strip():
                            raw_transcript = raw_transcript[:-1]

                        for m in raw_transcript[-30:]:
                            role = m.get("role", "user")
                            content = m.get("content", "")
                            if "interferencia en la mesa" not in content and content.strip():
                                history_messages.append({"role": role, "content": content})
                except Exception as e:
                    logger.warning(f"Error cargando historial de thread {thread_id}: {e}")

            final_text = ""
            used_model = config.OPENAI_MODEL
            tokens_in = 100
            tokens_out = 50

            # -----------------------------------------------------------------
            # 1. MOTOR PRINCIPAL: OpenAI con Function Calling real
            # -----------------------------------------------------------------
            if config.OPENAI_API_KEY and self.oa_client:
                try:
                    logger.info(f"⚡ [Orchestrator] Ejecutando OpenAI {config.OPENAI_MODEL} con tools...")
                    oa_client = self.oa_client
                    oa_msgs = [{"role": "system", "content": system_instruction}]
                    for hm in history_messages:
                        oa_msgs.append({"role": hm["role"], "content": hm["content"]})
                    oa_msgs.append({"role": "user", "content": user_message})

                    max_tool_turns = 3
                    turn = 0
                    while turn < max_tool_turns:
                        turn += 1
                        oa_resp = oa_client.chat.completions.create(
                            model=config.OPENAI_MODEL,
                            messages=oa_msgs,
                            tools=OPENAI_TOOLS,
                            temperature=0.5
                        )
                        msg = oa_resp.choices[0].message
                        if hasattr(oa_resp, "usage") and oa_resp.usage:
                            tokens_in += getattr(oa_resp.usage, "prompt_tokens", 0)
                            tokens_out += getattr(oa_resp.usage, "completion_tokens", 0)

                        # Si el modelo solicita ejecutar herramientas
                        if msg.tool_calls:
                            oa_msgs.append(msg)
                            for tc in msg.tool_calls:
                                fn_name = tc.function.name
                                try:
                                    fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                                except Exception:
                                    fn_args = {}
                                tool_start = time.time()
                                tool_result = execute_tool_call(
                                    tool_name=fn_name,
                                    args=fn_args,
                                    user_id=user_id,
                                    db=self.db,
                                    vfs=self.vfs,
                                    thread_id=thread_id
                                )
                                tool_dur = int((time.time() - tool_start) * 1000)
                                metrics_tracker.record_tool_call(fn_name, tool_dur)
                                log_event(
                                    logger,
                                    logging.INFO,
                                    event="tool_execution_completed",
                                    message=f"Tool {fn_name} ejecutada en {tool_dur}ms",
                                    tool_name=fn_name,
                                    duration_ms=tool_dur,
                                    user_id=user_id
                                )
                                oa_msgs.append({
                                    "role": "tool",
                                    "tool_call_id": tc.id,
                                    "content": tool_result
                                })
                        else:
                            # Respuesta de texto final
                            final_text = (msg.content or "").strip()
                            break

                    used_model = config.OPENAI_MODEL
                except Exception as oa_err:
                    logger.warning(f"Aviso: OpenAI {config.OPENAI_MODEL} falló ({oa_err}). Probando fallback OpenAI {config.OPENAI_FALLBACK_MODEL}...")
                    try:
                        oa_resp = oa_client.chat.completions.create(
                            model=config.OPENAI_FALLBACK_MODEL,
                            messages=oa_msgs,
                            temperature=0.5
                        )
                        msg = oa_resp.choices[0].message
                        final_text = (msg.content or "").strip()
                        used_model = config.OPENAI_FALLBACK_MODEL
                    except Exception as fb_err:
                        logger.error(f"Error en OpenAI fallback {config.OPENAI_FALLBACK_MODEL}: {fb_err}")
            if not final_text and config.GEMINI_API_KEY:
                full_prompt = user_message
                if history_messages:
                    hist_text = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history_messages)
                    full_prompt = f"HISTORIAL DE CONVERSACIÓN:\n{hist_text}\n\nMENSAJE DEL CREADOR:\n{user_message}"

                models_to_try = ["gemini-3.5-flash", "gemini-2.5-flash-lite", config.ORCHESTRATOR_MODEL, "gemini-flash-lite-latest"]
                for model_name in models_to_try:
                    try:
                        resp = self.client.models.generate_content(
                            model=model_name,
                            contents=full_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.5,
                            )
                        )
                        if hasattr(resp, "text") and resp.text:
                            final_text = resp.text.strip()
                        elif getattr(resp, "candidates", None):
                            cand = resp.candidates[0]
                            parts = getattr(getattr(cand, "content", None), "parts", []) or []
                            for p in parts:
                                if getattr(p, "text", None):
                                    final_text += p.text
                            final_text = final_text.strip()
                        if final_text:
                            used_model = model_name
                            tokens_in = getattr(resp.usage_metadata, "prompt_token_count", 100) or 100
                            tokens_out = getattr(resp.usage_metadata, "candidates_token_count", 50) or 50
                            break
                    except Exception as gem_err:
                        logger.warning(f"Aviso: Gemini modelo {model_name} no disponible ({gem_err}). Probando siguiente...")

            if not final_text:
                final_text = "¿Hacia dónde sientes que debe ir esta idea ahora? Cuéntamelo en un audio de 20 segundos y lo aterrizamos."

            # Limpiar cualquier residuo de formato corporativo no deseado y nombres de funciones filtrados
            final_text = re.sub(r'\b(consultar_piezas_creador|consultar_posts_instagram|consultar_perfil_creador|guardar_identidad_creador|guardar_guion_terminado|actualizar_memoria_activa|redactar_guion_formato_oficial)\b', '', final_text)
            final_text = re.sub(r'^[-\*_]{3,}\s*$', '', final_text, flags=re.MULTILINE)
            final_text = re.sub(r'^(#{1,6})\s+', '', final_text, flags=re.MULTILINE)
            final_text = re.sub(r'\n{3,}', '\n\n', final_text).strip()

            latency = int((time.time() - start_time) * 1000)

            self.telemetry.log_turn(
                phase="routing",
                model_name=used_model,
                prompt_tokens=tokens_in,
                completion_tokens=tokens_out,
                latency_ms=latency,
                user_id=user_id,
                thread_id=thread_id,
                channel=channel,
                status="success"
            )

            log_event(
                logger,
                logging.INFO,
                event="orchestrator_turn_completed",
                message=f"Turno completado con {used_model} en {latency}ms",
                model=used_model,
                latency_ms=latency,
                user_id=user_id,
                channel=channel
            )

            # Purga defensiva de cierres serviles o tímidos
            if "¿te gustaría" in final_text.lower() or "¿quieres que" in final_text.lower():
                final_text = re.sub(r'¿te gustaría[^?\n]*\??', '¿Cómo lo ves para avanzar?', final_text, flags=re.IGNORECASE)
                final_text = re.sub(r'¿quieres que[^?\n]*\??', '¿Cómo lo ves para avanzar?', final_text, flags=re.IGNORECASE)

            return final_text

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_event(
                logger,
                logging.ERROR,
                event="orchestrator_turn_failed",
                message=f"Error en RICK Orchestrator: {e}",
                error_type=type(e).__name__,
                error_message=str(e),
                latency_ms=latency,
                user_id=user_id,
                channel=channel
            )
            try:
                self.telemetry.log_turn(
                    phase="routing",
                    model_name=used_model if 'used_model' in locals() else "unknown",
                    prompt_tokens=tokens_in if 'tokens_in' in locals() else 0,
                    completion_tokens=tokens_out if 'tokens_out' in locals() else 0,
                    latency_ms=latency,
                    user_id=user_id,
                    thread_id=thread_id,
                    channel=channel,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
            except Exception:
                pass
            return "Siento una ligera interferencia en la mesa. Cuéntame de nuevo qué idea tienes y la aterrizamos juntos."
