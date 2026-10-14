import logging
import json
import time
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from src.core.config import config
from src.core.telemetry import TelemetryTracker
from src.db.supabase import DatabaseService
from src.engine.vfs import VirtualFileSystem
from src.engine.tools import OPENAI_TOOLS, execute_tool_call
from src.engine.skills_loader import skills_loader
from src.engine.subagents.creator_interviewer import CreatorInterviewerSubagent

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
        base = "Te llamas RICK. Eres el Productor Ejecutivo y Head of Content basado en el criterio de Rick Rubin."

    # Inyectar Principios Canónicos de Rubin y Árbol de Decisión de Estudio
    reduction_doc = skills_loader.get_brain_doc("01_philosophy/principles/reduction.md")
    beginner_doc = skills_loader.get_brain_doc("01_philosophy/principles/beginner_mind.md")
    synthesis_doc = skills_loader.get_brain_doc("01_philosophy/principles/synthesis.md")
    decision_tree = skills_loader.get_brain_doc("03_studio/frameworks/decision_tree.md")

    brain_injections = []
    if reduction_doc:
        brain_injections.append(f"### PRINCIPIO RUBIN — LA REDUCCIÓN AL ESENCIAL:\n{reduction_doc}")
    if beginner_doc:
        brain_injections.append(f"### PRINCIPIO RUBIN — MENTE DE PRINCIPIANTE:\n{beginner_doc}")
    if synthesis_doc:
        brain_injections.append(f"### PRINCIPIO RUBIN — SÍNTESIS DIGITAL:\n{synthesis_doc}")
    if decision_tree:
        brain_injections.append(f"### ÁRBOL DE DECISIÓN HEURÍSTICO DEL ESTUDIO (PSYCHOLOGY & FRAMEWORKS):\n{decision_tree}")

    if brain_injections:
        base += "\n\n---\n\n## 🧠 CEREBRO VIVO DE RICK (FILOSOFÍA CANÓNICA Y FRAMEWORKS DE ESTUDIO):\n" + "\n\n".join(brain_injections)

    return base

class RickOrchestrator:
    def __init__(self, db: DatabaseService):
        self.db = db
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.telemetry = TelemetryTracker(self.db.client)
        self.vfs = VirtualFileSystem(self.db)
        self.base_system_prompt = load_master_system_prompt()
        self.interviewer = CreatorInterviewerSubagent(self.client, self.db, self.telemetry)

    def process_message(
        self,
        user_message: str,
        user_id: str,
        channel: str = "whatsapp",
        thread_id: Optional[str] = None
    ) -> str:
        """
        Ejecuta el ciclo de RICK como Head of Content:
        1. Si el creador no ha completado el onboarding socrático (Método Rubin),
           enruta al CreatorInterviewerSubagent (skills/creator-interview).
        2. Si ya está consolidado en el estudio, orquesta con Function Calling real
           ejecutando el pipeline de producción (HookWriter -> Guionista -> Humanizer).
        """
        start_time = time.time()
        logger.info(f"🎙️ [RICK Orchestrator] Mensaje de usuario {user_id}: '{user_message[:60]}...'")

        # 1. Estado de memoria Tier-1 y VFS
        active_mem = self.db.get_active_memory(user_id)
        mem_state = active_mem.get("state") or {}
        inquiry_step = mem_state.get("inquiry_step", 0)
        onboarding_completed = mem_state.get("onboarding_completed", False)

        voice_dna_md = self.vfs.read_file("creator/identity/voice_dna.md", user_id)
        positioning_md = self.vfs.read_file("creator/identity/positioning.md", user_id)
        lore_md = self.vfs.read_file("creator/lore/origin_stories.md", user_id)
        active_ctx_md = self.vfs.read_file("memorias/active_context.md", user_id)
        recent_scripts_md = self.vfs.read_file("produccion/scripts", user_id)

        has_voice = bool(voice_dna_md and "sin voz registrada" not in voice_dna_md.lower() and "[pendiente_de_entrevista]" not in voice_dna_md.lower() and len(voice_dna_md.strip()) > 20)
        has_niche = bool(positioning_md and "sin nicho registrado" not in positioning_md.lower() and "[pendiente_de_entrevista]" not in positioning_md.lower() and len(positioning_md.strip()) > 20)
        profile = self.db.get_user_profile(user_id) or {}
        is_onboarded = bool(onboarding_completed or (profile.get("onboarding_status") == "completed"))

        # 2. ENRUTAMIENTO SOCRÁTICO DE ONBOARDING (skills/creator-interview)
        if not is_onboarded:
            logger.info(f"🎙️ [Orchestrator] Enrutando a CreatorInterviewerSubagent (LLM Rubin) para {user_id}")
            reply, is_done = self.interviewer.process_turn(user_message, user_id, active_mem, thread_id=thread_id)
            latency = int((time.time() - start_time) * 1000)
            self.telemetry.log_turn(
                phase="routing",
                model_name=config.ORCHESTRATOR_MODEL,
                prompt_tokens=100,
                completion_tokens=100,
                latency_ms=latency,
                user_id=user_id,
                thread_id=thread_id,
                channel=channel
            )
            return reply

        # Base de contexto viva del Creador (disponible en la mesa de estudio)
        context_block = (
            f"### RADIOGRAFÍA Y LORE DEL CREADOR (MULTI-TENANT):\n{lore_md}\n\n"
            f"### ADN DE VOZ Y POSICIONAMIENTO:\n{voice_dna_md}\n\n{positioning_md}\n\n"
            f"### MEMORIA ACTIVA Y ESTADO ACTUAL:\n{active_ctx_md}\n\n"
            f"### GUIONES Y PIEZAS EN LA MESA:\n{recent_scripts_md}\n\n"
        )

        if not is_onboarded:
            context_block += (
                "### ESTADO DEL CREADOR: EN PROCESO DE DEFINICIÓN / ONBOARDING ACTIVO\n"
                "El creador te acaba de hacer una pregunta sobre quién eres o qué sabes de él.\n"
                "- Resume con precisión y empatía de artesano lo que te ha contado hasta ahora (sus proyectos, conocimientos técnicos o dolores como monetizar o miedo a cobrar).\n"
                "- Explícale que eres RICK, su Head of Content y guardián de criterio, inspirado en Rick Rubin. No un bot de autoayuda, sino un productor de trinchera que lo acompaña a destilar su verdad.\n"
                "- Cierra con una sola pregunta corta invitándolo a continuar la entrevista socrática para asentar su mundo.\n"
            )
        else:
            context_block += (
                "REGLA DE CONTEXTO: Habla ÚNICAMENTE desde el lore y nicho real de este creador cargado arriba. "
                "Bajo NINGUNA circunstancia inventes clientes, empresas o proyectos que no figuren en su contexto.\n"
                "- Si el creador te saluda de nuevo ('hola', 'hola Rick'): salúdalo de forma natural y cercana de colega ('¡Ey!', '¡Qué más!'), demuestra que tienes fresco su radar creativo y pregúntale qué quieren atacar hoy (guion, inventario de piezas o nueva idea).\n"
            )

        system_instruction = (
            f"{self.base_system_prompt}\n\n"
            f"---\n"
            f"{context_block}\n\n"
            f"### ESTÁNDAR OPERATIVO DE RICK (HEAD OF CONTENT + CRITERIO RUBIN):\n"
            f"1. Eres el Head of Content y Productor Creativo del creador. Tu valor está en tu criterio implacable, tu honestidad brutal y tu capacidad de destilar la verdad al hueso para hacer crecer su audiencia. CERO palmaditas condescendientes en la espalda y CERO autoayuda vacía.\n"
            f"2. Tono y cercanía de chat: Habla de tú a tú como un gran colega y director creativo por WhatsApp o Telegram. Si te saluda, salúdalo con naturalidad ('¡Ey!', '¡Qué más!'). CERO formalismos corporativos de oficina. CERO formatos pesados de reporte.\n"
            f"3. Cierre con llamada a la acción de bajo esfuerzo (Frictionless CTA): Cierra SIEMPRE con una sola pregunta concreta o una invitación a mandar un audio de 20s para avanzar.\n"
            f"4. PIPELINE OBLIGATORIO DE REDACCIÓN DE GUIONES:\n"
            f"   Cuando el creador pida redactar un guion, desarrollar una idea o armar una pieza para grabar (ej: 'hazme un guion', 'dale', 'vamos a armarlo', 'escríbemelo'), O cuando comparta la historia, vivencia o anécdota solicitada para su contenido (en texto o nota de voz):\n"
            f"   DEBES LLAMAR INMEDIATAMENTE a la herramienta `redactar_guion_formato_oficial(brief=..., framework=..., formato=...)`.\n"
            f"   El motor ejecutará el pipeline oficial de 3 fases (HookWriter con 9 arquetipos de quiebre cognitivo anclados en su anécdota -> Guionista estructurado -> Humanizer anti-slop).\n"
            f"   PROHIBIDO responder con evasivas o preguntas tímidas como '¿Te gustaría que hagamos un guion con esto?'. Si ya compartió la anécdota o pidió el guion, EJECUTA la herramienta de inmediato y preséntale el guion finalizado.\n"
            f"   PROHIBIDO redactar el guion en texto improvisado sin llamar a la herramienta.\n\n"
            f"5. USO DE HERRAMIENTAS REALES:\n"
            f"   - Si el creador pregunta por sus posts o reels de Instagram: llama a `consultar_posts_instagram`.\n"
            f"   - Si el creador pregunta por sus piezas/guiones previos guardados: llama a `consultar_piezas_creador`.\n"
            f"   - Si cambias o estableces el tema en curso: llama a `actualizar_memoria_activa`.\n"
            f"   - Si descubres nuevos datos de perfil: llama a `guardar_identidad_creador`.\n"
            f"   - Si necesitas consultar principios de Rubin o frameworks narrativos: llama a `leer_documento_cerebro` o `buscar_en_cerebro`.\n\n"
            f"6. REGLAS DE ORO ANTIALUCINACIÓN Y TONO:\n"
            f"   - NUNCA inventes posts, clientes o empresas que no existan en el contexto.\n"
            f"   - NUNCA imprimas nombres de funciones técnicas en el texto (como 'consultar_piezas_creador' o 'consultar_posts_instagram').\n"
            f"   - NUNCA imprimas plantillas con corchetes vacíos como '[Breve descripción]'.\n\n"
            f"7. PROHIBICIÓN TOTAL DE PREGUNTAS TÍMIDAS DE PERMISO:\n"
            f"   NUNCA preguntes '¿Te gustaría que...?', '¿Te parece si...?', '¿Quieres que exploremos...?'. Eres el Head of Content de élite: actúa con criterio, propone la dirección con firmeza y da instrucciones claras y directas ('Dime X y te armo el guion ya mismo')."
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
            if config.OPENAI_API_KEY:
                try:
                    logger.info(f"⚡ [Orchestrator] Ejecutando OpenAI {config.OPENAI_MODEL} con tools...")
                    import openai
                    oa_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
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
                                tool_result = execute_tool_call(
                                    tool_name=fn_name,
                                    args=fn_args,
                                    user_id=user_id,
                                    db=self.db,
                                    vfs=self.vfs,
                                    thread_id=thread_id
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
                channel=channel
            )

            return final_text

        except Exception as e:
            logger.error(f"Error en RICK Orchestrator: {e}", exc_info=True)
            return "Siento una ligera interferencia en la mesa. Cuéntame de nuevo qué idea tienes y la aterrizamos juntos."
