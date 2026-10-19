"""State schema and core models for the RICK multi-tenant agent graph."""
from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class ScriptBlock(BaseModel):
    """Canonical block of a technical script (Hook, Desarrollo, Cierre/CTA)."""
    texto: str = Field(..., description="Texto exacto hablado sin desvíos ni rodeos")
    intencion: str = Field(..., description="Efecto psicológico o intención dramática")
    camara: str = Field(..., description="Indicación visual de cámara y plano")


class ScriptDraft(BaseModel):
    """Structured technical script adhering to the 3-block standard."""
    titulo: str = Field(..., description="Título corto del guion")
    formato: str = Field(default="Reel", description="Formato (Reel, TikTok, etc.)")
    duracion_objetivo: int = Field(default=45, description="Duración en segundos")
    hook: ScriptBlock = Field(..., description="Bloque inicial de enganche")
    desarrollo: ScriptBlock = Field(..., description="Bloque de desarrollo y anécdota")
    cierre: ScriptBlock = Field(..., description="Bloque de cierre / llamado a acción")


class CreatorProfile(BaseModel):
    """Profile of the content creator."""
    user_id: str = Field(..., description="Identificador único del usuario / tenant")
    instagram_handle: str = Field(..., description="Handle de Instagram del creador")
    nicho: str = Field(default="General", description="Sector o nicho de contenido")
    mediana_views: float = Field(default=0.0, description="Mediana de vistas de la cuenta")
    tono_voz: str = Field(default="directo y auténtico", description="Tono y estilo de voz")
    referentes: List[str] = Field(default_factory=list, description="Handles de referentes de cabecera")


class EvaluationResult(BaseModel):
    """Audit result from the evaluator-optimizer quality loop."""
    score: float = Field(..., description="Puntuación de 0 a 10")
    passed: bool = Field(..., description="Verdadero si cumple el estándar de calidad")
    feedback: str = Field(..., description="Observaciones y sugerencias específicas")
    plagio_detectado: bool = Field(default=False, description="Flag de coincidencia >= 5 palabras")
    max_palabras_coincidentes: int = Field(default=0, description="Máximo número de palabras consecutivas idénticas")
    simulacion_estimacion: str = Field(default="Media", description="Estimación empírica: Alta, Media, Baja")
    piezas_respaldo: int = Field(default=0, description="Número de piezas históricas que respaldan el patrón")


class WinningPattern(BaseModel):
    """Empirical pattern with relative performance >= 1.5x."""
    pattern_id: str
    tipo_hook: str
    formato: str
    emocion: str
    rendimiento_relativo_promedio: float
    piezas_respaldo: int
    ejemplos: List[str] = Field(default_factory=list)


class LearningItem(BaseModel):
    """Procedural learning extracted from account performance audit."""
    id: Optional[str] = None
    user_id: str
    statement: str
    applies_when: str
    confidence: float = 1.0
    created_at: Optional[str] = None


class ConversationMessage(BaseModel):
    """Message exchanged in WhatsApp or conversational interface."""
    role: str = Field(..., description="'user', 'assistant' o 'system'")
    content: str = Field(..., description="Contenido en texto plano")
    timestamp: Optional[str] = None


class GraphState(TypedDict, total=False):
    """State definition for the LangGraph / Graph Engine."""
    user_id: str
    creator_profile: Optional[CreatorProfile]
    messages: List[ConversationMessage]
    current_intent: str  # 'chat', 'extract_story', 'generate_script', 'view_report'
    story_extracted: Optional[str]
    referents_context: List[Dict[str, Any]]
    winning_patterns: List[WinningPattern]
    learnings: List[LearningItem]
    script_draft: Optional[ScriptDraft]
    evaluation: Optional[EvaluationResult]
    iteration_count: int
    final_response: Optional[str]
    error: Optional[str]


def create_initial_state(user_id: str, handle: str = "") -> GraphState:
    """Create a pristine, validated initial state for a creator session."""
    return GraphState(
        user_id=user_id,
        creator_profile=CreatorProfile(
            user_id=user_id,
            instagram_handle=handle or f"creator_{user_id}",
        ),
        messages=[],
        current_intent="chat",
        story_extracted=None,
        referents_context=[],
        winning_patterns=[],
        learnings=[],
        script_draft=None,
        evaluation=None,
        iteration_count=0,
        final_response=None,
        error=None,
    )


def update_state(state: GraphState, **updates: Any) -> GraphState:
    """Pure functional update: returns a new copy of GraphState with updates applied."""
    new_state = state.copy()
    new_state.update(updates)
    return new_state
