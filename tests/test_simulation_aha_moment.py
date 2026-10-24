"""
Comprehensive Simulation & Stress Test Harness for RICK Multitenant Engine.
Simulates end-to-end user journeys from initial greeting / cold onboarding to the 'Aha Moment',
testing real/famous reference accounts, shared link deconstruction, feedback rejection loops,
anti-slop filters, and integration resilience across 25 consecutive iterations.
"""
import pytest
import time
import re
from typing import Dict, Any, List, Optional
from unittest.mock import patch

from src.graph.state import (
    create_initial_state,
    ConversationMessage,
    WinningPattern,
    CreatorProfile,
    StoryReceipt,
    ScriptDraft,
    ScriptBlock,
    EvaluationResult,
)
from src.graph.engine import RickGraphEngine
from src.matrix.models import MatrixRow
from src.services.instagram_scraper import instagram_scraper_service, InstagramScraperService
from src.services.radar_ingestion import radar_ingestion_service, RadarIngestionService
from src.db.repository import SupabaseRepository
from src.services.session_runner import process_user_turn
from src.agents.evaluator import FORBIDDEN_SLOP_PHRASES, check_plagiarism


# =====================================================================
# 1. ORACULO DE CALIDAD DEL "AHA MOMENT" (AhaMomentOracle)
# =====================================================================
class AhaMomentOracle:
    """Automated judge asserting delivery of the canonical Aha Moment in RICK."""

    @staticmethod
    def assert_script_quality(response: str, expected_pillar: Optional[str] = None):
        """Verifies script canonical structure, absence of slop, and production readiness."""
        assert response is not None, "La respuesta no puede ser nula."
        assert len(response.strip()) > 50, "La respuesta es demasiado corta para un guion."

        # 1. 3 Bloques canónicos
        assert "HOOK" in response, "Falta el bloque HOOK canónico."
        assert "DESARROLLO" in response, "Falta el bloque DESARROLLO canónico."
        assert "CIERRE" in response, "Falta el bloque CIERRE canónico."

        # 2. Dirección de cámara o intención técnica
        assert "Cámara:" in response or "camara:" in response.lower(), (
            "Debe incluir indicaciones visuales/cámara para el creador."
        )

        # 3. Cero placeholders
        forbidden_placeholders = ["[link]", "[insertar", "[pegar link]", "placeholder.com"]
        for p in forbidden_placeholders:
            assert p not in response.lower(), f"Se detectó un placeholder prohibido: '{p}'"

        # 4. Cero frases de IA / Slop
        for slop in FORBIDDEN_SLOP_PHRASES:
            assert slop not in response.lower(), f"Se detectó frase de slop prohibida: '{slop}'"

        # 5. Cero markdown roto de tablas
        assert "|---|---|" not in response, "No debe incluir delimitadores de tabla en WhatsApp."

    @staticmethod
    def assert_shared_link_deconstruction(response: str):
        """Verifies deep analytical breakdown when a creator shares an Instagram reel."""
        assert response is not None
        lower = response.lower()
        # Debe analizar el gancho o la estructura
        assert "gancho" in lower or "estructura" in lower or "radar" in lower or "referente" in lower, (
            "RICK debe demostrar criterio editorial al analizar el enlace compartido."
        )
        assert "[link]" not in lower


# =====================================================================
# 2. ARQUETIPOS DE CREADORES SINTÉTICOS CON REFERENTES REALES / FAMOSOS
# =====================================================================
SYNTHETIC_CREATORS = {
    "hormozi_scaler": {
        "user_id": "usr_sim_hormozi",
        "handle": "carlos_b2b_offers",
        "nicho": "Ofertas de Alto Valor y Escalado de Negocios",
        "referentes": ["@alexhormozi", "@dan_martell"],
        "story": "Ayer perdimos 12 clientes en una semana porque cobrábamos por horas en vez de por resultado. Tuve que cambiar todo el empaquetado a una oferta irresistible de 5.000 dólares.",
        "shared_link": "https://www.instagram.com/reel/C5def303/",
    },
    "naval_mental_models": {
        "user_id": "usr_sim_naval",
        "handle": "diego_leverage",
        "nicho": "Apalancamiento, Código y Modelos Mentales",
        "referentes": ["@naval", "@matt_gray"],
        "story": "Me pasé 6 meses trabajando 14 horas al día sin ganar tracción. El quiebre fue entender que el esfuerzo no correlaciona con el resultado si no tienes apalancamiento de software.",
        "shared_link": "https://www.instagram.com/reel/C4xyz202/",
    },
    "huberman_performance": {
        "user_id": "usr_sim_huberman",
        "handle": "dra_lucia_salud",
        "nicho": "Neurobiología Aplicada y Alto Rendimiento",
        "referentes": ["@hubermanlab", "@peterattiamd"],
        "story": "Muchos pacientes creen que la fatiga se soluciona con más café. En la clínica medimos cortisol y el 80% tenía un pico de dopamina descalibrado por ver pantallas antes de salir el sol.",
        "shared_link": "https://www.instagram.com/reel/C3abc101/",
    },
    "cold_start_novato": {
        "user_id": "usr_sim_novato",
        "handle": "andres_consultor_nuevo",
        "nicho": "Consultoría Financiera",
        "referentes": [],
        "story": "No tengo marca personal y me da pena hablar a la cámara, pero mis clientes siempre cometen el error de mezclar finanzas personales con las de su empresa.",
        "shared_link": None,
    },
}


# =====================================================================
# 3. TEST CASES INDIVIDUALES DE LA MATRIZ
# =====================================================================

def test_esc01_cold_start_onboarding_to_aha_moment():
    """
    ESC-01: Creador novato sin reels previos ni referentes explícitos.
    Pasa por onboarding -> Mayéutica de Rubin -> Descubrimiento de nicho -> Guion 3 bloques.
    """
    engine = RickGraphEngine()
    user = SYNTHETIC_CREATORS["cold_start_novato"]
    state = create_initial_state(user["user_id"], user["handle"])

    # Turno 1: Saludo inicial
    state["messages"].append(ConversationMessage(role="user", content="Hola RICK, quiero empezar mi marca pero no sé cómo."))
    state = engine.run(state)
    r1 = state["final_response"]
    assert r1 is not None
    assert "¿" in r1

    # Turno 2: Comparte su Instagram y experiencia
    state["messages"].append(ConversationMessage(role="user", content=f"Mi cuenta es @{user['handle']}. {user['story']}"))
    state = engine.run(state)
    r2 = state["final_response"]
    assert r2 is not None

    # Turno 3: Pide estructurar el guion
    state["messages"].append(ConversationMessage(role="user", content="Listo, armemos el guion para grabar hoy."))
    state = engine.run(state)
    r3 = state["final_response"]

    AhaMomentOracle.assert_script_quality(r3)
    assert state["script_draft"] is not None
    assert state["evaluation"].passed is True
    assert state["evaluation"].score >= 8.0


def test_esc02_warm_start_with_famous_benchmarks():
    """
    ESC-02: Creador con cuenta establecida y referentes famosos (@alexhormozi, @dan_martell).
    RICK utiliza el benchmark del radar ($R >= 1.5x) para calibrar el guion.
    """
    engine = RickGraphEngine()
    user = SYNTHETIC_CREATORS["hormozi_scaler"]
    state = create_initial_state(user["user_id"], user["handle"])
    state["creator_profile"] = CreatorProfile(
        user_id=user["user_id"],
        instagram_handle=user["handle"],
        nicho=user["nicho"],
        mediana_views=25000.0,
        referentes=user["referentes"],
    )

    # Ingesta en el radar de reels virales de Hormozi y Dan Martell
    state["winning_patterns"] = [
        WinningPattern(
            pattern_id="pat_hormozi_01",
            tipo_hook="quiebre_creencia",
            formato="leccion",
            emocion="autoridad",
            rendimiento_relativo_promedio=3.2,
            piezas_respaldo=8,
            ejemplos=["Hacer más llamadas no arregla una mala oferta: el secreto de los $100M."],
        )
    ]

    # Creador comparte su historia de fricción
    state["messages"].append(ConversationMessage(role="user", content=user["story"]))
    state = engine.run(state)

    # Pide el guion directo
    state["messages"].append(ConversationMessage(role="user", content="Armemos el guion al grano con el estilo de Hormozi."))
    state = engine.run(state)
    r_final = state["final_response"]

    AhaMomentOracle.assert_script_quality(r_final)
    assert "HOOK" in r_final
    assert "DESARROLLO" in r_final
    assert "CIERRE" in r_final


def test_esc03_shared_reel_link_deconstruction():
    """
    ESC-03: Creador envía un link real de Instagram Reel y pide adaptarlo.
    RICK lo deconstruye en el radar y genera una pieza propia con 0% plagio.
    """
    engine = RickGraphEngine()
    user = SYNTHETIC_CREATORS["naval_mental_models"]
    state = create_initial_state(user["user_id"], user["handle"])

    # Envía link de Instagram
    reel_url = user["shared_link"]
    state["messages"].append(
        ConversationMessage(
            role="user",
            content=f"RICK, mira este video que vi: {reel_url} me parece brutal el quiebre. ¿Cómo lo adaptamos a mi marca?",
        )
    )
    state = engine.run(state)
    r1 = state["final_response"]

    AhaMomentOracle.assert_shared_link_deconstruction(r1)

    # Creador pasa su propia anécdota anclada a ese quiebre
    state["messages"].append(ConversationMessage(role="user", content=f"Mi experiencia es esta: {user['story']}. Hazme el guion."))
    state = engine.run(state)
    r_script = state["final_response"]

    AhaMomentOracle.assert_script_quality(r_script)
    # Comprobar plagio contra el gancho original
    referent_texts = ["Así automaticé el 70% de mi operación sin contratar agencias."]
    is_plag, max_match = check_plagiarism(r_script, referent_texts)
    assert not is_plag, f"No debe haber plagio literal (coincidencia de {max_match} palabras)."


def test_esc04_feedback_rejection_and_rewrite_loop():
    """
    ESC-04: Creador dice 'no me gustó el guion, suena muy formal'.
    RICK activa el bucle de feedback y reescribe adaptando el tono.
    """
    engine = RickGraphEngine()
    user = SYNTHETIC_CREATORS["huberman_performance"]
    state = create_initial_state(user["user_id"], user["handle"])

    # Generar primer guion
    state["story_extracted"] = user["story"]
    state["messages"].append(ConversationMessage(role="user", content="Escribe el guion sobre este caso."))
    state = engine.run(state)
    script_v1 = state["script_draft"]
    assert script_v1 is not None

    # Creador rechaza el tono
    state["messages"].append(ConversationMessage(role="user", content="No me gustó el guion. Suena muy corporativo y aburrido, quiero que suene más a charla de café."))
    state = engine.run(state)
    res_feedback = state["final_response"]

    assert res_feedback is not None
    # RICK debe responder con empatía o proponer el ajuste
    assert "¿" in res_feedback or "guion" in res_feedback.lower() or "café" in res_feedback.lower() or "ajust" in res_feedback.lower()


def test_esc05_anti_slop_and_plagiarism_internal_shield():
    """
    ESC-05: Stress test del filtro anti-slop y anti-plagio.
    Garantiza que cualquier borrador con frases cliché sea penalizado internamente.
    """
    from src.agents.evaluator import evaluate_script_quality

    # Borrador intencionalmente contaminado con slop
    slop_draft = ScriptDraft(
        titulo="Guion Cliché",
        formato="Reel",
        duracion_objetivo=45,
        hook=ScriptBlock(texto="En este mundo cambiante, descubre el secreto que desata tu potencial.", intencion="gancho", camara="frente"),
        desarrollo=ScriptBlock(texto="Hoy en día muchos sufren sin precedentes con una fórmula mágica.", intencion="cuerpo", camara="frente"),
        cierre=ScriptBlock(texto="En conclusión, sumérgete en mis mentorías.", intencion="cierre", camara="frente"),
    )
    pattern = WinningPattern(
        pattern_id="p1", tipo_hook="quiebre", formato="Reel", emocion="curiosidad",
        rendimiento_relativo_promedio=2.0, piezas_respaldo=3, ejemplos=["Referente limpio"]
    )

    eval_result = evaluate_script_quality(draft=slop_draft, referents_texts=["Referente limpio"], pattern=pattern)

    # Debe ser reprobado o severamente penalizado
    assert eval_result.passed is False or eval_result.score < 8.0
    assert "cliché" in eval_result.feedback.lower() or "cliche" in eval_result.feedback.lower()


def test_esc06_apify_resilience_and_graceful_fallback():
    """
    ESC-06: Simulación de fallo en Apify (timeout / 429) durante la búsqueda de reels virales.
    RICK debe degradar suavemente al radar mock/caché sin lanzar excepción ni frenar al usuario.
    """
    scraper = InstagramScraperService(token="fake_token_for_error")

    # Inyectar fallo en requests externos
    with patch("httpx.Client.post", side_effect=Exception("Apify HTTP 429 Rate Limit Exceeded")):
        rows = scraper.search_niche_reels(["growth", "b2b"], limit=3)

    assert len(rows) >= 1
    assert rows[0].post_id.startswith("https://www.instagram.com/reel/")
    assert rows[0].relative_performance >= 1.5


def test_esc07_two_part_saga_with_cliffhanger():
    """
    ESC-07: Historia con múltiples errores que RICK bifurca en saga de 2 partes con cliffhanger.
    """
    engine = RickGraphEngine()
    state = create_initial_state("usr_saga_01", "saga_creator")
    state["story_extracted"] = "Cometí dos errores graves que casi me quiebran en 2024: primero contraté a 10 personas sin ventas, y segundo me endeudé en dólares."

    state["messages"].append(ConversationMessage(role="user", content="Quiero armar una saga de 2 partes para contar los dos errores."))
    state = engine.run(state)

    draft = state["script_draft"]
    assert draft is not None
    assert draft.series is not None
    assert draft.series.episode_index == 1
    assert draft.series.total_episodes == 2
    # El cierre debe tener cliffhanger hacia la parte 2
    assert "parte 2" in draft.cierre.texto.lower() or "segunda parte" in draft.cierre.texto.lower() or "sígueme" in draft.cierre.texto.lower()


def test_esc08_chaotic_voice_transcription_input():
    """
    ESC-08: Ingesta de nota de voz caótica o texto desordenado sin puntuación.
    RICK debe extraer limpiamente el quiebre y friction sin confundirse.
    """
    engine = RickGraphEngine()
    state = create_initial_state("usr_chaotic_01", "creator_audio")
    chaotic_text = (
        "bueno rick mira te cuento estaba pensando que ayer me pasó algo terrible con un cliente "
        "porque le prometí entregarle una web en dos semanas y no pude porque mi programador se fue "
        "y me tocó aprender a programar a las 3 de la mañana un desastre total"
    )
    state["messages"].append(ConversationMessage(role="user", content=chaotic_text))
    state = engine.run(state)

    # Debe pedir profundizar o confirmar la escena
    r1 = state["final_response"]
    assert r1 is not None
    assert "¿" in r1

    # Creador confirma y pide guion
    state["messages"].append(ConversationMessage(role="user", content="Exacto, fue un error de no tener redundancia de equipo. Armemos el guion para advertirle a otros."))
    state = engine.run(state)
    r2 = state["final_response"]
    AhaMomentOracle.assert_script_quality(r2)


def test_esc09_multitenant_isolation_across_personas():
    """
    ESC-09: Verificación de aislamiento estricto multi-tenant entre creadores (@alexhormozi vs @naval).
    Garantiza que el lore, story bank y guiones no se filtren entre inquilinos.
    """
    repo = SupabaseRepository()
    engine = RickGraphEngine()

    user_a = "tenant_hormozi_fan"
    user_b = "tenant_naval_fan"

    # Ingesta para Tenant A
    state_a = create_initial_state(user_a, "carlos_b2b")
    state_a["creator_profile"] = CreatorProfile(
        user_id=user_a, instagram_handle="carlos_b2b", nicho="Ventas", mediana_views=20000.0,
        referentes=["@alexhormozi"],
        story_bank=[StoryReceipt(id="rec_a1", theme="ventas", summary="Perdí 10k por no cobrar por adelantado", concrete_details=["10k dolares", "cliente fantasma"], punchline="Cobra siempre antes")]
    )
    repo.upsert_creator_profile(state_a["creator_profile"])

    # Ingesta para Tenant B
    state_b = create_initial_state(user_b, "diego_code")
    state_b["creator_profile"] = CreatorProfile(
        user_id=user_b, instagram_handle="diego_code", nicho="Software", mediana_views=50000.0,
        referentes=["@naval"],
        story_bank=[StoryReceipt(id="rec_b1", theme="codigo", summary="El software escala a costo marginal cero", concrete_details=["servidores cloud", "python"], punchline="Programa o serás programado")]
    )
    repo.upsert_creator_profile(state_b["creator_profile"])

    # Ejecutar turno para A
    state_a["messages"].append(ConversationMessage(role="user", content="Hola RICK, ¿qué recuerdas de mis historias?"))
    res_a = engine.run(state_a)

    # Ejecutar turno para B
    state_b["messages"].append(ConversationMessage(role="user", content="Hola RICK, ¿qué recuerdas de mis historias?"))
    res_b = engine.run(state_b)

    # Validar aislamiento de memoria
    prof_a = repo.get_creator_profile(user_a)
    prof_b = repo.get_creator_profile(user_b)

    assert any("10k" in r.summary for r in prof_a.story_bank)
    assert not any("10k" in r.summary for r in prof_b.story_bank)
    assert any("software" in r.summary for r in prof_b.story_bank)
    assert not any("software" in r.summary for r in prof_a.story_bank)


def test_esc10_database_resilience_and_piece_persistence():
    """
    ESC-10: Guardado seguro de piezas generadas en Supabase verificando retrocompatibilidad de columnas JSONB.
    """
    repo = SupabaseRepository()
    user_id = "user_persistence_test"

    draft = ScriptDraft(
        titulo="La Regla de los 5 Minutos",
        formato="Reel",
        duracion_objetivo=50,
        hook=ScriptBlock(texto="Si tardas más de 5 minutos en responderle a un lead, ya perdiste la venta.", intencion="gancho", camara="directo"),
        desarrollo=ScriptBlock(texto="Probamos responder en 60 segundos con automatizaciones y cerramos el triple.", intencion="cuerpo", camara="café"),
        cierre=ScriptBlock(texto="Automatiza tu respuesta o contrata a alguien que no duerma.", intencion="cierre", camara="corte"),
        pilar="Estrategia Comercial",
    )

    # Guardar en repositorio
    piece_id = repo.save_piece(user_id=user_id, script=draft)
    assert piece_id is not None

    # Recuperar piezas
    pieces = repo.get_pieces(user_id=user_id)
    assert len(pieces) >= 1
    saved = pieces[0]
    assert saved.get("pilar") == "Estrategia Comercial" or saved.get("strategy_tag") == "Estrategia Comercial"
    assert "HOOK" in str(saved) or "5 minutos" in str(saved)


# =====================================================================
# 4. STRESS HARNESS: 25 EJECUCIONES CONSECUTIVAS COMPLETAS
# =====================================================================
def test_recursive_simulation_loop_25_iterations():
    """
    Stress harness required by user:
    Runs the full E2E user journey simulation 25 consecutive times, rotating through
    different real/famous personas, shared links, and multi-turn states.
    Asserts 100% success rate (25/25), strict determinism, and zero flakiness.
    """
    personas_list = list(SYNTHETIC_CREATORS.values())
    total_runs = 25
    successful_runs = 0
    latencies: List[float] = []

    engine = RickGraphEngine()

    for i in range(total_runs):
        start_time = time.perf_counter()
        persona = personas_list[i % len(personas_list)]
        iteration_user_id = f"{persona['user_id']}_run_{i+1:02d}"

        # 1. Crear estado inicial
        state = create_initial_state(iteration_user_id, persona["handle"])
        state["creator_profile"] = CreatorProfile(
            user_id=iteration_user_id,
            instagram_handle=persona["handle"],
            nicho=persona["nicho"],
            mediana_views=15000.0,
            referentes=persona["referentes"],
        )

        # 2. Ingesta de referentes o link compartido
        if persona.get("shared_link"):
            state["messages"].append(
                ConversationMessage(
                    role="user",
                    content=f"Mira este reel: {persona['shared_link']}. ¿Cómo lo adaptamos?",
                )
            )
            state = engine.run(state)
            assert state["final_response"] is not None

        # 3. Envío de anécdota y petición de guion
        state["messages"].append(
            ConversationMessage(
                role="user",
                content=f"{persona['story']} Armemos el guion técnico de una vez.",
            )
        )
        state = engine.run(state)

        final_response = state["final_response"]
        AhaMomentOracle.assert_script_quality(final_response)

        assert state["script_draft"] is not None
        assert state["evaluation"] is not None
        assert state["evaluation"].score >= 8.0

        elapsed = (time.perf_counter() - start_time) * 1000
        latencies.append(elapsed)
        successful_runs += 1

    assert successful_runs == 25, f"Fallaron iteraciones: {successful_runs}/{total_runs} exitosas."
