"""Technical script writer node (Hook, Desarrollo, Cierre/CTA)."""
from typing import Optional
from src.graph.state import (
    GraphState,
    ScriptDraft,
    ScriptBlock,
    WinningPattern,
    CreatorProfile,
    SeriesMetadata,
    update_state,
)


def generate_script_draft(
    story: str,
    pattern: WinningPattern,
    profile: Optional[CreatorProfile] = None,
    series: Optional[SeriesMetadata] = None,
    pilar: Optional[str] = None,
    plan_id: Optional[str] = None,
) -> ScriptDraft:
    """
    Synthesize the creator's real story on top of the empirical winning pattern,
    generating the canonical 3 blocks: HOOK, DESARROLLO, CIERRE.
    Supports episodic continuity and cliffhangers when series metadata is present.
    """
    clean_story = (story or "").strip()
    hook_type = pattern.tipo_hook.lower()
    story_summary = clean_story.split('.')[0] if clean_story else "este quiebre clave"

    # Formulate Hook
    if series is not None and series.episode_index > 1:
        hook_text = f"Ayer vimos la entrega anterior de {series.series_title}. Hoy en la parte {series.episode_index}: {story_summary}."
        hook_intencion = f"Continuidad narrativa episódica y puente con el episodio anterior"
    elif "confesion" in hook_type or "error" in hook_type:
        hook_text = f"Cometí un error grave con mi negocio: {story_summary.lower()}."
        hook_intencion = "Desarmar objeción y capturar dolor con vulnerabilidad inmediata"
    elif "quiebre" in hook_type or "creencia" in hook_type:
        hook_text = f"Nos enseñaron a creer que el camino era fácil, pero {story_summary.lower()}."
        hook_intencion = "Quiebre de creencia y fricción cognitiva en el segundo cero"
    else:
        hook_text = f"La mayoría ignora esto: {story_summary}."
        hook_intencion = "Curiosidad informada y detención de scroll"

    # Refine hook text if story already starts with a strong personal punch and not in series episode > 1
    if (series is None or series.episode_index == 1) and (
        clean_story.startswith("Le pagué") or clean_story.startswith("Perdí") or clean_story.startswith("Contraté")
    ):
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
    if series is not None:
        if series.total_episodes is not None and series.episode_index < series.total_episodes:
            cierre_text = f"En la parte {series.episode_index + 1} te cuento la solución definitiva. Sígueme para no perdértela."
            cierre_intencion = f"Cliffhanger dramático y retención hacia el episodio {series.episode_index + 1}"
        elif series.total_episodes is None:
            cierre_text = f"En la parte {series.episode_index + 1} te cuento el siguiente paso. Sígueme para no perdértela."
            cierre_intencion = f"Cliffhanger dramático y retención hacia el episodio {series.episode_index + 1}"
        else:
            cierre_text = f"Esta fue la última parte de {series.series_title}. Guarda esta serie para repasarla completa."
            cierre_intencion = "Cierre de arco narrativo de saga y llamado a guardar la serie"
    else:
        cierre_text = "Antes de invertir para escalar, asegúrate de que tienes algo que funciona cuando estás tú solo."
        cierre_intencion = "Fijar la regla de oro sin clichés promocionales"
    cierre_camara = "Pausa de 1 segundo antes del corte a negro"

    if series is not None:
        titulo = f"{series.series_title} - Ep. {series.episode_index}"
    else:
        titulo = f"Lección: {pattern.tipo_hook.replace('_', ' ').title()}"

    # Formulate Visual Hook (Dual-Coding Contrast on screen)
    if series is not None:
        visual_hook = f"{series.series_title} (Parte {series.episode_index})"
    elif "confesion" in hook_type or "error" in hook_type:
        visual_hook = "el error que casi me cuesta el negocio."
    elif "quiebre" in hook_type or "creencia" in hook_type:
        visual_hook = "la fantasía de automatizarlo todo."
    else:
        visual_hook = "lo que nadie te dice de este juego."

    spoken_hook = hook_text.strip(' "')
    friction_step = "delegar lo que no dominas es quemar capital sin aprender."

    return ScriptDraft(
        titulo=titulo,
        formato="Reel",
        duracion_objetivo=45,
        hook=ScriptBlock(
            texto=hook_text,
            intencion=hook_intencion,
            camara="Primer plano cerrado, directo al lente sin rodeos",
            visual_text=visual_hook,
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
        pilar=pilar,
        series=series,
        plan_id=plan_id,
        visual_hook=visual_hook,
        spoken_hook=spoken_hook,
        friction_step=friction_step,
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
    
    # Retrieve multidimensional parameters if set in state or previous draft
    existing_draft = state.get("script_draft")
    series = existing_draft.series if existing_draft and existing_draft.series else state.get("series_metadata")
    pilar = existing_draft.pilar if existing_draft and existing_draft.pilar else state.get("pilar")
    plan_id = existing_draft.plan_id if existing_draft and existing_draft.plan_id else state.get("plan_id")

    draft = generate_script_draft(
        story=story,
        pattern=pattern,
        profile=profile,
        series=series,
        pilar=pilar,
        plan_id=plan_id,
    )

    iteration = state.get("iteration_count", 0) + 1

    return update_state(
        state,
        script_draft=draft,
        iteration_count=iteration,
        current_intent="evaluate_script",
    )
