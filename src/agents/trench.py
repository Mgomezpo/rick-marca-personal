"""Trench Inquiry Module for Inactivity Reactivation (Stanley Soapbox Ritual)."""
from typing import Optional
from src.graph.state import GraphState, StoryReceipt, update_state


def generate_trench_inquiry(handle: str, inactive_days: int = 3, receipt: Optional[StoryReceipt] = None) -> str:
    """
    Stanley-style Soapbox Ritual inquiry for creator reactivation:
    1. Sharp observation on creator's real stance and instinct.
    2. Contrast against what 90% of the industry does.
    3. Low-friction voice note CTA.
    Internal team voice: Head of Content checking in on the canal.
    """
    clean_handle = handle.lstrip("@")
    return (
        f"Oye {clean_handle}, algo que destaca en tu instinto es que no publicas por cumplir; "
        f"pero en el equipo llevamos casi dos días sin mover piezas en el canal.\n\n"
        f"Mientras el 90% de la gente copia plantillas genéricas de marketing, tu mejor contenido "
        f"siempre sale de resolver problemas reales en el día a día.\n\n"
        f"¿Qué fue lo más frustrante o inesperado que viviste hoy con un cliente o en tu código?\n\n"
        f"Mándame una nota de voz de 20 a 30 segundos sin filtros; de ahí sacamos el próximo guion."
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
