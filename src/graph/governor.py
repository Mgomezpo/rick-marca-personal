"""Anti-Spam Governor and Cadence Controller for Proactive Loops."""
from typing import Dict, Any, Optional
from src.graph.state import GraphState, GovernorDecision, update_state


def evaluate_governor(
    user_id: str,
    trigger_type: str,
    hours_since_last_ping: float,
    current_local_hour: float,
    silence_streak: int = 0,
    confidence: float = 0.9,
    current_local_minute: int = 0,
) -> GovernorDecision:
    """
    Evaluates whether a proactive outreach is permitted or should be suppressed.
    Rules:
    1. User-initiated messages always bypass the governor.
    2. Quiet hours: Proactive pings only allowed between 09:00 and 19:00 local time.
    3. Trench inquiry: Strictly between 17:00 and 19:30 local time (end of day).
    4. Minimum SNR: Confidence must be >= 0.85.
    5. Base cooldown: 24 hours for spark/health, 42 hours for trench inquiry.
    6. Ignored pings apply progressive backoff (1 ping -> 48h, 2+ pings -> 96h).
    """
    if trigger_type == "user_message":
        return GovernorDecision(
            allowed=True,
            reason="Mensaje iniciado por el usuario; no aplica gobernador.",
            hours_since_last_ping=hours_since_last_ping,
            current_local_hour=current_local_hour,
            silence_streak=silence_streak,
            backoff_cooldown_hours=0.0,
        )

    time_in_hours = float(current_local_hour) + (float(current_local_minute) / 60.0)

    # 1. Quiet Hours check for regular proactive triggers (09:00 to 19:00)
    if trigger_type != "trench_inquiry":
        if time_in_hours < 9.0 or time_in_hours > 19.0:
            return GovernorDecision(
                allowed=False,
                reason=f"Fuera de ventana hábil (09:00 a 19:00). Hora actual: {int(current_local_hour):02d}:{int(current_local_minute):02d}.",
                hours_since_last_ping=hours_since_last_ping,
                current_local_hour=current_local_hour,
                silence_streak=silence_streak,
                backoff_cooldown_hours=24.0,
            )

    # 2. SNR Threshold check
    if confidence < 0.85:
        return GovernorDecision(
            allowed=False,
            reason=f"Confianza insuficiente del patrón ({confidence:.2f} < 0.85).",
            hours_since_last_ping=hours_since_last_ping,
            current_local_hour=current_local_hour,
            silence_streak=silence_streak,
            backoff_cooldown_hours=24.0,
        )

    # 3. Progressive Backoff calculation based on silence streak and trigger type
    if trigger_type == "trench_inquiry":
        # Inactivity inquiry requires 42 hours minimum
        base_cooldown = 42.0
    else:
        base_cooldown = 24.0

    if silence_streak == 0:
        required_cooldown = base_cooldown
    elif silence_streak == 1:
        required_cooldown = max(48.0, base_cooldown)
    else:
        required_cooldown = max(96.0, base_cooldown)

    if hours_since_last_ping < required_cooldown:
        return GovernorDecision(
            allowed=False,
            reason=(
                f"Cooldown activo (backoff por silencio={silence_streak}): "
                f"requeridas {required_cooldown:.1f}h, transcurridas {hours_since_last_ping:.1f}h."
            ),
            hours_since_last_ping=hours_since_last_ping,
            current_local_hour=current_local_hour,
            silence_streak=silence_streak,
            backoff_cooldown_hours=required_cooldown,
        )

    # 4. End-of-day timing for trench inquiry (17:00 to 19:30)
    if trigger_type == "trench_inquiry" and (time_in_hours < 17.0 or time_in_hours > 19.5):
        return GovernorDecision(
            allowed=False,
            reason=(
                f"Indagación de trinchera programada para el final de la jornada (17:00 a 19:30). "
                f"Hora actual: {int(current_local_hour):02d}:{int(current_local_minute):02d}."
            ),
            hours_since_last_ping=hours_since_last_ping,
            current_local_hour=current_local_hour,
            silence_streak=silence_streak,
            backoff_cooldown_hours=required_cooldown,
        )

    return GovernorDecision(
        allowed=True,
        reason="Ventana hábil, cooldown y umbral de calidad aprobados.",
        hours_since_last_ping=hours_since_last_ping,
        current_local_hour=current_local_hour,
        silence_streak=silence_streak,
        backoff_cooldown_hours=required_cooldown,
    )



def governor_node(state: GraphState) -> GraphState:
    """
    Graph node that enforces proactive limits before executing any outreach.
    """
    user_id = state.get("user_id", "default_user")
    trigger_type = state.get("trigger_type", "user_message")
    ctx = state.get("proactive_context") or {}

    hours_since_last_ping = float(ctx.get("hours_since_last_ping", 48.0))
    current_local_hour = float(ctx.get("current_local_hour", 11))
    current_local_minute = int(ctx.get("current_local_minute", 0))
    silence_streak = int(ctx.get("silence_streak", 0))
    confidence = float(ctx.get("confidence", 0.90))

    decision = evaluate_governor(
        user_id=user_id,
        trigger_type=trigger_type,
        hours_since_last_ping=hours_since_last_ping,
        current_local_hour=current_local_hour,
        silence_streak=silence_streak,
        confidence=confidence,
        current_local_minute=current_local_minute,
    )

    return update_state(state, governor_decision=decision)

