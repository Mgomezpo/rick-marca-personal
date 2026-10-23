import logging
import json
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from src.core.config import config
from src.core.telemetry import TelemetryTracker
from src.engine.skills_loader import skills_loader

logger = logging.getLogger("rick.subagent.hook_writer")

class HookWriterSubagent:
    """
    Subagente Hook-Writer de RICK:
    Carga dinámicamente 'skills/hook-writer/SKILL.md'.
    Aplica los 9 arquetipos de gancho (contracorriente, escena, confesión, quiebre cognitivo, etc.)
    anclados estrictamente en el lore, anécdotas de trinchera y ADN de voz del creador.
    Prohíbe aperturas cliché, preguntas retóricas aburridas y nombres de plataformas.
    """
    def __init__(self, client: genai.Client, telemetry: TelemetryTracker):
        self.client = client
        self.telemetry = telemetry

    def _build_system_instruction(self, voice_context: str = "") -> str:
        skill_doc = skills_loader.get_skill("hook-writer")
        instruction = (
            "Eres el especialista en ganchos de RICK. Tu trabajo es diseñar ganchos magnéticos para los primeros 3 segundos de un video.\n\n"
            f"{skill_doc}\n\n"
            "PAUTAS:\n"
            "1. Abre directo al quiebre, a la colisión o a la incógnita sin preámbulos ni saludos.\n"
            "2. Cero preguntas retóricas clichés ('¿Alguna vez te has preguntado...?').\n"
            "3. Habla con especificidad y lenguaje humano de tú a tú."
        )
        return instruction

    def generar_ganchos(
        self,
        tema: str,
        angulo: str,
        user_id: str,
        nicho: str = "creadores",
        voice_context: str = "",
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        system_instruction = self._build_system_instruction(voice_context)
        prompt = (
            f"TEMA DEL CONTENIDO: {tema}\n"
            f"ÁNGULO / HERIDA O ANÉCDOTA: {angulo}\n"
            f"NICHO / AUDIENCIA: {nicho}\n\n"
            f"Genera 3 opciones de ganchos poderosos eligiendo entre los 9 arquetipos canónicos de la skill "
            f"(contracorriente, escena viva, confesión brutal, quiebre cognitivo, dato exacto o empatía profunda).\n\n"
            f"Formato de salida para cada opción:\n"
            f"- **Arquetipo:** [nombre del arquetipo]\n"
            f"- **Canal Visual (0-3s):** [Acción física o plano de cámara]\n"
            f"- **Texto Exacto:** \"[Frase hablada con pausas y verdad]\""
        )

        tokens_in = 100
        tokens_out = 100
        used_model = config.OPENAI_MODEL
        hooks_text = ""

        if config.OPENAI_API_KEY:
            try:
                import openai
                oa_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
                oa_resp = oa_client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                hooks_text = (oa_resp.choices[0].message.content or "").strip()
                tokens_in = getattr(oa_resp.usage, "prompt_tokens", 100) or 100
                tokens_out = getattr(oa_resp.usage, "completion_tokens", 100) or 100
            except Exception as oa_err:
                logger.warning(f"Aviso OpenAI {config.OPENAI_MODEL} en HookWriter ({oa_err}). Probando fallback OpenAI {config.OPENAI_FALLBACK_MODEL}...")
                try:
                    oa_resp = oa_client.chat.completions.create(
                        model=config.OPENAI_FALLBACK_MODEL,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7
                    )
                    hooks_text = (oa_resp.choices[0].message.content or "").strip()
                    used_model = config.OPENAI_FALLBACK_MODEL
                except Exception as fb_err:
                    logger.error(f"Error OpenAI fallback en HookWriter: {fb_err}")

        self.telemetry.log_turn(
            phase="writing",
            model_name=used_model,
            prompt_tokens=tokens_in,
            completion_tokens=tokens_out,
            latency_ms=650,
            user_id=user_id,
            thread_id=thread_id,
            metadata={"type": "hooks"}
        )

        return {"success": bool(hooks_text), "hooks": hooks_text}

    def generar_gancho_principal(
        self,
        brief: str,
        voice_context: str = "",
        user_id: str = "anon",
        preferred_archetype: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Produce el gancho único y contundente para alimentar directamente al Guionista en el pipeline.
        Retorna: {"hook": "...", "archetype": "...", "visual_cue": "..."}
        """
        system_instruction = self._build_system_instruction(voice_context)
        prompt = (
            f"MATERIA PRIMA / ANÉCDOTA DEL CREADOR:\n{brief}\n\n"
            f"ARQUETIPO PREFERIDO: {preferred_archetype or 'El que genere mayor quiebre o contraste real'}\n\n"
            f"Tu tarea: Escribe UN gancho magistral de 1 o 2 frases habladas que abra el video sin rodeos ni saludos.\n"
            f"Devuelve estrictamente un bloque JSON con esta estructura:\n"
            f"```json\n"
            f"{{\n"
            f"  \"archetype\": \"nombre_del_arquetipo\",\n"
            f"  \"hook_text\": \"frase exacta hablada para los primeros 3 segundos\",\n"
            f"  \"visual_cue\": \"dirección de cámara o acción de 0 a 3s\"\n"
            f"}}\n"
            f"```"
        )

        res_text = ""
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
                    temperature=0.6
                )
                res_text = (resp.choices[0].message.content or "").strip()
            except Exception as e:
                logger.warning(f"Aviso OpenAI {config.OPENAI_MODEL} en hook principal: {e}. Probando fallback {config.OPENAI_FALLBACK_MODEL}...")
                try:
                    resp = oa_client.chat.completions.create(
                        model=config.OPENAI_FALLBACK_MODEL,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.6
                    )
                    res_text = (resp.choices[0].message.content or "").strip()
                except Exception as fb_err:
                    logger.error(f"Error OpenAI fallback en hook principal: {fb_err}")

        # Extraer JSON
        hook_data = {
            "archetype": "contracorriente",
            "hook_text": brief[:90],
            "visual_cue": "Plano medio cerrado, mirada directa al lente, sin saludos"
        }
        if "```json" in res_text:
            try:
                json_str = res_text.split("```json")[-1].split("```")[0].strip()
                parsed = json.loads(json_str)
                hook_data["archetype"] = parsed.get("archetype", hook_data["archetype"])
                hook_data["hook_text"] = parsed.get("hook_text", hook_data["hook_text"])
                hook_data["visual_cue"] = parsed.get("visual_cue", hook_data["visual_cue"])
            except Exception:
                pass
        elif res_text:
            clean = re.sub(r'[\*"`]', '', res_text).strip()
            hook_data["hook_text"] = clean.split("\n")[0]

        return hook_data
