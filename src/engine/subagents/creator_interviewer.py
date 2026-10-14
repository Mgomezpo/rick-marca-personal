"""
[DEPRECATED / ARCHIVED]
El subagente aislado CreatorInterviewerSubagent ha sido reemplazado por la arquitectura unificada:
- Skill: skills/creator-interview/SKILL.md
- Tools: investigar_huella_creador, completar_onboarding_creador en src/engine/tools.py
- Binario en BD: user_profiles.onboarding_status == 'completed'
"""
import logging

logger = logging.getLogger("rick.subagent.interviewer")

class CreatorInterviewerSubagent:
    """Compatibilidad histórica. El orquestador ahora utiliza herramientas nativas."""
    def __init__(self, *args, **kwargs):
        pass
