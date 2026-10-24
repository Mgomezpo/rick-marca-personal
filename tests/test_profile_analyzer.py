"""Unit tests for the centralized ProfileAnalyzerService."""
import pytest
from src.services.profile_analyzer import ProfileAnalyzerService, CreatorFootprintReport
from src.db.repository import SupabaseRepository


def test_clean_handle_variations():
    """Validates handle sanitization across various formats."""
    service = ProfileAnalyzerService()

    assert service.clean_handle("@miguel_gomezpo") == "miguel_gomezpo"
    assert service.clean_handle("miguel_gomezpo") == "miguel_gomezpo"
    assert service.clean_handle("https://www.instagram.com/miguel_gomezpo/") == "miguel_gomezpo"
    assert service.clean_handle("http://instagram.com/miguel.gomezpo") == "miguel.gomezpo"
    assert service.clean_handle("") == ""


def test_analyze_creator_footprint_returns_structured_report():
    """Validates that footprint analysis returns complete typed report."""
    repo = SupabaseRepository()
    service = ProfileAnalyzerService(repo=repo)

    report = service.analyze_creator_footprint(
        handle="@miguel_gomezpo",
        user_id="user_test_profile_1",
    )

    assert isinstance(report, CreatorFootprintReport)
    assert report.handle == "miguel_gomezpo"
    assert len(report.nicho) > 0
    assert report.median_views > 0
    assert len(report.diagnostico_critico) > 0
    assert "retención" in report.diagnostico_critico.lower() or "feed" in report.diagnostico_critico.lower()

    # Profile should be automatically updated in repository
    profile = repo.get_creator_profile("user_test_profile_1")
    assert profile is not None
    assert profile.instagram_handle == "miguel_gomezpo"
    assert profile.nicho == report.nicho
    assert profile.mediana_views == report.median_views


def test_profile_analyzer_reusable_by_subagents():
    """Verifies that specialist subagents can invoke the service with a single line."""
    service = ProfileAnalyzerService()
    report = service.analyze_creator_footprint("carlos_growth", user_id="user_carlos")

    assert report.handle == "carlos_growth"
    assert report.median_views > 0
    assert len(report.proyectos) >= 1
