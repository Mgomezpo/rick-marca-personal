"""Proactive Worker Service for Autonomous Engine Cycles."""
from typing import Dict, Any, Optional
from src.graph.state import (
    GraphState,
    CreatorProfile,
    create_initial_state,
    update_state,
)
from src.graph.engine import RickGraphEngine


def run_proactive_cycle_for_tenant(
    user_id: str,
    trigger_type: str,
    creator_profile: Optional[CreatorProfile] = None,
    proactive_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes a single proactive cycle for a tenant:
    1. Instantiates state with proactive trigger and context.
    2. Runs RickGraphEngine.
    3. Evaluates governor decision: if rejected, logs and aborts without sending.
    4. If approved and message produced: returns message ready for outbound delivery.
    """
    handle = creator_profile.instagram_handle if creator_profile else f"creator_{user_id}"
    state = create_initial_state(user_id=user_id, handle=handle)

    if creator_profile:
        state = update_state(state, creator_profile=creator_profile)

    state = update_state(
        state,
        trigger_type=trigger_type,
        proactive_context=proactive_context or {},
    )

    engine = RickGraphEngine()
    final_state = engine.run(state)

    decision = final_state.get("governor_decision")
    allowed = decision.allowed if decision else False
    reason = decision.reason if decision else "No decision evaluated"
    response_text = final_state.get("final_response")

    if not allowed or not response_text:
        return {
            "user_id": user_id,
            "trigger_type": trigger_type,
            "dispatched": False,
            "governor_allowed": allowed,
            "reason": reason,
            "message": None,
        }

    return {
        "user_id": user_id,
        "trigger_type": trigger_type,
        "dispatched": True,
        "governor_allowed": True,
        "reason": reason,
        "message": response_text,
    }
