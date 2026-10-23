"""RICK Strategist orchestrator node, intelligent intent routing, and Heavy-Lifting creative guidance."""
import re
from typing import Optional, List
from src.graph.state import (
    GraphState,
    ConversationMessage,
    SeriesMetadata,
    StoryReceipt,
    update_state,
)
from src.services.llm import llm_service
from src.services.receipt_extractor import receipt_extractor_service
from src.agents.prompts import RICK_CANONICAL_SYSTEM_PROMPT


def classify_intent(user_message: str, current_state: GraphState) -> str:
    """
    Intelligent intent classification:
    - 'cold_onboarding': New tenant with empty story bank needing handle scan.
    - 'view_report': Account metrics, audit, learnings.
    - 'generate_script': Explicit script request, ready to script, or format choice (single vs saga).
    - 'blocked_creator': Writer's block, blank mind ("mente en blanco", "bloqueado").
    - 'meta_question': Questions about architecture, pricing, ChatGPT comparison, reset.
    - 'extract_story': Personal anecdotes, problems, lessons, ideas.
    - 'chat': Greetings, general dialogue, transitions.
    """
    msg = user_message.lower().strip()

    # Check for concrete story narrative markers first
    story_keywords = [
        "anécdota", "anecdota", "ayer", "problema", "cliente", "quebró", "quiebro",
        "fundé", "funde", "lección", "leccion", "error", "pasó", "paso",
        "decisión", "decision", "experiencia", "contraté", "contrate", "agencia",
        "reunión", "reunion", "lanzamiento", "venta", "ventas", "desesperé", "desespere"
    ]
    has_story_keywords = any(k in msg for k in story_keywords)

    # Intent: Blocked creator (Stanley-style heavy lifting trigger when no concrete story is provided)
    block_markers = [
        "mente en blanco", "bloqueado", "bloqueada", "sin ideas", "cero ideas", "no se me ocurre nada"
    ]
    if any(b in msg for b in block_markers) or (("no sé qué decir" in msg or "no sé qué grabar" in msg) and not has_story_keywords):
        return "blocked_creator"

    # Intent: Meta questions (architecture, comparison, pricing, reset)
    meta_markers = [
        "chatgpt", "claude", "como funcionas", "cómo funcionas", "tu arquitectura",
        "por qué tú", "por que tu", "1 dolar", "1 dólar", "$1", "regateo", "descuento",
        "precio", "costo", "/reset", "reset", "explica tu psicologia", "explica tu psicología"
    ]
    if any(m in msg for m in meta_markers):
        return "meta_question"

    # Intent: View report / metrics
    report_keywords = [
        "reporte", "métrica", "metrica", "estadística", "estadistica",
        "analytics", "learnings", "semanal", "cómo van", "rendimiento",
        "auditoría", "auditoria", "mi cuenta"
    ]
    if any(k in msg for k in report_keywords) and not ("guion" in msg or "script" in msg):
        return "view_report"

    # Intent: Generate script (including format decisions: single piece vs saga)
    script_keywords = [
        "guion", "guión", "script", "escribe", "escribeme", "escríbeme",
        "redacta", "grabar", "armemos el guion", "armar el guion", "crear el guion",
        "una sola", "sola pieza", "al grano", "saga", "miniserie", "2 partes", "dos partes"
    ]
    if any(k in msg for k in script_keywords):
        return "generate_script"

    # Intent: Story extraction
    if has_story_keywords or len(msg.split()) >= 10:
        return "extract_story"

    # Contextual continuation: if we are already extracting a story, stay in extraction unless pure greeting
    if current_state.get("current_intent") == "extract_story" and not any(g in msg for g in ["hola", "buen día", "buenas tardes"]):
        return "extract_story"

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
    Enforces Rubin & Stanley principles:
    - In production (live LLM): 100% of dialogue is generated dynamically via OpenAI/Gemini.
    - Socratic Heavy Lifting when creator is blocked.
    - Grounded in episodic receipts (story_bank).
    - Multi-tenant support with automatic cold onboarding for new tenants.
    - Fast deterministic mock path during unit tests.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for m in reversed(messages):
        if m.role == "user":
            last_user_message = m.content
            break

    profile = state.get("creator_profile")
    story_bank: List[StoryReceipt] = state.get("story_bank") or (profile.story_bank if profile else [])
    
    intent = classify_intent(last_user_message, state) if last_user_message else state.get("current_intent", "chat")

    # Multi-tenant Cold Onboarding check (Tenant #2 with empty receipts bank)
    handle_match = re.search(r"@([A-Za-z0-9_.-]+)", last_user_message)
    if not story_bank and handle_match:
        extracted_handle = handle_match.group(1)
        new_receipts = receipt_extractor_service.extract_receipts_from_content(
            creator_handle=extracted_handle,
            raw_text_or_posts=last_user_message,
        )
        story_bank = new_receipts
        if profile:
            profile.instagram_handle = extracted_handle
            profile.story_bank = new_receipts
        state["story_bank"] = new_receipts
        intent = "cold_onboarding"

    state_updates = {"current_intent": intent}

    # Extract accumulated story elements
    story = extract_story_elements(state)
    if story:
        state_updates["story_extracted"] = story

    if intent == "blocked_creator":
        state_updates["current_intent"] = "extract_story"

    # Analyze scene and friction markers
    scene_markers = ["reunión", "reunion", "oficina", "llamada", "pantalla", "apertura", "entró", "entro", "horas", "mirando", "estaba", "abrí", "abri"]
    has_scene = any(w in story.lower() for w in scene_markers) if story else False
    friction_markers = ["error", "errores", "fricción", "friccion", "fricciones", "no validé", "no valide", "quebró", "quebro", "mentira", "mi culpa", "la causa"]
    has_friction = any(w in story.lower() for w in friction_markers) if story else False

    # Check multi-point / saga condition
    multi_point_markers = [
        "dos errores", "2 errores", "tres errores", "3 errores",
        "dos cosas", "dos problemas", "múltiples", "varias lecciones",
        "dos partes", "2 partes", "varios puntos"
    ]
    is_multi_point = any(m in story.lower() for m in multi_point_markers) if story else False

    asked_saga_choice = any(
        "¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?" in m.content
        for m in messages if m.role == "assistant"
    )

    if intent == "extract_story" and has_scene and has_friction:
        if is_multi_point and not asked_saga_choice:
            state_updates["current_intent"] = "extract_story"
        else:
            state_updates["current_intent"] = "generate_script"

    # Configure saga or single piece metadata when transitioning to script
    if intent == "generate_script" or state_updates.get("current_intent") == "generate_script":
        last_user_lower = last_user_message.lower() if last_user_message else ""
        saga_markers = ["saga", "miniserie", "2 partes", "dos partes", "segunda parte"]
        wants_saga = any(m in last_user_lower for m in saga_markers)
        single_markers = ["una sola", "sola pieza", "al grano", "una pieza"]
        wants_single = any(m in last_user_lower for m in single_markers)

        if wants_saga and not wants_single:
            clean_title = story.split('.')[0].strip()[:40] if story else "Saga de Negocios"
            clean_title = re.sub(r'^(en\s+la\s+|en\s+el\s+|el\s+|la\s+)', '', clean_title, flags=re.IGNORECASE).title()
            series = SeriesMetadata(
                series_id=f"saga_{state.get('user_id', 'user')}_{abs(hash(story)) % 10000}",
                series_title=clean_title or "Saga de Negocios",
                episode_index=1,
                total_episodes=2,
            )
            state_updates["series_metadata"] = series
        else:
            state_updates["series_metadata"] = None

    # -------------------------------------------------------------
    # PATH A: LIVE PRODUCTION GENERATION (100% LLM Call)
    # -------------------------------------------------------------
    if not llm_service.is_test_env:
        receipts_str = "\n".join(
            [f"- [{r.id}] {r.theme}: {r.summary} | Detalles: {', '.join(r.concrete_details)} | Conclusión: {r.punchline}" for r in story_bank]
        ) if story_bank else "Sin recibos previos (Usuario nuevo en onboarding)."
        history_str = "\n".join([f"{m.role.upper()}: {m.content}" for m in messages[-6:]])
        handle = profile.instagram_handle if profile else state.get("user_id", "creador")

        prompt = (
            f"PERFIL DEL CREADOR: @{handle} | Nicho: {profile.nicho if profile else 'General'}\n"
            f"RECIBOS REALES EN MEMORIA (LORE):\n{receipts_str}\n\n"
            f"HISTORIAL RECIENTE:\n{history_str}\n\n"
            f"ÚLTIMO MENSAJE DEL CREADOR: '{last_user_message}'\n\n"
            f"INTENCIÓN DETECTADA: {intent}\n"
            f"INSTRUCCIONES CLAVE:\n"
            f"- Si el creador no tiene recibos y acaba de entrar: dale la bienvenida al equipo y pídele su @ de Instagram para escanearlo.\n"
            f"- Si el creador tiene la mente en blanco o está bloqueado: haz el heavy lifting, proponle 2 opciones concretas basadas en sus propios recibos.\n"
            f"- Si hace preguntas meta (ChatGPT vs RICK, precios, arquitectura, /reset): responde con ingenio y anclaje en sus proyectos reales y redirígelo al guion.\n"
            f"- Si comparte una anécdota: profundiza en la fricción real y sugiere estructurar el guion (o saga de 2 partes si es densa).\n"
            f"- Tono: Head of Content, socio interno del equipo, directo, cero relleno corporativo, cero clichés de IA.\n\n"
            f"Responde como RICK directamente al creador:"
        )

        response = llm_service.generate(prompt=prompt, system_prompt=RICK_CANONICAL_SYSTEM_PROMPT, temperature=0.7)
        state_updates["final_response"] = response
        return update_state(state, **state_updates)

    # -------------------------------------------------------------
    # PATH B: DETERMINISTIC MOCK PATH (Unit Testing / Fast CI)
    # -------------------------------------------------------------
    if intent == "cold_onboarding":
        handle = profile.instagram_handle if profile else "creador"
        response = (
            f"¡qué más @{handle.lstrip('@')}! ya escaneé tu cuenta y tengo tus primeras historias reales listas para grabar. "
            f"¿qué problema o experiencia con clientes trabajamos hoy para el próximo guion?"
        )

    elif intent == "blocked_creator":
        if story_bank and len(story_bank) >= 2:
            s1 = story_bank[0]
            s2 = story_bank[1]
            response = (
                "tranquilo, no tienes que inventar nada de cero hoy. ya tienes historias reales listas para grabar:\n\n"
                f"1. {s1.theme.capitalize()}: {s1.summary}.\n"
                f"2. {s2.theme.capitalize()}: {s2.summary}.\n\n"
                "dime cuál te vibra más y yo hago el trabajo pesado de estructurar el gancho visual y el quiebre."
            )
        else:
            response = (
                "tranquilo, no tienes que inventar nada de cero hoy. ya tienes historias reales listas:\n\n"
                "1. Por qué seguir playbooks de marketing mata tu voz (la razón por la que creaste a RICK e Ireal).\n"
                "2. La automatización de 30 min con macros de Excel para la clínica dental de tu papá.\n\n"
                "dime cuál te vibra más y montamos el quiebre de inmediato."
            )

    elif intent == "meta_question":
        prompt = (
            f"El creador te pregunta: '{last_user_message}'.\n"
            f"Responde con agudeza e inteligencia desde tu identidad RICK. Usa sus recibos reales si aplica y redirígelo al guion."
        )
        response = llm_service.generate(prompt=prompt, system_prompt=RICK_CANONICAL_SYSTEM_PROMPT)

    elif intent == "chat":
        response = (
            "Buen día. En el equipo tenemos los referentes y números al día. "
            "¿Qué problema o anécdota real con clientes trabajamos hoy para el canal?"
        )

    elif intent == "extract_story":
        if not has_scene:
            response = "¿Qué pasó exactamente en ese momento? Cuéntame la escena sin adornos."
        elif not has_friction:
            response = "¿Cuál fue el error o la fricción que nadie vio en esa decisión?"
        elif is_multi_point and not asked_saga_choice:
            response = "¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?"
        else:
            response = "¿Quieres que montemos el guion sobre este quiebre?"

    elif intent == "view_report":
        response = "Revisemos cómo cerramos la semana y los aprendizajes en nuestro canal."

    elif intent == "generate_script":
        if state_updates.get("series_metadata"):
            response = "Listo. Convoquemos al guionista para estructurar la saga en 2 partes con ganchos continuos."
        else:
            response = "Listo. Convoquemos al guionista para estructurar la pieza en 3 bloques."
    else:
        response = "¿Qué problema o experiencia real trabajamos hoy?"

    state_updates["final_response"] = response
    return update_state(state, **state_updates)
