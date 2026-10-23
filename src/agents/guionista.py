"""Technical script writer node (Hook, Desarrollo, Cierre/CTA)."""
import re
import json
from typing import Optional
from src.graph.state import (
    GraphState,
    ScriptDraft,
    ScriptBlock,
    WinningPattern,
    CreatorProfile,
    SeriesMetadata,
    StrategistReasoning,
    update_state,
)
from src.services.llm import llm_service

VISUAL_HOOK_MAX_WORDS = 9


def _clip_words(text: str, max_words: int = VISUAL_HOOK_MAX_WORDS) -> str:
    """Clip on-screen text to max_words so the visual hook stays readable in <1s."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,:;") + "..."


def generate_script_draft(
    story: str,
    pattern: WinningPattern,
    profile: Optional[CreatorProfile] = None,
    series: Optional[SeriesMetadata] = None,
    pilar: Optional[str] = None,
    plan_id: Optional[str] = None,
    previous_draft: Optional[ScriptDraft] = None,
    evaluation_feedback: Optional[str] = None,
    reasoning_trace: Optional[StrategistReasoning] = None,
) -> ScriptDraft:
    """
    Synthesize the creator's real story on top of the empirical winning pattern,
    generating the canonical 3 blocks: HOOK, DESARROLLO, CIERRE.
    Supports episodic continuity and cliffhangers when series metadata is present.
    If previous_draft and evaluation_feedback are provided, executes a targeted rewrite loop.
    """
    clean_story = (story or "").strip()
    hook_type = pattern.tipo_hook.lower()
    story_summary = clean_story.split('.')[0] if clean_story else "este quiebre clave"

    # Rewrite handling when previous draft failed evaluation
    if previous_draft is not None and evaluation_feedback:
        # Check if live LLM is enabled
        if not llm_service.is_test_env:
            try:
                rewrite_prompt = (
                    "REESCRITURA OBLIGATORIA POR RECHAZO DE CALIDAD:\n"
                    f"El editor rechazó el borrador anterior con el siguiente reporte:\n{evaluation_feedback}\n\n"
                    f"BORRADOR ANTERIOR RECHAZADO:\n"
                    f"- Hook hablado: {previous_draft.hook.texto}\n"
                    f"- Hook visual: {previous_draft.hook.visual_text or previous_draft.visual_hook}\n"
                    f"- Desarrollo: {previous_draft.desarrollo.texto}\n"
                    f"- Cierre: {previous_draft.cierre.texto}\n\n"
                    f"ÁNGULO CONTRARIAN A SOSTENER: {reasoning_trace.contrarian_angle if reasoning_trace else 'Directo de la experiencia real'}\n"
                    f"TRAMPAS CLICHÉ A EVITAR: {reasoning_trace.cliche_trap_to_avoid if reasoning_trace else 'Cero frases hechas'}\n\n"
                    "INSTRUCCIONES DE CORRECCIÓN:\n"
                    "1. Elimina completamente las frases penalizadas o los pasajes con coincidencia literal de referentes.\n"
                    "2. Asegura que el hook visual en pantalla contraste con el spoken hook (Dual-Coding).\n"
                    "3. Devuelve exclusivamente un JSON con las claves: titulo, hook_texto, hook_visual, desarrollo_texto, cierre_texto, friction_step."
                )
                raw_json = llm_service.generate(
                    prompt=rewrite_prompt,
                    system_prompt="Eres el Guionista Técnico Senior. Devuelve exclusivamente JSON sin markdown.",
                    model=llm_service.writer_model,
                    temperature=0.4,
                )
                data = json.loads(raw_json)
                return ScriptDraft(
                    titulo=data.get("titulo", previous_draft.titulo),
                    formato=previous_draft.formato,
                    duracion_objetivo=previous_draft.duracion_objetivo,
                    hook=ScriptBlock(
                        texto=data["hook_texto"],
                        intencion=previous_draft.hook.intencion,
                        camara=previous_draft.hook.camara,
                        visual_text=data.get("hook_visual", previous_draft.visual_hook),
                    ),
                    desarrollo=ScriptBlock(
                        texto=data["desarrollo_texto"],
                        intencion=previous_draft.desarrollo.intencion,
                        camara=previous_draft.desarrollo.camara,
                    ),
                    cierre=ScriptBlock(
                        texto=data["cierre_texto"],
                        intencion=previous_draft.cierre.intencion,
                        camara=previous_draft.cierre.camara,
                    ),
                    pilar=pilar or previous_draft.pilar,
                    series=series or previous_draft.series,
                    plan_id=plan_id or previous_draft.plan_id,
                    visual_hook=data.get("hook_visual", previous_draft.visual_hook),
                    spoken_hook=data["hook_texto"].strip(' "'),
                    friction_step=data.get("friction_step", previous_draft.friction_step),
                )
            except Exception:
                pass  # Fall through to deterministic rewrite

        # Deterministic rewrite path (tests and offline fallback)
        from src.agents.evaluator import FORBIDDEN_SLOP_PHRASES
        rev_hook = previous_draft.hook.texto
        rev_des = previous_draft.desarrollo.texto
        rev_cie = previous_draft.cierre.texto

        # Clean all detected slop phrases
        for phrase in FORBIDDEN_SLOP_PHRASES:
            p_re = re.compile(re.escape(phrase), re.IGNORECASE)
            rev_hook = p_re.sub("en mis propias operaciones", rev_hook)
            rev_des = p_re.sub("con datos reales de negocio", rev_des)
            rev_cie = p_re.sub("aplica este principio hoy", rev_cie)

        # Clean forbidden greetings
        for g in ["hola a todos", "bienvenidos", "hola amigos", "hey qué tal"]:
            g_re = re.compile(re.escape(g), re.IGNORECASE)
            rev_hook = g_re.sub("", rev_hook).strip()

        # If plagiarism or lack of contrast was flagged
        if "plagio" in evaluation_feedback.lower():
            contrarian = reasoning_trace.contrarian_angle if reasoning_trace else "Cometí un error en mi propia empresa"
            rev_hook = f'"{contrarian}: decidí cambiar el enfoque por completo."'
            rev_des = f"El fallo no fue de la herramienta sino mío. En vez de copiar fórmulas ajenas, delegar lo que no dominas es quemar capital: {clean_story or 'este quiebre clave'}."

        rev_visual = "el error que casi me cuesta el negocio."
        if rev_visual.lower() == rev_hook.lower().strip(' "')[:len(rev_visual)]:
            rev_visual = "la fantasía de delegar a ciegas."

        rev_visual = _clip_words(rev_visual)
        rev_spoken = rev_hook.strip(' "')

        return ScriptDraft(
            titulo=previous_draft.titulo,
            formato=previous_draft.formato,
            duracion_objetivo=previous_draft.duracion_objetivo,
            hook=ScriptBlock(
                texto=rev_hook,
                intencion="Desarmar objeción y capturar dolor con vulnerabilidad inmediata",
                camara=previous_draft.hook.camara or "Primer plano cerrado, directo al lente sin rodeos",
                visual_text=rev_visual,
            ),
            desarrollo=ScriptBlock(
                texto=rev_des,
                intencion="Construir autoridad con experiencia práctica y desmontar la causa raíz",
                camara=previous_draft.desarrollo.camara or "Plano medio a cámara, mirada fija, tono natural y directo",
            ),
            cierre=ScriptBlock(
                texto=rev_cie,
                intencion="Fijar el principio clave sin clichés promocionales",
                camara=previous_draft.cierre.camara or "Pausa de 1 segundo antes del corte a negro",
            ),
            pilar=pilar or previous_draft.pilar,
            series=series or previous_draft.series,
            plan_id=plan_id or previous_draft.plan_id,
            visual_hook=rev_visual,
            spoken_hook=rev_spoken,
            friction_step=previous_draft.friction_step or "delegar lo que no dominas es quemar capital sin aprender.",
        )

    # Formulate Hook
    if series is not None and series.episode_index > 1:
        hook_text = f"Ayer vimos la entrega anterior de {series.series_title}. Hoy en la parte {series.episode_index}: {story_summary}."
        hook_intencion = f"Continuidad narrativa episódica y puente con el episodio anterior"
    elif "confesion" in hook_type or "error" in hook_type:
        hook_text = f"Cometí un error grave con mi negocio: {story_summary.lower()}."
        hook_intencion = "Desarmar objeción y capturar dolor con vulnerabilidad inmediata"
    elif "quiebre" in hook_type or "creencia" in hook_type:
        hook_text = f"Nos enseñaron a creer que el camino era fácil, pero {story_summary.lower()}."
        hook_intencion = "Desafiar una creencia común y detener el scroll en el segundo cero"
    else:
        hook_text = f"La mayoría ignora esto: {story_summary}."
        hook_intencion = "Curiosidad informada y detención de scroll"

    # Refine hook text if story already starts with a strong personal punch and not in series episode > 1
    if (series is None or series.episode_index == 1) and (
        clean_story.startswith("Le pagué") or clean_story.startswith("Perdí") or clean_story.startswith("Contraté")
    ):
        first_sentence = clean_story.split(".")[0].strip()
        hook_text = f'"{first_sentence}."'

    # Formulate Desarrollo (the friction step is spoken verbatim as the belief break)
    friction_step = "delegar lo que no dominas es quemar capital sin aprender."
    story_body = clean_story.rstrip(".") if clean_story else "este quiebre clave"
    desarrollo_text = (
        f"El problema real no fue la herramienta, fue querer delegar lo que yo todavía no dominaba: "
        f"{friction_step} "
        f"Si tú no sabes explicar tu valor en una servilleta, nadie lo va a vender por ti: {story_body}."
    )
    desarrollo_intencion = "Construir autoridad con experiencia práctica y desmontar la causa raíz"
    desarrollo_camara = "Plano medio a cámara, mirada fija, tono natural y directo"

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
        cierre_intencion = "Fijar el principio clave sin clichés promocionales"
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
    visual_hook = _clip_words(visual_hook)

    # Spoken hook is always synchronized with the canonical hook block
    spoken_hook = hook_text.strip(' "')

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
    Supports criticism-guided rewriting when iteration_count > 0 and previous evaluation failed.
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

    # Feedback from previous evaluation if this is a rewrite iteration
    eval_result = state.get("evaluation")
    feedback = eval_result.feedback if (eval_result and not eval_result.passed) else None
    reasoning_trace = state.get("reasoning_trace")

    draft = generate_script_draft(
        story=story,
        pattern=pattern,
        profile=profile,
        series=series,
        pilar=pilar,
        plan_id=plan_id,
        previous_draft=existing_draft if (state.get("iteration_count", 0) > 0 and feedback) else None,
        evaluation_feedback=feedback,
        reasoning_trace=reasoning_trace,
    )

    iteration = state.get("iteration_count", 0) + 1

    return update_state(
        state,
        script_draft=draft,
        iteration_count=iteration,
        current_intent="evaluate_script",
    )
