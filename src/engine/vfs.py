import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.config import config
from src.db.supabase import DatabaseService

logger = logging.getLogger("rick.vfs")

class VirtualFileSystem:
    """
    Virtual File System (VFS) que abstrae el conocimiento de RICK:
    - Carpetas estáticas (Código/Git): /filosofia, /studio, /skills.
    - Carpetas dinámicas multitenant (Supabase): /creator, /memorias, /produccion.
    """
    def __init__(self, db: DatabaseService):
        self.db = db
        self.root_dir = config.ROOT_DIR
        self.brain_dir = config.BRAIN_DIR
        self.skills_dir = config.SKILLS_DIR

    def _normalize_path(self, path: str) -> str:
        p = path.strip().replace("\\", "/")
        if p.startswith("/"):
            p = p[1:]
        return p

    # -------------------------------------------------------------------------
    # LISTAR CARPETA
    # -------------------------------------------------------------------------
    def list_dir(self, virtual_path: str, user_id: str) -> List[str]:
        p = self._normalize_path(virtual_path)

        # Raíz
        if not p or p == ".":
            return [
                "filosofia/ (canon y principios de Rick Rubin)",
                "studio/ (frameworks de guion y storytelling)",
                "skills/ (habilidades especializadas: guionista, hooks, etc.)",
                "creator/ (identidad y ADN de voz del creador actual)",
                "memorias/ (contexto activo y aprendizajes del creador)",
                "produccion/ (guiones y series guardadas del creador)",
            ]

        # 1. Zonas Estáticas (Repo)
        if p.startswith("filosofia"):
            sub = p.replace("filosofia", "").strip("/")
            target = self.brain_dir / "01_philosophy" / sub
            if target.exists() and target.is_dir():
                return [f.name + ("/" if f.is_dir() else "") for f in target.iterdir() if not f.name.startswith(".")]
            return []

        if p.startswith("studio"):
            sub = p.replace("studio", "").strip("/")
            target = self.brain_dir / "03_studio" / sub
            if target.exists() and target.is_dir():
                return [f.name + ("/" if f.is_dir() else "") for f in target.iterdir() if not f.name.startswith(".")]
            return []

        if p.startswith("skills"):
            sub = p.replace("skills", "").strip("/")
            target = self.skills_dir / sub
            if target.exists() and target.is_dir():
                return [f.name + ("/" if f.is_dir() else "") for f in target.iterdir() if not f.name.startswith(".")]
            return []

        # 2. Zonas Dinámicas Multitenant (Supabase)
        if p.startswith("creator"):
            return [
                "identity/voice_dna.md",
                "identity/positioning.md",
                "lore/origin_stories.md",
                "reality/current_focus.md"
            ]

        if p.startswith("memorias"):
            return [
                "active_context.md",
                "learnings.md",
                "series_status.md"
            ]

        if p.startswith("produccion"):
            scripts = self.db.get_user_scripts(user_id, limit=10)
            return [f"scripts/{s.get('id', 'item')}_{s.get('title', 'sin_titulo')}.md" for s in scripts] or ["scripts/ (vacío)"]

        return []

    # -------------------------------------------------------------------------
    # LEER DOCUMENTO
    # -------------------------------------------------------------------------
    def read_file(self, virtual_path: str, user_id: str) -> str:
        p = self._normalize_path(virtual_path)

        # 1. Zonas Estáticas (Repo)
        if p.startswith("filosofia"):
            sub = p.replace("filosofia", "").strip("/")
            target = self.brain_dir / "01_philosophy" / sub
            if target.exists() and target.is_file():
                return target.read_text(encoding="utf-8")
            return f"[Error: Archivo {virtual_path} no encontrado en filosofia]"

        if p.startswith("studio"):
            sub = p.replace("studio", "").strip("/")
            target = self.brain_dir / "03_studio" / sub
            if target.exists() and target.is_file():
                return target.read_text(encoding="utf-8")
            return f"[Error: Archivo {virtual_path} no encontrado en studio]"

        if p.startswith("skills"):
            sub = p.replace("skills", "").strip("/")
            target = self.skills_dir / sub
            if target.exists() and target.is_file():
                return target.read_text(encoding="utf-8")
            return f"[Error: Archivo {virtual_path} no encontrado en skills]"

        # 2. Zonas Dinámicas Multitenant (Supabase)
        if "voice_dna" in p or "voice-dna" in p or "voz" in p:
            assets = self.db.get_brand_assets(user_id)
            voice_slot = assets.get("voz")
            if not voice_slot or voice_slot.get("status") == "empty":
                return (
                    "# ADN de Voz del Creador\n\n"
                    "Estado: `[PENDIENTE_DE_ENTREVISTA]`\n\n"
                    "Este creador aún no ha completado su entrevista inicial. "
                    "Inicia la creator-interview con preguntas socráticas para descubrir su obsesión y enemigo común."
                )
            content = voice_slot.get("content") or {}
            summary = voice_slot.get("summary") or ""
            return (
                f"# ADN de Voz del Creador\n\n"
                f"**Resumen:** {summary}\n\n"
                f"**Vibe:** {content.get('vibe', 'Directo, reflexivo')}\n"
                f"**Cadencia:** {content.get('cadence', 'Pausada, asertiva')}\n"
                f"**Palabras Prohibidas:** {', '.join(content.get('prohibited_words', []))}\n"
                f"**Obsesión Central:** {content.get('obsession', 'No definida')}\n"
            )

        if "positioning" in p:
            profile = self.db.get_user_profile(user_id)
            assets = self.db.get_brand_assets(user_id)
            cliente_slot = assets.get("cliente_ideal")
            if not profile and not cliente_slot:
                return (
                    "# Posicionamiento y Audiencia\n\n"
                    "Estado: `[PENDIENTE_DE_ENTREVISTA]`\n\n"
                    "El creador no tiene configurado su nicho ni cliente ideal."
                )
            niche = profile.get("main_niche", "No especificado") if profile else "No especificado"
            angle = profile.get("unique_angle", "No especificado") if profile else "No especificado"
            audience = profile.get("target_audience", "No especificada") if profile else "No especificada"
            why = profile.get("why", "") if profile else ""
            return (
                f"# Posicionamiento de Marca\n\n"
                f"- **Nicho:** {niche}\n"
                f"- **Ángulo Único / Enemigo Común:** {angle}\n"
                f"- **Audiencia Objetivo:** {audience}\n"
                f"- **El Por Qué Profundo:** {why}\n"
                f"- **Cliente Ideal (Slot):** {cliente_slot.get('summary', 'Pendiente') if cliente_slot else 'Pendiente'}\n"
            )

        if "origin_stories" in p or "lore" in p:
            assets = self.db.get_brand_assets(user_id)
            lore_slot = assets.get("lore") or assets.get("historia_origen")
            if lore_slot:
                content = lore_slot.get("content") or {}
                story = content.get("origin_story") or str(content)
                summary = lore_slot.get("summary", "")
                return f"# Historias de Origen & Lore\n\n**Resumen:** {summary}\n\n**Historia / Fricción:** {story}"
            return "# Historias de Origen\n\nNo hay historias registradas aún. Indaga en anécdotas de trinchera."

        if "active_context" in p or "current_focus" in p:
            mem = self.db.get_active_memory(user_id)
            state = mem.get("state") or {}
            summary = mem.get("summary") or "Sin resumen"
            scratch = state.get("scratchpad_notes", [])
            notes_str = "\n".join([f"  • {n}" for n in scratch]) if scratch else "  (Sin notas acumuladas)"
            return (
                f"# Contexto Activo y Memoria de Trabajo\n\n"
                f"**Resumen Actual:** {summary}\n\n"
                f"- **Tema Activo:** {state.get('active_topic', 'Ninguno')}\n"
                f"- **Serie en Curso:** {state.get('current_series', 'Ninguna')}\n"
                f"- **Notas de Trabajo / Lote:**\n{notes_str}\n"
            )

        if "series_status" in p:
            mem = self.db.get_active_memory(user_id)
            state = mem.get("state") or {}
            curr_series = state.get("current_series", "serie-anti-slop")
            scratch = "\n".join([f"- {n}" for n in state.get("scratchpad_notes", [])])
            return (
                f"# Estado de Series del Creador\n\n"
                f"- **Serie Activa:** {curr_series}\n\n"
                f"### Lote de Producción y Notas:\n"
                f"{scratch or 'Sin notas de serie activas.'}\n"
            )

        if "learnings" in p:
            try:
                res = self.db.client.table("procedural_learnings").select("*").eq("user_id", user_id).limit(10).execute()
                rows = res.data or []
                if not rows:
                    return "# Aprendizajes Editoriales\n\nNo hay aprendizajes registrados aún para este creador."
                md = "# Aprendizajes de Rendimiento y Criterio\n\n"
                for r in rows:
                    md += f"- **[{r.get('status', 'activo')}]** {r.get('statement')}\n  *Aplica cuando:* {r.get('applies_when')}\n"
                return md
            except Exception as e:
                return f"# Aprendizajes\n\nError consultando aprendizajes: {e}"

        if "scripts" in p:
            scripts = self.db.get_user_scripts(user_id, limit=5)
            if not scripts:
                return "# Guiones Producidos\n\nNo hay guiones guardados aún."
            out = "# Últimos Guiones Producidos\n\n"
            for s in scripts:
                out += f"## {s.get('title', 'Sin título')} ({s.get('created_at')})\n"
                out += f"**Formato:** {s.get('format')} | **Estrategia:** {s.get('strategy_tag')}\n\n"
                out += f"{s.get('script', '')}\n\n---\n\n"
            return out

        return f"[Error: Documento {virtual_path} no reconocido en el VFS]"

    # -------------------------------------------------------------------------
    # BÚSQUEDA GLOBAL (Ripgrep estático + RAG Supabase)
    # -------------------------------------------------------------------------
    def search_brain(self, query: str, user_id: str, limit: int = 5) -> str:
        q_lower = query.lower()
        results: List[str] = []

        # 1. Búsqueda en archivos estáticos (filosofía y frameworks)
        search_dirs = [
            (self.brain_dir / "01_philosophy", "filosofia"),
            (self.brain_dir / "03_studio" / "frameworks", "studio/frameworks"),
            (self.skills_dir, "skills"),
        ]

        for s_dir, label in search_dirs:
            if not s_dir.exists():
                continue
            for file in s_dir.rglob("*.md"):
                try:
                    text = file.read_text(encoding="utf-8")
                    if q_lower in text.lower():
                        # Extraer snippet alrededor de la coincidencia
                        idx = text.lower().find(q_lower)
                        start = max(0, idx - 100)
                        end = min(len(text), idx + 250)
                        snippet = text[start:end].replace("\n", " ")
                        rel_path = file.relative_to(self.root_dir).as_posix()
                        results.append(f"📄 **[{label}] {rel_path}**:\n   `...{snippet}...`\n")
                        if len(results) >= limit:
                            break
                except Exception:
                    continue
            if len(results) >= limit:
                break

        # 2. Búsqueda en base de datos para este creador
        try:
            scripts = self.db.client.table("pieces").select("id, title, script").eq("user_id", user_id).ilike("script", f"%{query}%").limit(3).execute()
            for s in scripts.data or []:
                results.append(f"🎬 **[produccion/scripts] {s.get('title')}**:\n   `{s.get('script')[:180]}...`\n")
        except Exception as e:
            logger.debug(f"Error en búsqueda DB: {e}")

        if not results:
            return f"No se encontraron coincidencias para '{query}' en el cerebro."

        return f"### Resultados de Búsqueda para '{query}':\n\n" + "\n".join(results)
