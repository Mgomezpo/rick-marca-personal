"""Evaluator-Optimizer quality loop: anti-plagiarism, anti-slop, and empirical simulation."""
import re
from typing import List, Tuple, Dict, Any, Optional
from src.graph.state import (
    GraphState,
    ScriptDraft,
    EvaluationResult,
    WinningPattern,
    update_state,
)

FORBIDDEN_SLOP_PHRASES = [
    "en este mundo cambiante",
    "descubre el secreto",
    "desata tu potencial",
    "revoluciona tu vida",
    "sin precedentes",
    "hoy en día",
    "hoy en dia",
    "sumérgete",
    "sumergete",
    "en conclusión",
    "en conclusion",
    "como modelo de lenguaje",
    "por supuesto",
    "fórmula mágica",
    "formula magica",
]


def _clean_tokens(text: str) -> List[str]:
    """Extract lowercase alpha-numeric words from text."""
    return re.findall(r"\b\w+\b", text.lower())


def check_plagiarism(script_text: str, referents_texts: List[str]) -> Tuple[bool, int]:
    """
    Checks maximum consecutive matching words against reference texts.
    Returns (is_plagiarism, max_consecutive_words).
    Plagiarism is flagged if max_consecutive_words >= 5.
    """
    if not referents_texts:
        return False, 0

    script_words = _clean_tokens(script_text)
    if not script_words:
        return False, 0

    max_match = 0
    for ref in referents_texts:
        ref_words = _clean_tokens(ref)
        if not ref_words:
            continue

        # Find longest common contiguous subarray
        for i in range(len(script_words)):
            for j in range(len(ref_words)):
                k = 0
                while (
                    i + k < len(script_words)
                    and j + k < len(ref_words)
                    and script_words[i + k] == ref_words[j + k]
                ):
                    k += 1
                if k > max_match:
                    max_match = k

    is_plagiarism = max_match >= 5
    return is_plagiarism, max_match


def find_plagiarized_snippet(script_text: str, referents_texts: List[str]) -> Optional[str]:
    """Finds the longest contiguous matching phrase between script and references."""
    if not referents_texts:
        return None
    script_words = _clean_tokens(script_text)
    if not script_words:
        return None
    longest_snippet: List[str] = []
    for ref in referents_texts:
        ref_words = _clean_tokens(ref)
        for i in range(len(script_words)):
            for j in range(len(ref_words)):
                k = 0
                while (
                    i + k < len(script_words)
                    and j + k < len(ref_words)
                    and script_words[i + k] == ref_words[j + k]
                ):
                    k += 1
                if k > len(longest_snippet):
                    longest_snippet = script_words[i : i + k]
    if len(longest_snippet) >= 5:
        return " ".join(longest_snippet)
    return None


def calculate_simulation_probability(piezas_respaldo: int, avg_r: float) -> Dict[str, Any]:
    """
    Calculates estimated performance probability backed by empirical pieces and relative performance.
    """
    if piezas_respaldo >= 3 and avg_r >= 1.8:
        estimacion = "Alta"
        score = min(9.8, max(9.0, 8.0 + (piezas_respaldo * 0.2) + (avg_r * 0.4)))
    elif piezas_respaldo >= 2 and avg_r >= 1.4:
        estimacion = "Media"
        score = min(8.9, max(7.5, 6.5 + (piezas_respaldo * 0.3) + (avg_r * 0.5)))
    else:
        estimacion = "Baja"
        score = min(7.4, max(5.0, 4.0 + (piezas_respaldo * 0.5) + (avg_r * 0.5)))

    return {
        "estimacion": estimacion,
        "probabilidad_score": round(score, 1),
    }


def evaluate_script_quality(
    draft: ScriptDraft,
    referents_texts: List[str],
    pattern: Optional[WinningPattern] = None,
) -> EvaluationResult:
    """
    Multi-filter evaluator:
    1. Anti-plagiarism (< 5 consecutive words)
    2. Anti-slop checklist
    3. Empirical probability simulation
    """
    full_text = f"{draft.hook.texto} {draft.desarrollo.texto} {draft.cierre.texto}".lower()

    # 1. Anti-plagiarism check
    is_plag, max_words = check_plagiarism(full_text, referents_texts)

    # 2. Anti-slop checks
    slop_findings = []
    score = 10.0

    for phrase in FORBIDDEN_SLOP_PHRASES:
        if phrase in full_text:
            slop_findings.append(f"Frase cliché detectada: '{phrase}'")
            score -= 2.5

    # Check for greetings in hook
    hook_lower = draft.hook.texto.lower()
    if any(g in hook_lower for g in ["hola a todos", "bienvenidos", "hola amigos", "hey qué tal"]):
        slop_findings.append("Saludo inicial prohibido en el gancho.")
        score -= 1.5

    if is_plag:
        snippet = find_plagiarized_snippet(full_text, referents_texts)
        snippet_msg = f": frase '{snippet}' coincide con el referente" if snippet else f": {max_words} palabras consecutivas idénticas al referente."
        slop_findings.append(f"Plagio detectado ({max_words} palabras){snippet_msg}")
        score -= 5.0

    # Dual-coding tension contrast check
    if draft.visual_hook and draft.spoken_hook:
        clean_v = draft.visual_hook.lower().strip(" .,'\"")
        clean_s = draft.spoken_hook.lower().strip(" .,'\"")
        if clean_v == clean_s or clean_v == clean_s[:len(clean_v)]:
            slop_findings.append("Falta tensión Dual-Coding: el hook visual en pantalla repite textualmente el audio hablado.")
            score -= 1.0

    score = max(1.0, min(10.0, round(score, 1)))
    passed = (score >= 8.0 and not is_plag)

    # 3. Simulation
    piezas = pattern.piezas_respaldo if pattern else 1
    avg_r = pattern.rendimiento_relativo_promedio if pattern else 1.0
    sim = calculate_simulation_probability(piezas_respaldo=piezas, avg_r=avg_r)

    if passed:
        feedback = "Guion limpio, directo y auténtico. Tono de socio verificado."
    else:
        feedback = f"Corrección necesaria: {'; '.join(slop_findings)}"

    return EvaluationResult(
        score=score,
        passed=passed,
        feedback=feedback,
        plagio_detectado=is_plag,
        max_palabras_coincidentes=max_words,
        simulacion_estimacion=sim["estimacion"],
        piezas_respaldo=piezas,
    )


def evaluator_node(state: GraphState) -> GraphState:
    """
    Graph node that executes the quality loop audit on the current script draft.
    """
    draft = state.get("script_draft")
    if not draft:
        return state

    referents = [
        r.get("text", "") for r in state.get("referents_context", [])
        if isinstance(r, dict) and r.get("text")
    ]
    pattern = state["winning_patterns"][0] if state.get("winning_patterns") else None

    eval_result = evaluate_script_quality(
        draft=draft,
        referents_texts=referents,
        pattern=pattern,
    )

    return update_state(state, evaluation=eval_result)
