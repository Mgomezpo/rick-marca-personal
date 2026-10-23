"""State schema and core models for the RICK multi-tenant agent graph."""
from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class StoryReceipt(BaseModel):
    """Real episodic memory / receipt from creator's actual life and projects."""
    id: str = Field(..., description="Identificador corto único de la anécdota")
    summary: str = Field(..., description="Resumen conciso del hecho real")
    theme: str = Field(..., description="Tesis o valor central (ej. 'alivio humano > software inflado')")
    concrete_details: List[str] = Field(default_factory=list, description="Detalles hiper-específicos (nombres, tiempos, herramientas)")
    punchline: Optional[str] = Field(default=None, description="La conclusión o aprendizaje práctico que deja")


class StrategistReasoning(BaseModel):
    """Structured internal monologue and reasoning scratchpad for the Strategist node."""
    user_subtext: str = Field(..., description="Qué intenta expresar o qué problema real tiene el creador")
    cliche_trap_to_avoid: str = Field(..., description="Qué respuesta genérica, tibia o cliché de IA debemos prohibir en este turno")
    selected_receipt_id: Optional[str] = Field(default=None, description="ID del StoryReceipt del story_bank del creador más relevante para este turno")
    contrarian_angle: str = Field(..., description="Tesis o ángulo a contracorriente que evita sonar a gurú genérico")
    has_concrete_scene: bool = Field(default=False, description="Si la historia ya tiene escena/momento real")
    has_root_friction: bool = Field(default=False, description="Si la historia ya tiene el error o verdad incómoda")
    is_multipoint_story: bool = Field(default=False, description="Si la historia tiene múltiples puntos que ameritan sugerir saga de 2 partes vs pieza única")
    routed_intent: str = Field(default="chat", description="Intent clasificado: chat, extract_story, generate_script, view_report, cold_onboarding, etc.")


class ScriptBlock(BaseModel):
    """Canonical block of a technical script (Hook, Desarrollo, Cierre/CTA)."""
    texto: str = Field(..., description="Texto exacto hablado sin desvíos ni rodeos")
    intencion: str = Field(..., description="Efecto psicológico o intención dramática")
    camara: str = Field(default="", description="Indicación visual de cámara y plano")
    visual_text: Optional[str] = Field(default=None, description="Texto visual en pantalla (Visual Hook)")


class SeriesMetadata(BaseModel):
    """Metadata for episodic saga or series continuity."""
    series_id: str = Field(..., description="Identificador único de la saga o serie")
    series_title: str = Field(..., description="Título temático o nombre de la serie")
    episode_index: int = Field(..., description="Número de episodio actual (1-indexed)")
    total_episodes: Optional[int] = Field(default=None, description="Total planeado de episodios en la saga")
    previous_piece_id: Optional[str] = Field(default=None, description="ID de la pieza anterior en la secuencia")
    next_piece_id: Optional[str] = Field(default=None, description="ID de la siguiente pieza en la secuencia")


class ScriptDraft(BaseModel):
    """Structured technical script with Dual-Coding Contrast and Anti-Slop psychology."""
    titulo: str = Field(..., description="Título corto del guion")
    formato: str = Field(default="Reel", description="Formato (Reel, TikTok, etc.)")
    duracion_objetivo: int = Field(default=45, description="Duración en segundos")
    hook: ScriptBlock = Field(..., description="Bloque inicial de enganche")
    desarrollo: ScriptBlock = Field(..., description="Bloque de desarrollo y anécdota")
    cierre: ScriptBlock = Field(..., description="Bloque de cierre / llamado a acción")
    # Multidimensional content dimensions (Sagas, Brand Pillars, Plans)
    pilar: Optional[str] = Field(default=None, description="Pilar estratégico de marca (ej. 'Mentalidad', 'Ventas')")
    series: Optional[SeriesMetadata] = Field(default=None, description="Metadatos de saga o miniserie episódica")
    plan_id: Optional[str] = Field(default=None, description="ID del plan de contenido o campaña si aplica")
    # Stanley-level Dual-Coding fields
    visual_hook: Optional[str] = Field(default=None, description="Texto en pantalla que contrasta con el audio hablado")
    spoken_hook: Optional[str] = Field(default=None, description="Gancho hablado en audio de segundo cero")
    friction_step: Optional[str] = Field(default=None, description="Colisión o quiebre cognitivo en <10 palabras")


class CreatorProfile(BaseModel):
    """Profile of the content creator with Lore & Receipts episodic memory."""
    user_id: str = Field(..., description="Identificador único del usuario / tenant")
    instagram_handle: str = Field(..., description="Handle de Instagram del creador")
    nicho: str = Field(default="General", description="Sector o nicho de contenido")
    mediana_views: float = Field(default=0.0, description="Mediana de vistas de la cuenta")
    tono_voz: str = Field(default="directo y auténtico", description="Tono y estilo de voz")
    referentes: List[str] = Field(default_factory=list, description="Handles de referentes de cabecera")
    story_bank: List[StoryReceipt] = Field(default_factory=list, description="Banco de anécdotas e historias reales del creador")


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


class BrandPillarDistribution(BaseModel):
    """Distribution and balance of personal brand pillars."""
    pillar_name: str = Field(..., description="Nombre del pilar de contenido")
    target_percentage: float = Field(..., description="Porcentaje meta de la estrategia (ej. 40%)")
    actual_percentage: float = Field(..., description="Porcentaje real observado en posts recientes")
    post_count: int = Field(default=0, description="Número de posts recientes dedicados al pilar")
    status: str = Field(default="balanced", description="'balanced', 'over_indexed', 'deserted'")


class BrandHealthReport(BaseModel):
    """Diagnostic audit of personal brand positioning, authority and voice."""
    user_id: str = Field(..., description="Identificador del creador")
    overall_score: float = Field(..., description="Puntaje de salud de marca de 0 a 10")
    pillars: List[BrandPillarDistribution] = Field(default_factory=list, description="Desglose por pilares")
    voice_drift_detected: bool = Field(default=False, description="Flag si la voz se alejó del tono auténtico")
    voice_drift_notes: str = Field(default="", description="Explicación del desvío de tono o ángulo")
    key_recommendation: str = Field(..., description="Recomendación estratégica principal")
    suggested_action: str = Field(..., description="Acción táctica inmediata (ej. 'crear_demostracion_mecanismo')")


class ProactiveSpark(BaseModel):
    """Proactive content idea or angle proposed to the creator with market backing."""
    spark_id: str = Field(..., description="ID único de la propuesta")
    source_referent: str = Field(..., description="Handle del referente de cabecera que detonó la idea")
    referent_hook_text: str = Field(..., description="Hook original del referente")
    relative_performance: float = Field(..., description="Rendimiento relativo (R >= 2.0x)")
    adapted_angle: str = Field(..., description="Ángulo adaptado al nicho y tesis del creador")
    suggested_hook: str = Field(..., description="Propuesta concreta de gancho en las palabras del creador")
    target_pillar: str = Field(..., description="Pilar de marca que fortalece")
    confidence: float = Field(default=0.9, description="Confianza empírica del patrón (0 a 1)")


class GovernorDecision(BaseModel):
    """Outcome of the Anti-Spam Governor evaluation."""
    allowed: bool = Field(..., description="Si se autoriza el envío del mensaje proactivo")
    reason: str = Field(..., description="Motivo de la decisión o rechazo")
    hours_since_last_ping: float = Field(..., description="Horas transcurridas desde el último mensaje de RICK")
    current_local_hour: int = Field(..., description="Hora local actual del usuario (0-23)")
    silence_streak: int = Field(default=0, description="Racha de mensajes proactivos sin respuesta del usuario")
    backoff_cooldown_hours: float = Field(default=24.0, description="Horas de espera obligatorias aplicadas")


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
    # Proactive loop extensions
    trigger_type: Optional[str]  # 'user_message', 'brand_health_audit', 'market_spark', 'trench_inquiry', 'post_mortem'
    proactive_context: Optional[Dict[str, Any]]
    brand_health_report: Optional[BrandHealthReport]
    proactive_spark: Optional[ProactiveSpark]
    governor_decision: Optional[GovernorDecision]
    # Multidimensional extensions
    series_metadata: Optional[SeriesMetadata]
    pilar: Optional[str]
    plan_id: Optional[str]
    # Episodic receipts
    story_bank: List[StoryReceipt]
    # Cognitive scratchpad trace
    reasoning_trace: Optional[StrategistReasoning]


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
        trigger_type="user_message",
        proactive_context={},
        brand_health_report=None,
        proactive_spark=None,
        governor_decision=None,
        series_metadata=None,
        pilar=None,
        plan_id=None,
        story_bank=[],
        reasoning_trace=None,
    )


def update_state(state: GraphState, **updates: Any) -> GraphState:
    """Pure functional update: returns a new copy of GraphState with updates applied."""
    new_state = state.copy()
    new_state.update(updates)
    return new_state

