"""Compilador y motor de ejecución del State Graph de RICK Multitenant."""
from typing import Optional
from src.graph.state import GraphState, update_state
from src.agents.rick import rick_strategist_node
from src.agents.guionista import guionista_node
from src.agents.evaluator import evaluator_node
from src.agents.routine import routine_reporter_node
from src.graph.edges import quality_loop_router
from src.graph.formatter import format_script_whatsapp


class RickGraphEngine:
    """
    Compiles and executes the RICK multi-tenant state graph:
    1. Rick Strategist & Intent Router (Rubin mayeutics)
    2. Routine Reporter (Account audit & procedural learnings)
    3. Guionista + Quality Loop (Anti-plagiarism, Anti-slop, Simulation)
    4. WhatsApp Formatter (Clean conversational output)
    """

    def run(self, initial_state: GraphState) -> GraphState:
        """
        Execute the graph end-to-end starting from initial_state.
        """
        state = initial_state

        # Step 1: Execute RICK Strategist & Router
        state = rick_strategist_node(state)
        intent = state.get("current_intent", "chat")

        # Branch 1: Chat or Story Extraction (Trench inquiry)
        if intent in ("chat", "extract_story"):
            return state

        # Branch 2: Account Audit & Weekly Routine Report
        if intent == "view_report":
            state = routine_reporter_node(state)
            return state

        # Branch 3: Technical Script Generation with Closed Quality Loop
        if intent in ("generate_script", "evaluate_script"):
            max_iterations = 3
            while True:
                # Node Guionista
                state = guionista_node(state)

                # Node Evaluator
                state = evaluator_node(state)

                # Conditional Edge Quality Loop Router
                next_step = quality_loop_router(state)
                if next_step == "format_output" or state.get("iteration_count", 0) >= max_iterations:
                    break

            # Format final response for WhatsApp
            draft = state.get("script_draft")
            evaluation = state.get("evaluation")
            if draft:
                final_text = format_script_whatsapp(draft, evaluation)
                state = update_state(state, final_response=final_text)

        return state
