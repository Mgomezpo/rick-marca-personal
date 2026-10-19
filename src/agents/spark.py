"""Proactive Sparks and High-Leverage Contributions Module (Proactive Loop B)."""
from typing import Optional
from src.graph.state import (
    ProactiveSpark,
    WinningPattern,
    GraphState,
    update_state,
)


def generate_proactive_spark(
    creator_handle: str,
    creator_nicho: str,
    winning_pattern: WinningPattern,
    creator_thesis: str,
    source_referent: str = "@referente",
) -> ProactiveSpark:
    """
    Synthesizes a market anomaly from a referent into an adapted, unsolicited
    script idea grounded in the creator's specific thesis.
    """
    hook_type = winning_pattern.tipo_hook
    mult = winning_pattern.rendimiento_relativo_promedio

    if "revelacion" in hook_type or "contraria" in hook_type:
        suggested_hook = (
            f"Te vendieron la fantasía de automatizarlo todo con 10 agentes. "
            f"La realidad es que un solo state graph bien diseñado resuelve el 90%."
        )
        adapted_angle = f"Desmontar el hype de agentes múltiples frente a la tesis: '{creator_thesis}'."
    elif "mecanismo" in hook_type:
        suggested_hook = (
            f"Te muestro en 30 segundos el circuito exacto de nodos y memoria "
            f"que usamos para que el bot no alucine ni mande spam."
        )
        adapted_angle = f"Demostración de mecanismo aplicada a: '{creator_thesis}'."
    else:
        suggested_hook = f"El error más costoso que veo en {creator_nicho} cuando intentan escalar."
        adapted_angle = f"Fricción de trinchera respaldada por: '{creator_thesis}'."

    return ProactiveSpark(
        spark_id=f"spark_{winning_pattern.pattern_id}",
        source_referent=source_referent,
        referent_hook_text=winning_pattern.ejemplos[0] if winning_pattern.ejemplos else "Hook ganador",
        relative_performance=mult,
        adapted_angle=adapted_angle,
        suggested_hook=suggested_hook,
        target_pillar="Arquitectura de Sistemas",
        confidence=0.91,
    )


def format_spark_whatsapp(spark: ProactiveSpark, handle: str) -> str:
    """
    Formats the proactive spark into a high-resonance WhatsApp pitch.
    Internal team voice: Head of Content bringing an opportunity from the team's radar.
    """
    clean_handle = handle.lstrip("@")
    return (
        f"Oye {clean_handle}, en el radar del equipo vimos que {spark.source_referent} pegó un pico de "
        f"*{spark.relative_performance:.1f}x* sobre su mediana con este gancho:\n"
        f'"{spark.referent_hook_text}"\n\n'
        f"Lo bajé a nuestra tesis:\n"
        f'👉 *"{spark.suggested_hook}"*\n\n'
        f"Ya tiene tracción validada en el mercado. ¿Le damos luz verde para armar el próximo guion?"
    )


def proactive_spark_node(state: GraphState) -> GraphState:
    """Graph node for generating proactive spark contributions."""
    gov = state.get("governor_decision")
    if gov and not gov.allowed:
        return state

    user_id = state.get("user_id", "default_user")
    creator_profile = state.get("creator_profile")
    handle = creator_profile.instagram_handle if creator_profile else f"creator_{user_id}"
    nicho = creator_profile.nicho if creator_profile else "Tecnología"

    ctx = state.get("proactive_context") or {}
    pattern = ctx.get("winning_pattern")
    source_ref = ctx.get("source_referent", "@referente")
    thesis = ctx.get("thesis", "Sistemas determinísticos sobre caos")

    if not pattern:
        # Fallback synthetic pattern if none supplied
        pattern = WinningPattern(
            pattern_id="fallback_spark",
            tipo_hook="revelacion_contraria",
            formato="Reel",
            emocion="intriga",
            rendimiento_relativo_promedio=2.3,
            piezas_respaldo=3,
            ejemplos=["La verdad sobre las automatizaciones que nadie te dice"],
        )

    spark = generate_proactive_spark(
        creator_handle=handle,
        creator_nicho=nicho,
        winning_pattern=pattern,
        creator_thesis=thesis,
        source_referent=source_ref,
    )

    formatted = format_spark_whatsapp(spark, handle)

    return update_state(
        state,
        proactive_spark=spark,
        final_response=formatted,
    )
