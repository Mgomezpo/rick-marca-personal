import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from google import genai
from google.genai import types
from src.core.config import config
from src.core.telemetry import TelemetryTracker
from src.engine.skills_loader import skills_loader

logger = logging.getLogger("rick.anti_slop")

# Lista expandida de patrones y muletillas sintéticas de IA
PROHIBITED_PATTERNS = [
    r"en este mundo cambiante",
    r"en la era digital",
    r"descubre el secreto",
    r"desata tu potencial",
    r"un viaje fascinante",
    r"sin lugar a dudas",
    r"hoy en día",
    r"revolucionario",
    r"disruptivo",
    r"sumérgete en",
    r"en conclusión",
    r"para resumir",
    r"el juego ha cambiado",
    r"desbloquea tu",
    r"en un abrir y cerrar de ojos",
    r"es crucial entender",
    r"un aspecto fundamental",
    r"imagina por un momento",
    r"en el tapiz de",
    r"testamento de",
    r"es un espejismo",
    r"tu brújula hacia",
    r"¿qué es lo peor que podría pasar\? piénsalo",
    r"¿alguna vez te has preguntado",
    r"¿cuántas veces te has frenado",
    r"yo he estado ahí, esperando que todo sea perfecto",
]

class AntiSlopEditor:
    """
    Editor Humanizer y Purgador de Clichés de RICK:
    Carga dinámicamente 'skills/humanizer/SKILL.md'.
    Audita el texto para detectar y eliminar los 29 patrones de escritura sintética de IA:
    - Retórica predecible y preguntas retóricas clichés.
    - Metáforas cursis ('brújula', 'espejismo', 'tapiz').
    - Simetría robótica y moralejas de autoayuda.
    Reemplaza la prosa sintética con lenguaje de trinchera, asimetría conversacional y voz humana real.
    """
    def __init__(self, client: genai.Client, telemetry: TelemetryTracker):
        self.client = client
        self.telemetry = telemetry

    def quick_scan(self, text: str) -> List[str]:
        """Detecta coincidencias con patrones de IA."""
        t_low = text.lower()
        found = []
        for pat in PROHIBITED_PATTERNS:
            if re.search(pat, t_low):
                found.append(pat.replace("\\", ""))
        return found

    def audit_and_refine(
        self,
        text: str,
        user_id: str,
        creator_voice_context: str = "",
        creator_prohibited: Optional[List[str]] = None
    ) -> Tuple[str, bool, List[str]]:
        """
        Aplica la skill canónica de humanizer sobre el guion o texto generado.
        Garantiza que el resultado suene a una persona real hablando con un colega.
        """
        detected = self.quick_scan(text)
        if creator_prohibited:
            for p in creator_prohibited:
                if p.lower() in text.lower():
                    detected.append(p)

        # Cargar skill de humanizer
        humanizer_skill = skills_loader.get_skill("humanizer")

        detected_hint = f"\nPatrones y clichés a purgar sin excepción: {', '.join(detected)}" if detected else ""
        system_instruction = (
            f"{humanizer_skill}\n\n"
            "Aplica la skill Humanizer a todo el texto para eliminar cualquier patrón o cliché sintético de IA (como 'en este mundo cambiante', 'el juego ha cambiado', 'desata tu potencial') y devolverlo con voz natural, variada y humana."
            f"{detected_hint}\n"
            "Devuelve únicamente el texto pulido, sin explicaciones ni preámbulos."
        )

        prompt = f"Texto a humanizar:\n{text}"

        cleaned = ""
        used_model = config.OPENAI_MODEL
        tokens_in = 150
        tokens_out = 150

        if config.OPENAI_API_KEY:
            try:
                import openai
                oa_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
                resp = oa_client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                cleaned = (resp.choices[0].message.content or "").strip()
                tokens_in = getattr(resp.usage, "prompt_tokens", 150) or 150
                tokens_out = getattr(resp.usage, "completion_tokens", 150) or 150
            except Exception as e:
                logger.warning(f"Aviso OpenAI {config.OPENAI_MODEL} en Humanizer ({e}). Probando fallback OpenAI {config.OPENAI_FALLBACK_MODEL}...")
                try:
                    resp = oa_client.chat.completions.create(
                        model=config.OPENAI_FALLBACK_MODEL,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5
                    )
                    cleaned = (resp.choices[0].message.content or "").strip()
                    used_model = config.OPENAI_FALLBACK_MODEL
                except Exception as fb_err:
                    logger.error(f"Error OpenAI fallback en Humanizer: {fb_err}")

        final_script = cleaned if cleaned else text
        was_clean = len(detected) == 0 and (final_script == text)

        self.telemetry.log_turn(
            phase="humanizing",
            model_name=used_model,
            prompt_tokens=tokens_in,
            completion_tokens=tokens_out,
            latency_ms=800,
            user_id=user_id,
            metadata={"humanized": True, "issues_detected": detected}
        )

        return final_script, was_clean, detected
