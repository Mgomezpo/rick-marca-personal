import logging
import json
import re
from typing import Any, Dict, Tuple, Optional, List
from google import genai
from google.genai import types
from src.core.config import config
from src.db.supabase import DatabaseService
from src.core.telemetry import TelemetryTracker
from src.services.instagram import InstagramService
from src.engine.skills_loader import skills_loader

logger = logging.getLogger("rick.subagent.interviewer")

class CreatorInterviewerSubagent:
    """
    Subagente de Entrevista al Creador (El Método Rubin):
    100% impulsado por Inteligencia Artificial conversacional (LLM).
    Sin máquinas de estado rígidas, sin contadores de pasos manuales y sin asignaciones
    hardcodeadas de texto a columnas de base de datos.

    Carga dinámicamente 'skills/creator-interview/SKILL.md'.
    Interpreta la conversación viva (mensajes de voz, anécdotas, correcciones, typos, preguntas)
    con inteligencia natural, mantiene la voz de Rick Rubin (productor de estudio honesto,
    sin clichés corporativos ni autoayuda vacía) y extrae las 5 dimensiones del creador:
    1. Obsesión Central (qué tema hablaría 3 horas seguidas con un café sin cansarte).
    2. Enemigo Común / Quiebre Cognitivo (el dogma, mentira o cliché de su industria que combate).
    3. Lore / Escena de Origen (la escena exacta, llamada o error de trinchera).
    4. ADN de Voz (cadencia relajada de colega a socio, sin poses de gurú).
    5. Audiencia Espejo (su versión de hace 1 o 2 años que necesitaba ahorrarse ese dolor).
    """

    def __init__(self, client: genai.Client, db: DatabaseService, telemetry: TelemetryTracker):
        self.client = client
        self.db = db
        self.telemetry = telemetry
        self.instagram = InstagramService()

    def process_turn(
        self,
        user_message: str,
        user_id: str,
        active_memory: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Ejecuta el turno de entrevista socrática de forma completamente conversacional vía LLM.
        Retorna (texto_respuesta, is_complete).
        """
        state = active_memory.get("state") or {}
        if "inquiry_answers" not in state or not isinstance(state["inquiry_answers"], dict):
            state["inquiry_answers"] = {}
        answers = state["inquiry_answers"]

        # 1. Cargar contexto acumulado previo del perfil y memoria viva
        user_profile = self.db.get_user_profile(user_id) or {}
        known_context = {
            "instagram_handle": answers.get("instagram_handle") or user_profile.get("analytics_username"),
            "obsession": answers.get("obsession") or user_profile.get("passion"),
            "common_enemy": answers.get("common_enemy") or user_profile.get("unique_angle"),
            "origin_story": answers.get("origin_story"),
            "voice_tone": answers.get("voice_tone"),
            "target_audience": answers.get("target_audience") or user_profile.get("target_audience"),
        }
        # Filtrar solo campos que tengan valor real
        active_known = {k: v for k, v in known_context.items() if v and str(v).lower() not in ["null", "none"]}

        # 2. Cargar historial de conversación reciente del hilo (hasta 15 mensajes)
        history_messages: List[Dict[str, str]] = []
        if thread_id:
            try:
                th = self.db.client.table("rick_threads").select("transcript").eq("id", thread_id).execute()
                if th.data and th.data[0].get("transcript"):
                    raw = th.data[0]["transcript"]
                    # Excluir el último mensaje si coincide con user_message (ya guardado en el transcript por el bot)
                    if raw and raw[-1].get("role") == "user" and raw[-1].get("content", "").strip() == user_message.strip():
                        raw = raw[:-1]
                    for m in raw[-15:]:
                        content = m.get("content", "")
                        if "interferencia en la mesa" not in content and content.strip():
                            history_messages.append({"role": m.get("role", "user"), "content": content})
            except Exception as e:
                logger.warning(f"Error cargando transcript para entrevista socrática: {e}")

        # 3. Cargar la skill oficial
        skill_doc = skills_loader.get_skill("creator-interview")

        system_instruction = (
            "Eres RICK, productor creativo y Head of Content en la mesa de estudio (inspirado en Rick Rubin y The Creative Act).\n"
            "Tu misión es descubrir quién es este creador mediante una conversación socrática orgánica, honesta y de tú a tú.\n\n"
            "### METODOLOGÍA OFICIAL (CREATOR-INTERVIEW):\n"
            f"{skill_doc}\n\n"
            "### DIMENSIONES CLAVE A SINTONIZAR (DE FORMA ORGÁNICA, NUNCA COMO UN FORMULARIO):\n"
            "1. Instagram / Terreno actual: Su cuenta de Instagram (@usuario) o lo que está construyendo hoy.\n"
            "2. La Obsesión Central: De qué tema o proyecto podría hablar 3 horas seguidas con un café sin cansarse y sin mirar notas.\n"
            "3. El Enemigo Común / Quiebre Cognitivo: Qué mentira, dogma o cliché de su industria le da rabia y quiere desarmar.\n"
            "4. El Lore / La Escena de Origen: La escena concreta, llamada o error de trinchera donde sintió esa fricción.\n"
            "5. El ADN de Voz: Cómo habla cuando le explica algo a un socio tomando un café (sin poses de gurú ni jerga corporativa).\n"
            "6. La Audiencia Espejo: A quién le habla con exactitud (casi siempre su versión de hace 1 o 2 años).\n\n"
            "### REGLAS INFLEXIBLES DE CONVERSACIÓN:\n"
            "1. UNA SOLA PREGUNTA A LA VEZ: Haz ÚNICAMENTE una sola pregunta sugerente, directa y corta (~15-25 palabras).\n"
            "2. ESCUCHA PROFUNDA: Abre SIEMPRE reflejando en 1 frase certera lo que el creador acaba de contarte antes de soltar la siguiente pregunta.\n"
            "3. CONVERSACIÓN VIVA E INTELIGENTE: Si el creador comete un typo, aclara una duda, dice 'me equivoqué, es @...', bromea o cuenta una anécdota, acéptalo con total naturalidad humana. NUNCA tomes frases de corrección o errores como si fueran su pasión o proyecto.\n"
            "4. PRIMER CONTACTO: Si el creador apenas entra al estudio o no ha dicho nada aún, dale la bienvenida al estudio en 2 frases y pídele su Instagram (@usuario) o una nota de voz sobre lo que está construyendo.\n"
            "5. CIERRE Y GRADUACIÓN: Cuando hayas cubierto con profundidad real las dimensiones clave (Obsesión, Enemigo Común, Escena/Lore y Audiencia), haz el cierre de estudio al estilo Rubin resumiendo su ADN en 3 puntos contundentes, invítalo a producir su primer guion oficial y marca 'is_onboarding_complete': true.\n\n"
            "### FORMATO DE SALIDA:\n"
            "Debes responder EXCLUSIVAMENTE un objeto JSON válido con la siguiente estructura:\n"
            "{\n"
            "  \"reply\": \"Tu mensaje directo al creador en primera persona\",\n"
            "  \"extracted_profile\": {\n"
            "    \"instagram_handle\": \"handle sin @ si fue mencionado o corregido, o null\",\n"
            "    \"obsession\": \"síntesis de su tema u obsesión central o null\",\n"
            "    \"common_enemy\": \"síntesis del dogma o mentira que combate o null\",\n"
            "    \"origin_story\": \"síntesis de la escena de trinchera o error clave o null\",\n"
            "    \"voice_tone\": \"estilo de comunicación o poses que rechaza o null\",\n"
            "    \"target_audience\": \"a quién le habla exactamente o null\"\n"
            "  },\n"
            "  \"is_onboarding_complete\": false\n"
            "}"
        )

        user_prompt = (
            f"LO QUE YA SABEMOS DEL CREADOR HASTA AHORA:\n{json.dumps(active_known, ensure_ascii=False, indent=2)}\n\n"
            f"MENSAJE ACTUAL DEL CREADOR:\n\"{user_message}\"\n\n"
            "Genera tu respuesta en JSON."
        )

        # 4. Inferencia con LLM (OpenAI con fallback automático a Google Gemini)
        reply_text = ""
        extracted_data = {}
        is_complete = False

        if config.OPENAI_API_KEY:
            try:
                import openai
                oa = openai.OpenAI(api_key=config.OPENAI_API_KEY)
                oa_msgs = [{"role": "system", "content": system_instruction}]
                for hm in history_messages:
                    oa_msgs.append({"role": hm["role"], "content": hm["content"]})
                oa_msgs.append({"role": "user", "content": user_prompt})

                resp = oa.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=oa_msgs,
                    response_format={"type": "json_object"},
                    temperature=0.6
                )
                raw_json = resp.choices[0].message.content or "{}"
                data = json.loads(raw_json)
                reply_text = data.get("reply", "").strip()
                extracted_data = data.get("extracted_profile", {})
                is_complete = bool(data.get("is_onboarding_complete", False))
            except Exception as e:
                logger.warning(f"Aviso: OpenAI falló en creator interview ({e}). Fallback a Gemini...")

        if not reply_text and config.GEMINI_API_KEY:
            try:
                gem_prompt = "HISTORIAL DE CONVERSACIÓN PREVIO:\n"
                for hm in history_messages:
                    gem_prompt += f"{hm['role'].capitalize()}: {hm['content']}\n"
                gem_prompt += f"\n{user_prompt}"

                resp = self.client.models.generate_content(
                    model=config.ORCHESTRATOR_MODEL,
                    contents=gem_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.6
                    )
                )
                data = json.loads(resp.text)
                reply_text = data.get("reply", "").strip()
                extracted_data = data.get("extracted_profile", {})
                is_complete = bool(data.get("is_onboarding_complete", False))
            except Exception as e:
                logger.error(f"Error Gemini en creator interview: {e}")

        # Fallback de seguridad si ambos LLM fallaron
        if not reply_text:
            reply_text = "Te escucho con atención en la mesa. Cuéntame un poco más sobre esa idea o proyecto que estás construyendo."

        # 5. Persistencia y actualización orgánica en Supabase
        if extracted_data and isinstance(extracted_data, dict):
            # A. Instagram Handle
            raw_h = extracted_data.get("instagram_handle")
            if raw_h and isinstance(raw_h, str):
                clean_h = raw_h.strip().lstrip("@,;:. ")
                if clean_h and clean_h.lower() not in ["null", "none"]:
                    old_h = answers.get("instagram_handle")
                    answers["instagram_handle"] = clean_h
                    self.db.upsert_user_profile(user_id, {"analytics_username": clean_h})
                    if clean_h != old_h:
                        try:
                            self.instagram.research_creator_footprint(clean_h)
                        except Exception as e:
                            logger.warning(f"Aviso investigando huella de @{clean_h}: {e}")

            # B. Obsesión Central
            obs = extracted_data.get("obsession")
            if obs and isinstance(obs, str) and obs.strip().lower() not in ["null", "none"]:
                answers["obsession"] = obs.strip()
                self.db.upsert_user_profile(user_id, {"passion": obs.strip()[:200]})

            # C. Enemigo Común / Quiebre Cognitivo
            enemy = extracted_data.get("common_enemy")
            if enemy and isinstance(enemy, str) and enemy.strip().lower() not in ["null", "none"]:
                answers["common_enemy"] = enemy.strip()
                self.db.upsert_user_profile(user_id, {"unique_angle": enemy.strip()[:200]})

            # D. Lore / Escena de Origen
            lore = extracted_data.get("origin_story")
            if lore and isinstance(lore, str) and lore.strip().lower() not in ["null", "none"]:
                answers["origin_story"] = lore.strip()
                self.db.upsert_brand_asset(
                    user_id=user_id,
                    slot_type="historia_origen",
                    content={"origin_story": lore.strip()},
                    summary=f"Escena de trinchera: {lore.strip()[:100]}...",
                    status="ready"
                )

            # E. ADN de Voz
            voice = extracted_data.get("voice_tone")
            if voice and isinstance(voice, str) and voice.strip().lower() not in ["null", "none"]:
                answers["voice_tone"] = voice.strip()
                self.db.upsert_brand_asset(
                    user_id=user_id,
                    slot_type="voz",
                    content={"vibe": voice.strip(), "obsession": answers.get("obsession", "")},
                    summary=f"Voz: {voice.strip()[:80]}",
                    status="ready"
                )

            # F. Audiencia Espejo
            aud = extracted_data.get("target_audience")
            if aud and isinstance(aud, str) and aud.strip().lower() not in ["null", "none"]:
                answers["target_audience"] = aud.strip()
                self.db.upsert_user_profile(user_id, {"target_audience": aud.strip()[:200]})
                self.db.upsert_brand_asset(
                    user_id=user_id,
                    slot_type="cliente_ideal",
                    content={"mirror_audience": aud.strip()},
                    summary=f"Audiencia espejo: {aud.strip()[:100]}",
                    status="ready"
                )

        # 6. Graduación / Finalización del Onboarding
        if is_complete:
            self.db.upsert_user_profile(user_id, {
                "onboarding_status": "completed",
                "main_niche": answers.get("obsession", "Creador y Estratega")[:100],
                "unique_angle": answers.get("common_enemy", "Práctica de trinchera vs teoría")[:200]
            })
            state["onboarding_completed"] = True
            state["active_topic"] = "Producción de Guiones"
            self.db.update_active_memory(
                user_id=user_id,
                state=state,
                summary="Onboarding socrático completado por LLM. ADN del creador asentado en Supabase."
            )
        else:
            state["onboarding_completed"] = False
            self.db.update_active_memory(
                user_id=user_id,
                state=state,
                summary="Entrevista socrática con el creador en curso."
            )

        return reply_text, is_complete
