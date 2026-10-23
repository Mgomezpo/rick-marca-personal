"""Unified LLM service supporting Gemini, OpenAI, and deterministic mock mode for tests."""
import os
import logging
from typing import Optional, List, Dict, Any

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
        self.is_test_env = (
            os.getenv("APP_ENV") == "test"
            or os.getenv("MOCK_LLM", "false").lower() == "true"
            or "PYTEST_CURRENT_TEST" in os.environ
        )

        self._openai_client = None
        self._gemini_client = None

        if not self.is_test_env:
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
        target_model = model or self.default_model

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
        Simulates Stanley-level contextual intelligence, empathy, and lore anchoring.
        """
        p_lower = prompt.lower()

        # Meta question: architecture, how it works, why not chatgpt
        if "arquitectura" in p_lower or "chatgpt" in p_lower or "claude" in p_lower or "como funcionas" in p_lower or "cómo funcionas" in p_lower:
            return (
                "la diferencia con chatgpt o claude es que ellos no tienen tu contexto vivo. "
                "si les pides un guion, te dan un ensayo con subtítulos corporativos y frases como 'en este mundo cambiante'. "
                "yo tengo tus 5 recibos reales en memoria: desde cuando automatizaste en 30 minutos el excel de la clínica de tu papá para devolverle los domingos, "
                "hasta la trinchera de ayudasismo y el quiebre de handoff.md. cada gancho que armamos parte de lo que ya viviste, no de un playbook clónico.\n\n"
                "¿quieres que bajemos esa primera pieza hoy?"
            )

        # Haggling / pricing / reset
        if "precio" in p_lower or "1 dolar" in p_lower or "$1" in p_lower or "regateo" in p_lower:
            return (
                "jajaja buen intento, pero mi trabajo no es venderte humo por un dólar. "
                "un solo reel bien colocado que te posicione como la voz técnica de referencia en tu nicho vale cien veces más que cualquier suscripción de juguete. "
                "además, los números de tus referentes demuestran que la trinchera convierte, no los descuentos.\n\n"
                "¿te parece si dejamos el regateo y armamos la pieza de la semana?"
            )

        # Blank mind / blocked creator (Heavy Lifting by RICK)
        if "mente en blanco" in p_lower or "bloqueado" in p_lower or "no sé qué decir" in p_lower or "no se que decir" in p_lower or "no sé qué grabar" in p_lower:
            return (
                "tranquilo, no tienes que inventar nada de cero hoy. ya tienes historias reales listas en la recámara:\n\n"
                "1. por qué seguir playbooks de marketing mata tu voz (la razón exacta por la que decidiste construir a rick e ireal).\n"
                "2. la automatización de 30 minutos con macros de excel para la clínica dental de tu papá para devolverle los domingos.\n\n"
                "dime cuál te vibra más y yo hago el trabajo pesado de estructurar el gancho visual y el quiebre."
            )

        # Script request
        if "guion" in p_lower or "script" in p_lower or "armemos" in p_lower or "escribe" in p_lower:
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

        # Greeting or open dialogue
        return (
            "buenas. tengo el radar del nicho y tus aprendizajes al día. "
            "¿qué fricción o lección real de estos días ponemos sobre la mesa para el canal?"
        )


llm_service = LLMService()
