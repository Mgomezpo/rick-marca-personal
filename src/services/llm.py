"""Unified LLM service supporting Gemini, OpenAI, and deterministic mock mode for tests."""
import os
import json
import logging
from typing import Optional, List, Dict, Any
from src.graph.state import StrategistReasoning

logger = logging.getLogger("rick.services.llm")


class LLMService:
    """
    Unified LLM caller for RICK Multitenant Engine.
    Handles dynamic model selection, fallback, and zero-cost mock execution during tests.
    """

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.orchestrator_model = os.getenv("ORCHESTRATOR_MODEL", "gpt-4o")
        self.writer_model = os.getenv("WRITER_MODEL", "gpt-4o")

        self._openai_client = None
        self._gemini_client = None

        if self.openai_key:
            try:
                import openai
                self._openai_client = openai.OpenAI(api_key=self.openai_key)
            except Exception as e:
                logger.warning(f"Could not init OpenAI client: {e}")

        if self.gemini_key:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.warning(f"Could not init Gemini client: {e}")

    @property
    def is_test_env(self) -> bool:
        """Dynamically detect test environment or explicit mock override."""
        return (
            os.getenv("APP_ENV") == "test"
            or os.getenv("MOCK_LLM", "false").lower() == "true"
            or "PYTEST_CURRENT_TEST" in os.environ
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
        model: Optional[str] = None,
        force_mock: bool = False,
    ) -> str:
        """Generate text completion from LLM with graceful fallbacks."""
        target_model = model or self.writer_model or self.default_model

        # Fast mock path for unit testing and offline development
        if force_mock or self.is_test_env:
            return self._mock_completion(prompt, system_prompt)

        # 1. Try OpenAI if configured
        if self._openai_client:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                res = self._openai_client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if res.choices and res.choices[0].message.content:
                    return res.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}. Attempting fallback...")

        # 2. Try Gemini fallback
        if self._gemini_client:
            try:
                from google.genai import types
                gemini_model = "gemini-2.5-flash"
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
                res = self._gemini_client.models.generate_content(
                    model=gemini_model,
                    contents=prompt,
                    config=config,
                )
                if res.text:
                    return res.text.strip()
            except Exception as e:
                logger.error(f"Gemini fallback generation failed: {e}")

        # 3. Last-resort contextual fallback
        return self._mock_completion(prompt, system_prompt)

    def _mock_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Deterministic mock response for fast, offline unit testing.
        Extracts user intent and message to simulate Stanley-level intelligence without API calls.
        """
        user_msg = prompt
        if "ÚLTIMO MENSAJE DEL CREADOR: '" in prompt:
            try:
                user_msg = prompt.split("ÚLTIMO MENSAJE DEL CREADOR: '", 1)[1].split("'", 1)[0]
            except Exception:
                user_msg = prompt

        u_lower = user_msg.lower()

        # Meta question: architecture, how it works, why not chatgpt
        if "chatgpt" in u_lower or "claude" in u_lower or "como funcionas" in u_lower or "cómo funcionas" in u_lower or "arquitectura" in u_lower:
            return (
                "la diferencia con chatgpt o claude es que ellos no tienen tu contexto vivo. "
                "si les pides un guion, te dan un ensayo con subtítulos corporativos y frases como 'en este mundo cambiante'. "
                "yo tengo tus 5 historias reales en memoria: desde cuando automatizaste en 30 minutos el excel de la clínica de tu papá para devolverle los domingos, "
                "hasta la creación cívica de ayudasismo y el aprendizaje de handoff.md. cada gancho que armamos parte de lo que ya viviste, no de un playbook clónico.\n\n"
                "¿quieres que bajemos esa primera pieza hoy?"
            )

        # Haggling / pricing / reset
        if "precio" in u_lower or "1 dolar" in u_lower or "$1" in u_lower or "regateo" in u_lower:
            return (
                "jajaja buen intento, pero mi trabajo no es venderte humo por un dólar. "
                "un solo reel bien colocado que te posicione como la voz técnica de referencia en tu nicho vale cien veces más que cualquier suscripción de juguete. "
                "además, los números de tus referentes demuestran que los casos reales y los resultados convierten, no los descuentos.\n\n"
                "¿te parece si dejamos el regateo y armamos la pieza de la semana?"
            )

        # Blank mind / blocked creator (Heavy Lifting by RICK)
        if "mente en blanco" in u_lower or "bloqueado" in u_lower or "bloqueada" in u_lower or "sin ideas" in u_lower:
            return (
                "tranquilo, no tienes que inventar nada de cero hoy. ya tienes historias reales listas para grabar:\n\n"
                "1. por qué seguir playbooks de marketing mata tu voz (la razón exacta por la que decidiste construir a rick e ireal).\n"
                "2. la automatización de 30 minutos con macros de excel para la clínica dental de tu papá para devolverle los domingos.\n\n"
                "dime cuál te vibra más y yo hago el trabajo pesado de estructurar el gancho visual y el quiebre."
            )

        # Multi-point / saga detection in user story
        if ("dos errores" in u_lower or "2 errores" in u_lower or "varias lecciones" in u_lower or "múltiples" in u_lower) and not ("una sola" in u_lower or "saga" in u_lower):
            return "¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?"

        # Story extraction: missing scene or friction
        if "reunión" in u_lower or "reunion" in u_lower or "oficina" in u_lower or "cliente" in u_lower:
            if "error" in u_lower or "fricción" in u_lower or "friccion" in u_lower:
                return "¿Quieres que montemos el guion sobre este quiebre?"
            return "¿Cuál fue el error o la fricción que nadie vio en esa decisión?"

        if "lanzamiento" in u_lower or "quebró" in u_lower or "desesperé" in u_lower or "negocio" in u_lower:
            return "¿Qué pasó exactamente en ese momento? Cuéntame la escena sin adornos."

        # Script request
        if "guion" in u_lower or "script" in u_lower or "armemos" in u_lower or "escribe" in u_lower:
            return (
                "aquí tienes la estructura lista para grabar:\n\n"
                "**visual hook (en pantalla):**\n"
                "automatizar con 10 agentes es una trampa.\n\n"
                "**spoken hook (lo que dices):**\n"
                "le armé a mi papá una automatización de 30 minutos para su clínica dental y le devolví los domingos. "
                "mientras tanto, veo empresas quemando miles de dólares en agentes que nadie usa.\n\n"
                "**el quiebre:**\n"
                "a tu cliente no le importa tu stack de herramientas; le importa recuperar su tiempo libre. "
                "si no puedes explicar el alivio en una servilleta, ningún software lo va a salvar por ti.\n\n"
                "**cierre:**\n"
                "antes de gastar en escalar, asegúrate de que tienes algo que funciona cuando estás tú solo."
            )

        # General greeting or open dialogue
        return (
            "Buen día. En el equipo tenemos los referentes y números al día. "
            "¿Qué problema o anécdota real con clientes trabajamos hoy para el canal?"
        )

    def think_and_route(
        self,
        prompt: str,
        story_bank: Optional[List[Any]] = None,
        current_intent: str = "chat",
    ) -> StrategistReasoning:
        """
        Orchestrator reasoning step: Generates structured internal monologue (StrategistReasoning).
        In live environments, uses orchestrator_model (temp=0.2) to evaluate subtext, clichés to avoid,
        and contrarian angles.
        In test environments or on failure, falls back to deterministic mock reasoning.
        """
        if self.is_test_env:
            return self._mock_think_and_route(prompt, story_bank, current_intent)

        receipts_ctx = ""
        if story_bank:
            receipts_ctx = "\n".join(
                [f"- ID: {getattr(r, 'id', str(i))} | Tema: {getattr(r, 'theme', '')} | Resumen: {getattr(r, 'summary', '')}" 
                 for i, r in enumerate(story_bank)]
            )

        reasoning_prompt = (
            "Eres el Estratega Principal de Contenido (RICK). Analiza el mensaje del creador y su banco de historias.\n"
            "Devuelve un JSON estrictamente estructurado con las siguientes claves:\n"
            "- user_subtext (str): Qué intenta expresar o qué dolor/bloqueo real tiene el creador.\n"
            "- cliche_trap_to_avoid (str): Qué respuesta genérica, tibia o cliché de IA debemos prohibir en este turno.\n"
            "- selected_receipt_id (str o null): ID del recibo más relevante del banco para anclar la respuesta.\n"
            "- contrarian_angle (str): Tesis o postura contraria que evita lugares comunes.\n"
            "- has_concrete_scene (bool): Si la historia compartida ya tiene una escena tangible.\n"
            "- has_root_friction (bool): Si ya tiene el error, quiebre o fricción raíz.\n"
            "- is_multipoint_story (bool): Si la historia tiene múltiples puntos para sugerir saga.\n"
            "- routed_intent (str): chat, extract_story, generate_script, view_report, cold_onboarding, blocked_creator, meta_question.\n\n"
            f"BANCO DE HISTORIAS:\n{receipts_ctx or 'Ninguno aún'}\n\n"
            f"INTENCIÓN PREVIA: {current_intent}\n"
            f"MENSAJE A ANALIZAR:\n{prompt}\n\n"
            "Devuelve ÚNICAMENTE el objeto JSON sin bloques de markdown adicionales:"
        )

        # 1. Try OpenAI if configured
        if self._openai_client:
            try:
                res = self._openai_client.chat.completions.create(
                    model=self.orchestrator_model,
                    messages=[
                        {"role": "system", "content": "Devuelve exclusivamente un objeto JSON válido."},
                        {"role": "user", "content": reasoning_prompt},
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                if res.choices and res.choices[0].message.content:
                    data = json.loads(res.choices[0].message.content)
                    return StrategistReasoning(**data)
            except Exception as e:
                logger.warning(f"OpenAI think_and_route failed: {e}. Falling back...")

        # 2. Try Gemini if configured
        if self._gemini_client:
            try:
                from google.genai import types
                config = types.GenerateContentConfig(
                    system_instruction="Devuelve exclusivamente un objeto JSON válido.",
                    temperature=0.2,
                    response_mime_type="application/json",
                )
                res = self._gemini_client.models.generate_content(
                    model=self.orchestrator_model,
                    contents=reasoning_prompt,
                    config=config,
                )
                if res.text:
                    data = json.loads(res.text)
                    return StrategistReasoning(**data)
            except Exception as e:
                logger.warning(f"Gemini think_and_route failed: {e}. Falling back...")

        return self._mock_think_and_route(prompt, story_bank, current_intent)

    def _mock_think_and_route(
        self,
        prompt: str,
        story_bank: Optional[List[Any]] = None,
        current_intent: str = "chat",
    ) -> StrategistReasoning:
        """Deterministic reasoning generation for tests and fast offline execution."""
        user_msg = prompt
        if "ÚLTIMO MENSAJE DEL CREADOR: '" in prompt:
            try:
                user_msg = prompt.split("ÚLTIMO MENSAJE DEL CREADOR: '", 1)[1].split("'", 1)[0]
            except Exception:
                user_msg = prompt

        u_lower = user_msg.lower().strip()
        first_receipt_id = story_bank[0].id if (story_bank and len(story_bank) > 0 and hasattr(story_bank[0], 'id')) else None

        # Blocked creator / blank mind
        block_markers = ["mente en blanco", "bloqueado", "bloqueada", "sin ideas", "cero ideas", "no se me ocurre nada"]
        if any(b in u_lower for b in block_markers) or ("no sé qué decir" in u_lower or "no sé qué grabar" in u_lower):
            return StrategistReasoning(
                user_subtext="El creador está bloqueado creativamente y necesita que RICK proponga opciones concretas de su lore.",
                cliche_trap_to_avoid="Decir 'no te preocupes, piensa en tus pasiones' o hacer preguntas abiertas vagas.",
                selected_receipt_id=first_receipt_id or "rec_excel_papa",
                contrarian_angle="El contenido que mejor convierte no se inventa de la nada: se extrae de tus cicatrices operativas.",
                has_concrete_scene=False,
                has_root_friction=False,
                is_multipoint_story=False,
                routed_intent="blocked_creator",
            )

        # Meta question
        meta_markers = ["chatgpt", "claude", "como funcionas", "cómo funcionas", "tu arquitectura", "1 dolar", "precio", "regateo", "descuento", "$1"]
        if any(m in u_lower for m in meta_markers):
            return StrategistReasoning(
                user_subtext="Cuestionamiento sobre la diferenciación de RICK frente a ChatGPT o el valor de la suscripción.",
                cliche_trap_to_avoid="Sonar como bot corporativo diciendo 'fui diseñado para ayudarte a crear contenido'.",
                selected_receipt_id=first_receipt_id,
                contrarian_angle="Un LLM genérico te da ensayos con subtítulos; RICK opera sobre tus anécdotas vividas.",
                has_concrete_scene=False,
                has_root_friction=False,
                is_multipoint_story=False,
                routed_intent="meta_question",
            )

        # Generate script
        script_keywords = ["guion", "guión", "script", "escribe", "escribeme", "redacta", "armemos el guion", "armar el guion", "una sola", "sola pieza", "saga", "2 partes"]
        if any(k in u_lower for k in script_keywords):
            return StrategistReasoning(
                user_subtext="El creador está listo para estructurar el guion técnico de grabación.",
                cliche_trap_to_avoid="Ganchos genéricos con saludos de 'hola a todos' o introducciones lentas.",
                selected_receipt_id=first_receipt_id,
                contrarian_angle="El contraste visual-hablado en el segundo cero detiene el scroll mejor que cualquier promesa exagerada.",
                has_concrete_scene=True,
                has_root_friction=True,
                is_multipoint_story=False,
                routed_intent="generate_script",
            )

        # Multi-point / saga
        multi_markers = ["dos errores", "2 errores", "tres errores", "varias lecciones", "múltiples", "dos partes", "2 partes"]
        is_multi = any(m in u_lower for m in multi_markers)

        # Scene and friction markers
        scene_markers = ["reunión", "reunion", "oficina", "llamada", "ayer", "pantalla", "cliente", "lanzamiento", "negocio", "quebró"]
        friction_markers = ["error", "errores", "fricción", "friccion", "no validé", "quebró", "desesperé", "problema", "lección"]
        has_scene = any(w in u_lower for w in scene_markers)
        has_friction = any(w in u_lower for w in friction_markers)

        if has_scene or has_friction or len(u_lower.split()) >= 10:
            return StrategistReasoning(
                user_subtext="El creador está relatando una anécdota o dolor de negocio que encierra una tesis de autoridad.",
                cliche_trap_to_avoid="Validar con adulación vacía tipo '¡Excelente experiencia! Seguro tus seguidores aprenderán mucho'.",
                selected_receipt_id=first_receipt_id,
                contrarian_angle="El error operativo específico enseña más y genera más autoridad que un caso de éxito adornado.",
                has_concrete_scene=has_scene,
                has_root_friction=has_friction,
                is_multipoint_story=is_multi,
                routed_intent="extract_story",
            )

        # View report
        if any(k in u_lower for k in ["reporte", "métrica", "metrica", "estadística", "analytics", "rendimiento"]):
            return StrategistReasoning(
                user_subtext="Solicitud de diagnóstico o métricas de rendimiento.",
                cliche_trap_to_avoid="Reportar métricas de vanidad (likes o seguidores) sin correlación con retención.",
                selected_receipt_id=first_receipt_id,
                contrarian_angle="Solo medimos retención real y rendimiento relativo sobre tu mediana.",
                has_concrete_scene=False,
                has_root_friction=False,
                is_multipoint_story=False,
                routed_intent="view_report",
            )

        # Cold onboarding
        if "@" in u_lower:
            return StrategistReasoning(
                user_subtext="Usuario nuevo compartiendo su handle de Instagram para escanear historias.",
                cliche_trap_to_avoid="Dar un discurso largo de bienvenida sin escanear ni pasar a la acción.",
                selected_receipt_id=None,
                contrarian_angle="Tu archivo de contenido ya tiene el oro de tu posicionamiento.",
                has_concrete_scene=False,
                has_root_friction=False,
                is_multipoint_story=False,
                routed_intent="cold_onboarding",
            )

        # Default chat
        return StrategistReasoning(
            user_subtext="Saludo inicial o comentario general.",
            cliche_trap_to_avoid="Responder como bot de soporte '¿En qué puedo asistirte hoy?'",
            selected_receipt_id=first_receipt_id,
            contrarian_angle="Socio de contenido en la mesa listo para desarmar objeciones y bajar piezas.",
            has_concrete_scene=False,
            has_root_friction=False,
            is_multipoint_story=False,
            routed_intent="chat",
        )


llm_service = LLMService()
