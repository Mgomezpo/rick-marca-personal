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

        # 0. DETECCIÓN E INVESTIGACIÓN ACTIVA DE HUELLA DIGITAL
        detected_handle = self.instagram.extract_handle(user_message)
        if not detected_handle:
            # Si el usuario solo escribió su usuario directo (ej: 'miguel_gomezpo')
            first_word = user_message.strip().split()[0].lstrip("@,;:. ") if user_message.strip() else ""
            if len(first_word) >= 3 and re.match(r'^[a-zA-Z0-9._]{3,30}$', first_word) and first_word.lower() not in ["start", "reset", "help", "hola", "si", "no", "bien", "ok", "dale", "gracias"]:
                detected_handle = first_word

        current_handle = detected_handle or answers.get("instagram_handle")
        if not current_handle:
            user_profile = self.db.get_user_profile(user_id) or {}
            current_handle = user_profile.get("analytics_username")

        # Si tenemos handle pero aún no se ha investigado su huella digital:
        if current_handle and not answers.get("footprint_summary"):
            logger.info(f"🔍 [CreatorInterviewer] Investigando huella digital de @{current_handle} antes de responder...")
            footprint = self.instagram.research_creator_footprint(current_handle)
            if footprint.get("summary"):
                answers["footprint_summary"] = footprint["summary"]
                answers["instagram_handle"] = current_handle
                self.db.upsert_user_profile(user_id, {
                    "analytics_username": current_handle,
                    "backstory": footprint["summary"][:500]
                })

        # PRIMER CONTACTO (Estilo Stanley / Head of Content):
        # Si aún no tenemos redes registradas ni investigación de huella, presentarse con autoridad ejecutiva
        if not current_handle and not answers.get("footprint_summary"):
            welcome_reply = (
                "¡Ey! Soy RICK, tu nuevo Head of Content. Hago crecer tu audiencia estudiando lo que publicas y haciendo el trabajo real 📈\n\n"
                "Tu prueba corre por mi cuenta. Después acordamos juntos qué quieres que maneje y cuánto vale eso.\n\n"
                "¿Cuáles son tus redes? Déjame ver qué has estado haciendo 📲"
            )
            answers["inquiry_step"] = 0
            state["inquiry_answers"] = answers
            try:
                self.db.update_active_memory(user_id, state=state)
            except Exception as e:
                logger.warning(f"Aviso actualizando memoria activa en primer contacto: {e}")
            return welcome_reply, False

        # 1. Cargar contexto acumulado previo del perfil y memoria viva
        user_profile = self.db.get_user_profile(user_id) or {}
        known_context = {
            "instagram_handle": answers.get("instagram_handle") or user_profile.get("analytics_username"),
            "footprint_investigation": answers.get("footprint_summary"),
            "inquiry_step": answers.get("inquiry_step", 0),
            "obsession": answers.get("obsession") or user_profile.get("passion"),
            "common_enemy": answers.get("common_enemy") or user_profile.get("unique_angle"),
            "origin_story": answers.get("origin_story"),
            "voice_tone": answers.get("voice_tone"),
            "target_audience": answers.get("target_audience") or user_profile.get("target_audience"),
        }
        active_known = {k: v for k, v in known_context.items() if v is not None and str(v).lower() not in ["null", "none"]}

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
            "Tu misión es descubrir quién es este creador, ganarte su respeto con criterio ejecutivo y calibrar su cerebro y su voz real.\n\n"
            "### METODOLOGÍA OFICIAL (CREATOR-INTERVIEW — EL MÉTODO RUBIN):\n"
            f"{skill_doc}\n\n"
            "### LAS 4 ETAPAS DEL FLUJO DE ESTUDIO:\n"
            "1. ETAPA 1: PRIMER CONTACTO (Sin redes registradas aún):\n"
            "   - Si el creador entra por primera vez o no ha dado sus redes, preséntate como su Head of Content en 2 frases directas y pídele su cuenta de Instagram (@usuario) o web para ver qué ha estado haciendo.\n\n"
            "2. ETAPA 2: RADIOGRAFÍA DE AUTORIDAD + PREGUNTA DE TRINCHERA:\n"
            "   - SE ACTIVA cuando ya se investigó su huella digital ('footprint_investigation') y 'inquiry_step' es 0:\n"
            "     a) Radiografía de Autoridad: Resume quién es, qué construye y cómo se posiciona a partir ÚNICAMENTE de los datos reales encontrados en su huella (sin inventar datos).\n"
            "     b) Diagnóstico Honesto: Señala con criterio qué le funciona mejor (pruebas tangibles, vivencias reales) vs qué se siente genérico o desaprovechado.\n"
            "     c) Pregunta Quirúrgica #1: Lanza UNA SOLA pregunta viva, humana y concreta sobre alguna historia, caso real o proyecto descubierto en su huella para entender su material en bruto. Invítalo a responder en texto o audio.\n"
            "   - En extracted_profile marca 'inquiry_step': 1.\n\n"
            "3. ETAPA 3: ESCUCHA PROFUNDA + QUIEBRE COGNITIVO (EL ENEMIGO COMÚN):\n"
            "   - SE ACTIVA cuando el creador responde la pregunta #1 compartiendo su anécdota o experiencia:\n"
            "     a) Escucha profunda: Refleja en 1 frase certera el valor y la tensión de lo que acaba de contar.\n"
            "     b) Pregunta Quirúrgica #2: Lanza UNA SOLA pregunta sobre el dogma, cliché o mentira de su industria que más rabia le da y que combate con su trabajo práctico.\n"
            "   - En extracted_profile marca 'inquiry_step': 2.\n\n"
            "4. ETAPA 4: SÍNTESIS DE ADN Y GRADUACIÓN A PRODUCCIÓN:\n"
            "   - SE ACTIVA cuando el creador responde la pregunta sobre su enemigo común:\n"
            "     a) Síntesis de estudio: Refleja en 2-3 frases limpias su verdad de trinchera, su postura y a quién le habla. PROHIBIDO inventar metas numéricas (nada de 'hacia los 10k seguidores' a menos que el creador lo haya pedido), PROHIBIDO inventar calendarios ficticios ('jueves a las 10am', '3 posts por semana') y PROHIBIDO usar jerga técnica innecesaria (nada de 'beats', 'funnels', etc.).\n"
            "     b) Pase directo a la acción: Proponle aterrizar de inmediato esa verdad en su primer guion oficial a partir de la historia que acaba de compartir.\n"
            "     c) Cierre natural: '¿Le damos forma al primer guion ahora mismo?'\n"
            "   - Marca 'is_onboarding_complete': true.\n\n"
            "### REGLAS INFLEXIBLES:\n"
            "- NUNCA hagas más de UNA sola pregunta por turno.\n"
            "- NUNCA prometas 'voy a revisar tu perfil y te escribo después' ni 'pronto te haré una pregunta'. Telegram no envía mensajes asíncronos sin un trigger del usuario. Debes entregar tu radiografía y la pregunta de turno EN ESTE MISMO MENSAJE.\n"
            "- Cero tono de autoayuda barata o coaching motivacional. Eres un Head of Content de élite en la mesa de estudio con Rick Rubin.\n"
            "- Habla en español natural, cercano, de colega a socio, sin poses corporativas.\n\n"
            "### REGLAS DE EXTRACCIÓN (OBLIGATORIAS EN EL JSON):\n"
            "- Si el creador comparte una anécdota, escena o vivencia real (como la automatización de su papá, un cliente, etc.), sintetízala OBLIGATORIAMENTE en 'origin_story'.\n"
            "- Si el creador menciona la mentira, cliché o dogma que combate, sintetízala OBLIGATORIAMENTE en 'common_enemy'.\n"
            "- Si el creador habla de su enfoque o estilo, sintetízalo en 'voice_tone'.\n\n"
            "### FORMATO DE SALIDA:\n"
            "Debes responder EXCLUSIVAMENTE un objeto JSON válido con la siguiente estructura:\n"
            "{\n"
            "  \"reply\": \"Tu mensaje directo al creador en primera persona\",\n"
            "  \"extracted_profile\": {\n"
            "    \"instagram_handle\": \"handle sin @ si fue mencionado o corregido, o null\",\n"
            "    \"inquiry_step\": 1,\n"
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
            # Step
            if "inquiry_step" in extracted_data and extracted_data["inquiry_step"] is not None:
                try:
                    answers["inquiry_step"] = int(extracted_data["inquiry_step"])
                except Exception:
                    pass

            # A. Instagram Handle
            raw_h = extracted_data.get("instagram_handle")
            if raw_h and isinstance(raw_h, str):
                clean_h = raw_h.strip().lstrip("@,;:. ")
                if clean_h and clean_h.lower() not in ["null", "none"]:
                    answers["instagram_handle"] = clean_h
                    self.db.upsert_user_profile(user_id, {"analytics_username": clean_h})

            # B. Obsesión Central
            obs = extracted_data.get("obsession")
            if obs and isinstance(obs, str) and obs.strip().lower() not in ["null", "none"]:
                answers["obsession"] = obs.strip()
                self.db.upsert_user_profile(user_id, {"passion": obs.strip()[:200]})

            # C. Enemigo Común / Quiebre Cognitivo
            enemy = extracted_data.get("common_enemy")
            if enemy and isinstance(enemy, str) and enemy.strip().lower() not in ["null", "none"]:
                answers["common_enemy"] = enemy.strip()
                self.db.upsert_user_profile(user_id, {
                    "unique_angle": enemy.strip()[:200],
                    "why": enemy.strip()[:200]
                })

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
                self.db.upsert_brand_asset(
                    user_id=user_id,
                    slot_type="lore",
                    content={"origin_story": lore.strip()},
                    summary=f"Escena de trinchera: {lore.strip()[:100]}...",
                    status="ready"
                )
                self.db.upsert_user_profile(user_id, {"backstory": lore.strip()[:500]})

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
                "main_niche": answers.get("obsession", "Creador y Estratega de IA")[:100],
                "unique_angle": answers.get("common_enemy", "Práctica de trinchera vs teoría")[:200]
            })
            state["onboarding_completed"] = True
            state["active_topic"] = "Producción de Guiones"
            self.db.update_active_memory(
                user_id=user_id,
                state=state,
                summary="Onboarding y calibración completados. Radiografía y ADN del creador asentados en Supabase."
            )
        else:
            state["onboarding_completed"] = False
            self.db.update_active_memory(
                user_id=user_id,
                state=state,
                summary="Entrevista y calibración con el creador en curso."
            )

        return reply_text, is_complete
