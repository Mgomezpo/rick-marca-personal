import os
import re
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
from src.core.config import config

logger = logging.getLogger("rick.skills_loader")

class SkillsLoader:
    """
    Cargador dinámico de habilidades (skills/*.md).
    Lee directamente los archivos canónicos de la carpeta skills/,
    remueve el frontmatter YAML para no gastar tokens innecesarios,
    y cachea el contenido verificando la fecha de modificación del archivo
    para que cualquier cambio en las skills se refleje de inmediato en vivo.
    """
    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or config.SKILLS_DIR
        self._cache: Dict[str, Tuple[float, str]] = {}

    def _strip_yaml_frontmatter(self, text: str) -> str:
        """Remueve los bloques de metadata YAML (--- ... ---) al inicio del markdown."""
        stripped = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)
        return stripped.strip()

    def get_skill(self, skill_name: str) -> str:
        """
        Obtiene el contenido canónico de una skill por nombre de carpeta
        (ej: 'creator-interview', 'hook-writer', 'guionista', 'humanizer').
        """
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            # Fallback para nombres con guion bajo
            alt_name = skill_name.replace("-", "_")
            skill_path = self.skills_dir / alt_name / "SKILL.md"
            if not skill_path.exists():
                logger.warning(f"Skill '{skill_name}' no encontrada en {self.skills_dir}")
                return ""

        try:
            mtime = skill_path.stat().st_mtime
            if skill_name in self._cache:
                cached_mtime, cached_content = self._cache[skill_name]
                if cached_mtime == mtime:
                    return cached_content

            raw_text = skill_path.read_text(encoding="utf-8")
            clean_text = self._strip_yaml_frontmatter(raw_text)
            self._cache[skill_name] = (mtime, clean_text)
            logger.info(f"📚 [SkillsLoader] Skill '{skill_name}' cargada dinámicamente ({len(clean_text)} caracteres).")
            return clean_text
        except Exception as e:
            logger.error(f"Error cargando skill '{skill_name}': {e}")
            return ""

    get_skill_instructions = get_skill

    def get_brain_doc(self, rel_path: str) -> str:
        """
        Obtiene el contenido canónico de un documento del cerebro (brain/*).
        Ej: '03_studio/frameworks/decision_tree.md', '01_philosophy/principles/reduction.md'
        Cachea con mtime para hot-reloading inmediato.
        """
        doc_path = config.BRAIN_DIR / rel_path.strip().lstrip("/\\")
        if not doc_path.exists():
            logger.warning(f"Documento de cerebro '{rel_path}' no encontrado en {config.BRAIN_DIR}")
            return ""

        try:
            mtime = doc_path.stat().st_mtime
            cache_key = f"brain:{rel_path}"
            if cache_key in self._cache:
                cached_mtime, cached_content = self._cache[cache_key]
                if cached_mtime == mtime:
                    return cached_content

            raw_text = doc_path.read_text(encoding="utf-8")
            clean_text = self._strip_yaml_frontmatter(raw_text)
            self._cache[cache_key] = (mtime, clean_text)
            logger.info(f"🧠 [BrainLoader] Documento '{rel_path}' cargado dinámicamente ({len(clean_text)} caracteres).")
            return clean_text
        except Exception as e:
            logger.error(f"Error cargando documento de cerebro '{rel_path}': {e}")
            return ""

# Instancia global singleton
skills_loader = SkillsLoader()
