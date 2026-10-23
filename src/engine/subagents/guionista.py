import logging
import json
import re
from typing import Any, Dict, Optional
from google import genai
from google.genai import types
from src.core.config import config
from src.core.telemetry import TelemetryTracker
from src.db.supabase import DatabaseService
from src.engine.skills_loader import skills_loader
from src.engine.subagents.anti_slop_editor import AntiSlopEditor
from src.engine.subagents.hook_writer import HookWriterSubagent

logger = logging.getLogger("rick.subagent.guionista")

class GuionistaSubagent:
    """
    Subagente Guionista Maestro de RICK:
    Pipeline encadenado de 3 fases:
    1. HookWriter (carga 'skills/hook-writer/SKILL.md' y genera un gancho de quiebre cognitivo).
    2. Redactor (carga 'skills/guionista/SKILL.md' y desarrolla los 5 actos con intención y cámara).
    3. AntiSlopEditor / Humanizer (carga 'skills/humanizer/SKILL.md', purga clichés de IA y calibra la voz humana).
    Persiste la pieza en Supabase (tabla 'pieces').
    """
    def __init__(
        self,
        client: genai.Client,
        db: DatabaseService,
        telemetry: TelemetryTracker,
        editor: AntiSlopEditor,
        hook_writer: Optional[HookWriterSubagent] = None
    ):
        self.client = client
        self.db = db
        self.telemetry = telemetry
        self.editor = editor
        self.hook_writer = hook_writer or HookWriterSubagent(client, telemetry)

    def redactar_guion(
        self,
        brief: str,
        user_id: str,
        formato: str = "reel",
        framework: str = "pas",
        voice_context: str = "",
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"🎬 [Guionista Pipeline] Iniciando redacción para usuario {user_id} con framework={framework}")

        # ---------------------------------------------------------------------
        # FASE 1: Generación de Gancho de Quiebre con HookWriter
        # ---------------------------------------------------------------------
        logger.info("🎣 [Guionista] Fase 1: Solicitando gancho de impacto a HookWriter...")
        hook_info = self.hook_writer.generar_gancho_principal(
            brief=brief,
            voice_context=voice_context,
            user_id=user_id
        )
        winning_hook = hook_info.get("hook_text", brief[:80])
        hook_archetype = hook_info.get("archetype", "contracorriente")
        hook_visual = hook_info.get("visual_cue", "Plano medio cerrado, mirada directa al lente, sin saludos")
        logger.info(f"✨ [Guionista] Gancho seleccionado ({hook_archetype}): '{winning_hook}'")

        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------
        # FASE 2: Redacción del Guion Estructurado con la Skill Guionista y Cerebro
        # ---------------------------------------------------------------------
        guionista_skill = skills_loader.get_skill("guionista")

        system_instruction = (
            "Eres el Guionista de RICK. Tu trabajo es transformar una idea, anécdota o concepto en un guion "
            "claro, dinámico y grabable para Reels o Shorts (45-60s).\n\n"
            f"{guionista_skill}\n\n"
            "PAUTAS DE REDACCIÓN:\n"
            "1. De socio a socio: habla de 'yo' a 'tú'. Lenguaje hablado, natural y con ritmo variado.\n"
            "2. Sin relleno ni frases corporativas vacías.\n"
            "3. La estructura es una guía de dirección para grabar con tensión y claridad, no una ficha técnica abstracta."
        )

        req_fw = (framework or "auto").strip().lower()
        fw_directive = f"- Estructura Narrativa / Framework: {req_fw.upper()}"
        if req_fw in ["auto", "pas"]:
            fw_directive = (
                "- SELECCIÓN HEURÍSTICA DE FRAMEWORK (ÁRBOL DE DECISIÓN):\n"
                "  Evalúa la idea/anécdota contra las 4 ramas del Árbol de Decisión y selecciona la estructura óptima:\n"
                "  * Si ataca un dogma o práctica común equivocada -> QUIEBRE_COGNITIVO\n"
                "  * Si muestra código, software o sistemas en vivo -> CASO_REAL\n"
                "  * Si comparte vivencia, error propio o lección de batalla -> HISTORIA_LECCION\n"
                "  * Si contrasta antes vs después -> BAB\n"
                "  * Si es dolor y solución directa -> PAS\n"
                "  Declara la estructura exacta seleccionada en el encabezado `Estructura: [NOMBRE]`."
            )

        user_prompt = (
            f"DATOS DE ENTRADA DEL CREADOR:\n"
            f"- Idea / Anécdota o Fricción Real: {brief}\n"
            f"- Formato: {formato}\n"
            f"{fw_directive}\n\n"
            f"GANCHO SELECCIONADO PARA EL PASO 1:\n"
            f"- Arquetipo: {hook_archetype}\n"
            f"- Texto Gancho: \"{winning_hook}\"\n"
            f"- Cámara Gancho: \"{hook_visual}\"\n\n"
            f"CONTEXTO DE VOZ DEL CREADOR:\n"
            f"{voice_context or 'Directo, pausado, reflexivo, de trinchera, sin poses.'}\n\n"
            f"Redacta el guion completo siguiendo rigurosamente el formato oficial:\n"
            f"GUION: [TÍTULO]\n"
            f"Formato: [Reel (45-60s)] | Estructura: [NOMBRE_DE_ESTRUCTURA_SELECCIONADA]\n\n"
            f"OBJETIVO Y TRANSFORMACIÓN\n[De dónde parte la audiencia y hacia dónde la llevas]\n\n"
            f"1. HOOK\n"
            f"• Texto: \"{winning_hook}\"\n"
            f"• Intención: [Efecto psicológico del gancho]\n"
            f"• Cámara: \"{hook_visual}\"\n\n"
            f"[PASOS SIGUIENTES CON Texto + Intención + Cámara según el framework]\n\n"
            f"---\n"
            f"DIRECCIÓN Y COPY\n"
            f"• Tono: [Conversación en una mesa de café, de socio a socio]\n"
            f"• Copy para Publicar:\n"
            f"[Gancho en texto]\n"
            f"[Bullet 1]\n"
            f"[Bullet 2]\n"
            f"[Pregunta abierta reflexiva para comentarios]\n"
            f"[3 hashtags de nicho]"
        )

        raw_script = ""
        tokens_in = 150
        tokens_out = 250
        used_model = config.WRITER_MODEL

        # Intentar OpenAI
        if config.OPENAI_API_KEY:
            try:
                import openai
                oa_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
                oa_resp = oa_client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.6
                )
                raw_script = (oa_resp.choices[0].message.content or "").strip()
                used_model = config.OPENAI_MODEL
                tokens_in = getattr(oa_resp.usage, "prompt_tokens", 150) or 150
                tokens_out = getattr(oa_resp.usage, "completion_tokens", 250) or 250
            except Exception as e:
                logger.warning(f"Aviso OpenAI {config.OPENAI_MODEL} en Guionista ({e}). Probando fallback OpenAI {config.OPENAI_FALLBACK_MODEL}...")
                try:
                    oa_resp = oa_client.chat.completions.create(
                        model=config.OPENAI_FALLBACK_MODEL,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.6
                    )
                    raw_script = (oa_resp.choices[0].message.content or "").strip()
                    used_model = config.OPENAI_FALLBACK_MODEL
                except Exception as fb_err:
                    logger.error(f"Error OpenAI fallback en Guionista: {fb_err}")

        if not raw_script:
            raise RuntimeError("Ningún proveedor LLM pudo generar el borrador del guion.")

        # ---------------------------------------------------------------------
        # FASE 3: Pase de Calidad Humanizer & Anti-Slop (Skills/Humanizer)
        # ---------------------------------------------------------------------
        logger.info("🛡️ [Guionista] Fase 3: Pasando guion por Humanizer...")
        clean_script, was_clean, issues = self.editor.audit_and_refine(
            text=raw_script,
            user_id=user_id,
            creator_voice_context=voice_context
        )

        # Estandarización defensiva de encabezados canónicos
        clean_script = re.sub(r'(?i)objetivo y transformación', 'OBJETIVO Y TRANSFORMACIÓN', clean_script)
        clean_script = re.sub(r'(?i)1\.\s*(inicio|gancho)', '1. HOOK', clean_script)
        clean_script = re.sub(r'(?i)dirección y copy', 'DIRECCIÓN Y COPY', clean_script)
        clean_script = re.sub(r'(?i)dirección y texto', 'DIRECCIÓN Y COPY', clean_script)

        # Extraer metadatos con regexes robustas
        title_m = re.search(r'GUION:\s*([^\n\r]+)', clean_script, re.IGNORECASE)
        title = title_m.group(1).strip().strip("[]*") if title_m else brief[:50]

        hook_m = re.search(r'1\.\s*HOOK[\s\S]*?•\s*Texto:\s*["\']?([^"\n\r]+)["\']?', clean_script, re.IGNORECASE)
        hook = hook_m.group(1).strip() if hook_m else winning_hook

        struct_m = re.search(r'Estructura:\s*\[?([a-zA-Z_]+)\]?', clean_script, re.IGNORECASE)
        effective_framework = struct_m.group(1).lower().strip() if struct_m else (framework or "pas")

        copy_text = ""
        copy_m = re.search(r'Copy para Publicar:?\s*([\s\S]+)', clean_script, re.IGNORECASE)
        if copy_m:
            copy_text = copy_m.group(1).strip()
        else:
            lines = [l.strip() for l in clean_script.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if "copy para publicar" in line.lower():
                    copy_text = "\n".join(lines[i+1:])
                    break

        # Guardar en Supabase
        saved_piece = self.db.save_script_piece(
            user_id=user_id,
            title=title,
            hook=hook,
            body=clean_script,
            copy=copy_text,
            format=formato,
            framework=effective_framework,
            thread_id=thread_id
        )

        self.telemetry.log_turn(
            phase="writing",
            model_name=used_model,
            prompt_tokens=tokens_in,
            completion_tokens=tokens_out,
            latency_ms=1300,
            user_id=user_id,
            thread_id=thread_id,
            metadata={"framework": framework, "formato": formato, "pipeline": "hook->guion->humanizer"}
        )

        return {
            "success": True,
            "title": title,
            "hook": hook,
            "framework": effective_framework,
            "script": clean_script,
            "content": clean_script,
            "piece_id": saved_piece.get("id") if isinstance(saved_piece, dict) else None,
            "was_clean": was_clean,
            "issues_fixed": issues
        }
