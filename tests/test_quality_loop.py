"""Tests for Quality Loop: Anti-plagiarism, Anti-slop, Simulation, and Conditional Edges (Task 7)."""
import pytest
from src.graph.state import (
    create_initial_state,
    ScriptDraft,
    ScriptBlock,
    WinningPattern,
    EvaluationResult,
)
from src.agents.evaluator import (
    check_plagiarism,
    evaluate_script_quality,
    calculate_simulation_probability,
    evaluator_node,
)
from src.graph.edges import quality_loop_router


def test_anti_plagiarism_detects_5_consecutive_words():
    reference = "le pagué dos mil dólares a una agencia para que me salvara el negocio"

    # Exact match of 6 words -> Plagiarism
    plagiarized_text = "ayer le pagué dos mil dólares a una agencia y fue un desastre."
    is_plagiarism, count = check_plagiarism(plagiarized_text, [reference])
    assert is_plagiarism is True
    assert count >= 5

    # Match of 3 words -> Not plagiarism
    original_text = "le pagué dos dólares a otro mentor en vez de delegar."
    is_plag, count_clean = check_plagiarism(original_text, [reference])
    assert is_plag is False
    assert count_clean <= 4


def test_anti_slop_penalizes_cliches():
    draft_slop = ScriptDraft(
        titulo="Test Slop",
        formato="Reel",
        duracion_objetivo=45,
        hook=ScriptBlock(
            texto="En este mundo cambiante, descubre el secreto que desatará tu potencial.",
            intencion="Enganche falso",
            camara="Plano general",
        ),
        desarrollo=ScriptBlock(
            texto="Hoy en día todos buscan la fórmula mágica sin precedentes.",
            intencion="Explicar",
            camara="Plano medio",
        ),
        cierre=ScriptBlock(
            texto="Comenta FUEGO y revoluciona tu vida.",
            intencion="CTA forzado",
            camara="Corte",
        ),
    )

    eval_result = evaluate_script_quality(draft_slop, referents_texts=[])
    assert eval_result.score < 8.0
    assert eval_result.passed is False
    assert "cliché" in eval_result.feedback.lower() or "slop" in eval_result.feedback.lower()


def test_clean_script_passes_with_high_score():
    clean_draft = ScriptDraft(
        titulo="Error de Agencia",
        formato="Reel",
        duracion_objetivo=42,
        hook=ScriptBlock(
            texto='"Le pagué dos mil dólares a una agencia y casi me funden."',
            intencion="Desarmar objeción y capturar dolor inmediato",
            camara="Primer plano directo al lente sin rodeos",
        ),
        desarrollo=ScriptBlock(
            texto="El error no fue de ellos. Fue mío, por querer comprar clientes con dinero en vez de entenderlos con tiempo.",
            intencion="Construir autoridad y vulnerabilidad de socio a socio",
            camara="Plano medio relajado, mirada fija, tono de café",
        ),
        cierre=ScriptBlock(
            texto="Antes de pagar para escalar, asegúrate de que tienes algo que funciona cuando estás tú solo.",
            intencion="Fijar regla de oro",
            camara="Pausa de 1 segundo antes del corte",
        ),
    )

    pattern = WinningPattern(
        pattern_id="pat_1",
        tipo_hook="confesion_error",
        formato="historia_personal",
        emocion="vulnerabilidad",
        rendimiento_relativo_promedio=2.5,
        piezas_respaldo=5,
    )

    eval_result = evaluate_script_quality(clean_draft, referents_texts=[], pattern=pattern)
    assert eval_result.passed is True
    assert eval_result.score >= 8.5
    assert eval_result.simulacion_estimacion == "Alta"
    assert eval_result.piezas_respaldo == 5


def test_simulation_probability_calculation():
    # 5 pieces with 2.5x -> Alta
    high_sim = calculate_simulation_probability(piezas_respaldo=5, avg_r=2.5)
    assert high_sim["estimacion"] == "Alta"
    assert high_sim["probabilidad_score"] >= 9.0

    # 1 piece with 1.1x -> Baja
    low_sim = calculate_simulation_probability(piezas_respaldo=1, avg_r=1.1)
    assert low_sim["estimacion"] == "Baja"
    assert low_sim["probabilidad_score"] < 7.5


def test_quality_loop_router_conditional_edge():
    state = create_initial_state("u1", "miguel_gomezpo")

    # Case 1: Evaluation passed -> route to format_output
    state["evaluation"] = EvaluationResult(
        score=9.0, passed=True, feedback="Excelente", plagio_detectado=False
    )
    state["iteration_count"] = 1
    assert quality_loop_router(state) == "format_output"

    # Case 2: Evaluation failed, iteration < 3 -> retry guionista
    state["evaluation"] = EvaluationResult(
        score=6.0, passed=False, feedback="Mucho slop", plagio_detectado=False
    )
    state["iteration_count"] = 1
    assert quality_loop_router(state) == "guionista"

    # Case 3: Evaluation failed, max iterations reached (3) -> stop loop and proceed to format_output
    state["iteration_count"] = 3
    assert quality_loop_router(state) == "format_output"
