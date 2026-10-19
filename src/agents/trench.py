"""Trench Inquiry Module for Inactivity Reactivation (Proactive Loop C)."""
from src.graph.state import GraphState, update_state


def generate_trench_inquiry(handle: str, inactive_days: int = 3) -> str:
    """
    Formulates a sharp, reflective question to pull a raw story out of the creator's real day.
    Rubin mayeutics: authentic, non-judgmental, curious.
    Internal team voice: Head of Content checking in on the canal.
    """
    clean_handle = handle.lstrip("@")
    return (
        f"Oye {clean_handle}, en el equipo llevamos casi dos días sin mover piezas en el canal.\n\n"
        f"¿Qué fue lo más frustrante o inesperado que te pasó hoy con un cliente o en tu código?\n\n"
        f"Grábame una nota de voz de 30 segundos sin filtros; de ahí sacamos el próximo guion."
    )


def trench_inquiry_node(state: GraphState) -> GraphState:
    """Graph node for dormant creator reactivation inquiry."""
    gov = state.get("governor_decision")
    if gov and not gov.allowed:
        return state

    user_id = state.get("user_id", "default_user")
    creator_profile = state.get("creator_profile")
    handle = creator_profile.instagram_handle if creator_profile else f"creator_{user_id}"

    ctx = state.get("proactive_context") or {}
    inactive_days = int(ctx.get("inactive_days", 3))

    message = generate_trench_inquiry(handle, inactive_days)

    return update_state(
        state,
        final_response=message,
    )
