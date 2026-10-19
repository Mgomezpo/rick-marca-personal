"""Tests for personal account routine reporter and procedural learnings (Task 8)."""
import pytest
from src.graph.state import (
    create_initial_state,
    LearningItem,
)
from src.matrix.models import MatrixRow
from src.agents.routine import (
    audit_personal_account,
    format_weekly_report,
    routine_reporter_node,
    AccountAuditResult,
)


def test_audit_personal_account_extracts_learnings_and_winners():
    user_id = "user_miguel"
    posts = [
        MatrixRow(
            post_id="p1",
            account_handle="miguel_gomezpo",
            views=32000,
            account_median=12000.0,
            relative_performance=2.67,
            hook_text="Casi quiebro mi negocio por contratar una agencia",
            hook_type="confesion_error",
            format="historia_personal",
            emotion="vulnerabilidad",
            duration_seconds=44,
        ),
        MatrixRow(
            post_id="p2",
            account_handle="miguel_gomezpo",
            views=25000,
            account_median=12000.0,
            relative_performance=2.08,
            hook_text="Perdí tres meses en anuncios antes de entender la verdad",
            hook_type="confesion_error",
            format="historia_personal",
            emotion="vulnerabilidad",
            duration_seconds=50,
        ),
        MatrixRow(
            post_id="p3",
            account_handle="miguel_gomezpo",
            views=6000,
            account_median=12000.0,
            relative_performance=0.5,
            hook_text="Tutorial de cómo configurar Make para tu CRM",
            hook_type="tutorial",
            format="pantalla",
            emotion="neutral",
            duration_seconds=30,
        ),
    ]

    audit = audit_personal_account(user_id=user_id, posts=posts, personal_median=12000.0)

    assert isinstance(audit, AccountAuditResult)
    assert len(audit.winner_posts) == 2
    assert len(audit.low_posts) == 1
    assert len(audit.learnings) >= 1

    top_learning = audit.learnings[0]
    assert isinstance(top_learning, LearningItem)
    assert top_learning.user_id == user_id
    assert "confesion" in top_learning.statement.lower() or "error" in top_learning.statement.lower()
    assert top_learning.confidence >= 0.85
    assert top_learning.applies_when == "Planificación de guiones semanales"


def test_format_weekly_report_clean_whatsapp_style():
    audit = AccountAuditResult(
        account_handle="miguel_gomezpo",
        personal_median=12000.0,
        total_posts_audited=3,
        winner_posts=[
            MatrixRow(
                post_id="p1",
                account_handle="miguel_gomezpo",
                views=32000,
                account_median=12000.0,
                relative_performance=2.67,
                hook_text="Casi quiebro mi negocio por contratar una agencia",
                hook_type="confesion_error",
                format="historia_personal",
                emotion="vulnerabilidad",
                duration_seconds=44,
            )
        ],
        low_posts=[],
        learnings=[
            LearningItem(
                user_id="u1",
                statement="Las confesiones de errores en tu negocio te dan 2.6x más retención que los tutoriales técnicos.",
                applies_when="Planificación de guiones semanales",
                confidence=0.92,
            )
        ],
    )

    report = format_weekly_report(audit, handle="miguel_gomezpo")

    assert report is not None
    assert "12,000" in report or "12000" in report
    assert "2.6x" in report or "2.67x" in report
    # Spoken WhatsApp tone: no robotic tables
    assert "|---|---|" not in report
    assert "Estimado usuario" not in report
    assert "miguel_gomezpo" in report


def test_routine_reporter_node_state_update():
    state = create_initial_state("user_miguel", "miguel_gomezpo")
    state["referents_context"] = [
        {
            "post_id": "p1",
            "account_handle": "miguel_gomezpo",
            "views": 35000,
            "hook_text": "Mi mayor error de 2025",
            "hook_type": "confesion_error",
            "format": "historia_personal",
            "emotion": "vulnerabilidad",
            "duration_seconds": 40,
        }
    ]

    new_state = routine_reporter_node(state)

    assert new_state["final_response"] is not None
    assert len(new_state["learnings"]) >= 1
    assert "12" in new_state["final_response"] or "views" in new_state["final_response"].lower() or "reporte" in new_state["final_response"].lower()
