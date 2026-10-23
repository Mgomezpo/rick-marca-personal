"""Brand Health and Personal Brand Audit Module (Proactive Loop A)."""
from typing import List, Dict, Any, Optional
from src.graph.state import (
    BrandHealthReport,
    BrandPillarDistribution,
    GraphState,
    update_state,
)


def analyze_brand_health(
    user_id: str,
    recent_posts: List[Dict[str, Any]],
    declared_pillars: List[Dict[str, Any]],
) -> BrandHealthReport:
    """
    Audits the creator's recent post distribution against their declared brand pillars.
    Detects abandoned pillars, over-indexing, and voice drift.
    """
    total_posts = len(recent_posts)
    pillar_counts: Dict[str, int] = {p["name"]: 0 for p in declared_pillars}

    for post in recent_posts:
        post_pillar = post.get("pillar")
        if post_pillar in pillar_counts:
            pillar_counts[post_pillar] += 1

    distributions: List[BrandPillarDistribution] = []
    has_deserted = False
    has_over_indexed = False

    for p in declared_pillars:
        name = p["name"]
        target = float(p.get("target_pct", 50.0))
        count = pillar_counts.get(name, 0)
        actual = (count / total_posts * 100.0) if total_posts > 0 else 0.0

        if actual == 0.0 and target > 0.0:
            status = "deserted"
            has_deserted = True
        elif actual > (target + 25.0):
            status = "over_indexed"
            has_over_indexed = True
        else:
            status = "balanced"

        distributions.append(
            BrandPillarDistribution(
                pillar_name=name,
                target_percentage=target,
                actual_percentage=round(actual, 1),
                post_count=count,
                status=status,
            )
        )

    # Calculate overall health score
    score = 9.0
    if has_deserted:
        score -= 2.5
    if has_over_indexed:
        score -= 1.0

    score = max(1.0, min(10.0, score))
    voice_drift = has_deserted or has_over_indexed

    drift_notes = ""
    deserted_pillar = next((d.pillar_name for d in distributions if d.status == "deserted"), None)
    if deserted_pillar:
        drift_notes = (
            f"El pilar central '{deserted_pillar}' no tiene piezas recientes. "
            f"Tu audiencia puede percibir falta de profundidad o cambio de foco."
        )
        recommendation = f"Equilibrar el canal produciendo una demostración técnica de {deserted_pillar}."
        action = "crear_demostracion_mecanismo"
    else:
        drift_notes = "Distribución saludable entre tus pilares estratégicos."
        recommendation = "Mantén el ritmo actual y refuerza con historias reales o casos de tus clientes."
        action = "mantener_ritmo"

    return BrandHealthReport(
        user_id=user_id,
        overall_score=round(score, 1),
        pillars=distributions,
        voice_drift_detected=voice_drift,
        voice_drift_notes=drift_notes,
        key_recommendation=recommendation,
        suggested_action=action,
    )


def format_brand_health_whatsapp(report: BrandHealthReport, handle: str) -> str:
    """
    Formats the brand audit as a direct, high-value WhatsApp observation.
    Internal team voice: Head of Content reviewing weekly balance in the canal.
    """
    clean_handle = handle.lstrip("@")
    deserted = [p for p in report.pillars if p.status == "deserted"]

    if deserted:
        target_pillar = deserted[0].pillar_name
        return (
            f"Oye {clean_handle}, estuve revisando cómo cerramos la semana en el canal.\n\n"
            f"Noté que tenemos desatendido nuestro pilar técnico de *{target_pillar}* (0% de presencia reciente).\n"
            f"Nuestra autoridad depende de que la gente vea el mecanismo y cómo piensas, no solo reflexiones.\n\n"
            f"¿Armamos hoy una demostración técnica del mecanismo para rebalancear la autoridad?"
        )

    return (
        f"Oye {clean_handle}, revisé el equilibrio de nuestros pilares de contenido en el canal y se ve sólido.\n"
        f"Nuestra tesis está consistente. ¿Te pasó algo interesante esta semana con un cliente o en tus proyectos para armar el próximo guion?"
    )


def brand_health_node(state: GraphState) -> GraphState:
    """Graph node for proactive personal brand audit."""
    gov = state.get("governor_decision")
    if gov and not gov.allowed:
        return state

    user_id = state.get("user_id", "default_user")
    creator_profile = state.get("creator_profile")
    handle = creator_profile.instagram_handle if creator_profile else f"creator_{user_id}"

    ctx = state.get("proactive_context") or {}
    recent_posts = ctx.get("recent_posts", [])
    declared_pillars = ctx.get("declared_pillars", [
        {"name": "Arquitectura de Sistemas", "target_pct": 50.0},
        {"name": "Casos Reales y Aprendizajes", "target_pct": 50.0},
    ])

    report = analyze_brand_health(user_id, recent_posts, declared_pillars)
    formatted = format_brand_health_whatsapp(report, handle)

    return update_state(
        state,
        brand_health_report=report,
        final_response=formatted,
    )
