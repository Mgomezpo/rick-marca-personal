"""Unified Channel-Agnostic Session Runner for RICK Multitenant Engine."""
import logging
from typing import Optional, List
from src.db.repository import SupabaseRepository
from src.graph.engine import RickGraphEngine
from src.graph.state import ConversationMessage, create_initial_state

logger = logging.getLogger("rick.session_runner")
repo = SupabaseRepository()
engine = RickGraphEngine()


def compress_conversation_window(
    messages: List[ConversationMessage],
    max_recent: int = 10,
    threshold: int = 12,
) -> List[ConversationMessage]:
    """
    Compresses conversation history when length exceeds threshold.
    Older turns are synthesized into a single compact context message,
    while keeping the most recent `max_recent` messages intact.
    """
    if len(messages) <= threshold:
        return messages

    older_messages = messages[:-max_recent]
    recent_messages = messages[-max_recent:]

    summary_snippets = []
    for m in older_messages:
        prefix = "Usuario" if m.role == "user" else "RICK"
        content_preview = m.content.strip().replace("\n", " ")
        if len(content_preview) > 80:
            content_preview = content_preview[:77] + "..."
        summary_snippets.append(f"{prefix}: {content_preview}")

    summary_text = (
        f"[Contexto de conversación previa comprimido ({len(older_messages)} mensajes)]: "
        + "; ".join(summary_snippets)
    )

    synthetic_summary_message = ConversationMessage(
        role="system",
        content=summary_text,
    )

    return [synthetic_summary_message] + recent_messages


def process_user_turn(
    user_id: str,
    handle: str,
    text: str,
    channel: str = "telegram",
    timestamp: Optional[str] = None,
    repo_override: Optional[SupabaseRepository] = None,
    engine_override: Optional[RickGraphEngine] = None,
) -> str:
    """
    Executes a single conversational or command turn through the RICK LangGraph engine.
    Channel-agnostic: Works identically for Telegram and WhatsApp.
    
    1. Loads creator profile & episodic story receipts from Supabase.
    2. Loads previous conversation history and appends current user message.
    3. Runs RickGraphEngine (Stanley architecture, dual-coding, heavy lifting, zero-slop).
    4. Persists learnings, pieces, and assistant reply to Supabase.
    5. Returns final_response string.
    """
    active_repo = repo_override or repo
    active_engine = engine_override or engine

    try:
        profile = active_repo.get_creator_profile(user_id)
        state = create_initial_state(user_id=user_id, handle=handle)

        if profile:
            state["creator_profile"] = profile
            state["story_bank"] = profile.story_bank
        else:
            state["story_bank"] = active_repo.get_story_bank(user_id)

        # Load previous learnings
        state["learnings"] = active_repo.get_learnings(user_id)

        # Persist incoming user message
        user_msg = ConversationMessage(
            role="user",
            content=text,
            timestamp=timestamp or "",
        )
        active_repo.save_message(user_id, user_msg)
        raw_conversation = active_repo.get_conversation(user_id)
        state["messages"] = compress_conversation_window(raw_conversation, max_recent=10, threshold=12)

        # Execute State Graph Engine
        final_state = active_engine.run(state)

        # Save any new learnings generated
        for learning in final_state.get("learnings", []):
            active_repo.save_learning(learning)

        # Save script piece if produced
        draft = final_state.get("script_draft")
        if draft:
            active_repo.save_piece(user_id, draft)

        # Persist assistant reply
        final_response = final_state.get("final_response") or "Entendido. Sigamos avanzando con el guion."
        assistant_msg = ConversationMessage(
            role="assistant",
            content=final_response,
        )
        active_repo.save_message(user_id, assistant_msg)

        logger.info(f"[{channel.upper()}] Processed turn for {user_id}: response generated successfully.")
        return final_response

    except Exception as e:
        logger.error(f"[{channel.upper()}] Error processing turn for {user_id}: {e}", exc_info=True)
        return "Disculpa, hubo una interferencia técnica en la mesa. ¿Me repites la última frase?"
