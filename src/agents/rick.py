"""RICK Strategist orchestrator node, intent classification, and Rubin mayeutic inquiry."""
import re
from typing import Optional
from src.graph.state import GraphState, ConversationMessage, update_state


def classify_intent(user_message: str, current_state: GraphState) -> str:
    """
    Classify the user intent into one of 4 canonical pathways:
    1. 'view_report': Account metrics, audit, learnings.
    2. 'generate_script': Explicit script request or ready to script.
    3. 'extract_story': Personal anecdotes, problems, lessons, ideas.
    4. 'chat': Greetings, general dialogue, transitions.
    """
    msg = user_message.lower().strip()

    # Intent 1: View report / metrics
    report_keywords = [
        "reporte", "métrica", "metrica", "estadística", "estadistica",
        "analytics", "learnings", "semanal", "cómo van", "rendimiento",
        "auditoría", "auditoria", "mi cuenta"
    ]
    if any(k in msg for k in report_keywords) and not ("guion" in msg or "script" in msg):
        return "view_report"

    # Intent 2: Generate script
    script_keywords = [
        "guion", "guión", "script", "escribe", "escribeme", "escríbeme",
        "redacta", "grabar", "armemos el guion", "armar el guion", "crear el guion"
    ]
    if any(k in msg for k in script_keywords):
        return "generate_script"

    # Intent 3: Story extraction (anecdote, problem, business lesson)
    story_keywords = [
        "anécdota", "anecdota", "ayer", "problema", "cliente", "quebró", "quiebro",
        "fundé", "funde", "lección", "leccion", "error", "pasó", "paso",
        "decisión", "decision", "experiencia", "contraté", "contrate", "agencia"
    ]
    if any(k in msg for k in story_keywords) or len(msg.split()) > 15:
        return "extract_story"

    # Intent 4: Chat fallback
    return "chat"


def extract_story_elements(state: GraphState) -> str:
    """Accumulates and extracts user-shared narrative elements from messages."""
    user_turns = [
        m.content for m in state.get("messages", [])
        if m.role == "user"
    ]
    return " ".join(user_turns).strip()


def rick_strategist_node(state: GraphState) -> GraphState:
    """
    Main RICK strategist conversation node.
    Enforces Rubin principles: concise, 1 question per inquiry turn, no AI filler.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for m in reversed(messages):
        if m.role == "user":
            last_user_message = m.content
            break

    intent = classify_intent(last_user_message, state) if last_user_message else state.get("current_intent", "chat")
    state_updates = {"current_intent": intent}

    if intent == "chat":
        response = (
            "Buen día. Tengo tus referentes y tus números presentes. "
            "¿Qué tema o anécdota de trinchera quieres trabajar hoy?"
        )
        state_updates["final_response"] = response

    elif intent == "extract_story":
        story = extract_story_elements(state)
        state_updates["story_extracted"] = story

        # Rubin Protocol: Trench inquiry (1 question per turn)
        # Check if user already gave the scene
        has_scene = any(w in story.lower() for w in ["reunión", "reunion", "oficina", "llamada", "momento", "pantalla", "cliente", "ayer", "cuando"])
        # Check if user gave the friction
        has_friction = any(w in story.lower() for w in ["error", "fricción", "friccion", "quebró", "perdí", "ventas", "mentira", "casi"])

        if not has_scene:
            response = "¿Qué pasó exactamente en ese momento? Cuéntame la escena sin adornos."
        elif not has_friction:
            response = "¿Cuál fue el error o la fricción que nadie vio en esa decisión?"
        else:
            # Both present: stop inquiry immediately and transition to script writing
            state_updates["current_intent"] = "generate_script"
            response = "¿Quieres que montemos el guion sobre este quiebre?"

        state_updates["final_response"] = response

    elif intent == "view_report":
        state_updates["final_response"] = "Preparando la auditoría de tu cuenta y los aprendizajes de la semana."

    elif intent == "generate_script":
        state_updates["final_response"] = "Listo. Convocando al guionista técnico para armar la estructura en 3 bloques."

    return update_state(state, **state_updates)
