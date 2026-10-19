"""Graph edges and conditional routing for the RICK multi-tenant engine."""
from src.graph.state import GraphState


def quality_loop_router(state: GraphState) -> str:
    """
    Conditional edge router for the quality loop.
    - If evaluation passed: routes to 'format_output'.
    - If evaluation failed and iteration_count < 3: routes back to 'guionista' for correction.
    - If iteration_count >= 3: halts loop and routes to 'format_output'.
    """
    evaluation = state.get("evaluation")
    iteration = state.get("iteration_count", 0)

    if evaluation is None or evaluation.passed:
        return "format_output"

    if iteration < 3:
        return "guionista"

    # Stop looping after 3 attempts
    return "format_output"
