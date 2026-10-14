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

        system_instruction = (
            "Eres el Humanizer y Editor Anti-Slop Maestro de RICK (Productor Creativo inspirado en Rick Rubin).\n"
            "Tu misión es tomar un borrador de guion y DE-AI-IZARLO (des-sloppearlo) por completo.\n\n"
            "### DIRECTRICES MAESTRAS DE LA SKILL HUMANIZER:\n"
            f"{humanizer_skill}\n\n"
            "### CONTEXTO DE VOZ DEL CREADOR:\n"
            f"{creator_voice_context or 'Directo, conversacional, sobrio, de trinchera, de tú a tú.'}\n\n"
            "CRITERIOS DE CIRUGÍA EDITORIAL:\n"
            "1. PURGAR CLICHÉS DE IA: Elimina preguntas retóricas mecánicas ('¿Cuántas veces te has...?'), "
            "metáforas baratas ('espejismo', 'brújula hacia la monetización'), y moralejas de autoayuda barata.\n"
            "2. MANTENER LA ESTRUCTURA OFICIAL: Conserva el encabezado GUION, Formato/Estructura, OBJETIVO Y TRANSFORMACIÓN, "
            "los pasos numerados con • Texto, • Intención, • Cámara, y al final DIRECCIÓN Y COPY.\n"
            "3. VOZ VIVA: Haz que las líneas de • Texto suenen a algo que dirías tomando un café con un socio "
            "después de un día duro de trabajo. Cero teleprompter, frases con ritmo variado (cortas y afiladas).\n"
            "4. Devuelve ÚNICAMENTE el guion pulido, sin explicaciones, sin preámbulos y sin disculpas."
        )

        prompt = f"AUDITA, PURGA CLICHÉS Y HUMANIZA ESTE GUION:\n\n{text}"

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
                logger.warning(f"Aviso OpenAI en Humanizer ({e}). Probando Gemini...")

        if not cleaned and config.GEMINI_API_KEY:
            try:
                resp = self.client.models.generate_content(
                    model=config.ORCHESTRATOR_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.5,
                    )
                )
                cleaned = resp.text.strip()
                used_model = config.ORCHESTRATOR_MODEL
                tokens_in = getattr(resp.usage_metadata, "prompt_token_count", 0)
                tokens_out = getattr(resp.usage_metadata, "candidates_token_count", 0)
            except Exception as e:
                logger.error(f"Error Gemini en Humanizer: {e}")

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
