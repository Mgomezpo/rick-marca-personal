"""Technical script writer node (Hook, Desarrollo, Cierre/CTA)."""
from typing import Optional
from src.graph.state import (
    GraphState,
    ScriptDraft,
    ScriptBlock,
    WinningPattern,
    CreatorProfile,
    update_state,
)


def generate_script_draft(
    story: str,
    pattern: WinningPattern,
    profile: Optional[CreatorProfile] = None,
) -> ScriptDraft:
    """
    Synthesize the creator's real story on top of the empirical winning pattern,
    generating the canonical 3 blocks: HOOK, DESARROLLO, CIERRE.
    """
    clean_story = story.strip()
    hook_type = pattern.tipo_hook.lower()

    # Formulate Hook
    if "confesion" in hook_type or "error" in hook_type:
        hook_text = f"Cometí un error grave con mi negocio: {clean_story.split('.')[0].lower()}."
        hook_intencion = "Desarmar objeción y capturar dolor con vulnerabilidad inmediata"
    elif "quiebre" in hook_type or "creencia" in hook_type:
        hook_text = f"Nos enseñaron a creer que el camino era fácil, pero {clean_story.split('.')[0].lower()}."
        hook_intencion = "Quiebre de creencia y fricción cognitiva en el segundo cero"
    else:
        hook_text = f"La mayoría ignora esto: {clean_story.split('.')[0]}."
        hook_intencion = "Curiosidad informada y detención de scroll"

    # Refine hook text if story already starts with a strong personal punch
    if clean_story.startswith("Le pagué") or clean_story.startswith("Perdí") or clean_story.startswith("Contraté"):
        first_sentence = clean_story.split(".")[0].strip()
        hook_text = f'"{first_sentence}."'

    # Formulate Desarrollo
    desarrollo_text = (
        f"El problema real no fue la herramienta, fue querer delegar lo que yo todavía no dominaba. "
        f"Si tú no sabes explicar tu valor en una servilleta, nadie lo va a vender por ti: {clean_story}."
    )
    desarrollo_intencion = "Construir autoridad de trinchera y desmontar la causa raíz"
    desarrollo_camara = "Plano medio relajado, mirada fija, tono de café de socio a socio"

    # Formulate Cierre / CTA
    cierre_text = "Antes de invertir para escalar, asegúrate de que tienes algo que funciona cuando estás tú solo."
    cierre_intencion = "Fijar la regla de oro sin clichés promocionales"
    cierre_camara = "Pausa de 1 segundo antes del corte a negro"

    titulo = pattern.tipo_hook.replace("_", " ").title()

    return ScriptDraft(
        titulo=f"Lección: {titulo}",
        formato="Reel",
        duracion_objetivo=45,
        hook=ScriptBlock(
            texto=hook_text,
            intencion=hook_intencion,
            camara="Primer plano cerrado, directo al lente sin rodeos",
        ),
        desarrollo=ScriptBlock(
            texto=desarrollo_text,
            intencion=desarrollo_intencion,
            camara=desarrollo_camara,
        ),
        cierre=ScriptBlock(
            texto=cierre_text,
            intencion=cierre_intencion,
            camara=cierre_camara,
        ),
    )


def guionista_node(state: GraphState) -> GraphState:
    """
    Graph node that generates or refines the technical script draft.
    """
    story = state.get("story_extracted") or ""
    if not story and state.get("messages"):
        user_msgs = [m.content for m in state["messages"] if m.role == "user"]
        story = " ".join(user_msgs)

    patterns = state.get("winning_patterns", [])
    if patterns:
        pattern = patterns[0]
    else:
        pattern = WinningPattern(
            pattern_id="pat_default",
            tipo_hook="confesion_error",
            formato="historia_personal",
            emocion="vulnerabilidad",
            rendimiento_relativo_promedio=2.2,
            piezas_respaldo=5,
        )

    profile = state.get("creator_profile")
    draft = generate_script_draft(story=story, pattern=pattern, profile=profile)

    iteration = state.get("iteration_count", 0) + 1

    return update_state(
        state,
        script_draft=draft,
        iteration_count=iteration,
        current_intent="evaluate_script",
    )
