"""Tests for Decoupled Radar Ingestion Service and Sub-50ms Matrix Cache."""
import time
import pytest
from src.matrix.models import MatrixRow
from src.services.radar_ingestion import RadarIngestionService


def _dummy_row(post_id: str, handle: str, r: float) -> MatrixRow:
    return MatrixRow(
        post_id=post_id,
        account_handle=handle,
        views=int(r * 10000),
        account_median=10000.0,
        relative_performance=r,
        hook_text=f"Gancho ganador de {handle}",
        hook_type="revelacion_contraria",
        format="Reel",
        emotion="curiosidad",
        duration_seconds=30,
    )


def test_radar_ingestion_caches_and_retrieves_under_50ms():
    service = RadarIngestionService()
    user_id = "user_fast_01"

    # Ingest 10 rows
    rows = [_dummy_row(f"p_{i}", f"@creator_{i}", 2.0 + (i * 0.1)) for i in range(10)]
    service.ingest_creator_posts(user_id=user_id, creator_handle="@creator_0", posts=rows)

    # Measure retrieval latency
    start = time.perf_counter()
    cached = service.get_cached_matrix(user_id=user_id)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert len(cached) == 10
    assert elapsed_ms < 50.0  # Must be strictly under 50ms (zero live scraping)


def test_radar_ingestion_batch_pool_wide_and_fresh():
    service = RadarIngestionService()
    user_id = "user_pool_01"

    # Pool of 20 creators with 5 posts each (100 posts total)
    pool_data = {}
    for c in range(20):
        handle = f"@creator_{c:02d}"
        pool_data[handle] = [
            _dummy_row(f"p_{c}_{p}", handle, 1.6 + (p * 0.2))
            for p in range(5)
        ]

    summary = service.batch_ingest_pool(user_id=user_id, creator_posts_map=pool_data, max_per_creator=3)
    assert summary["creators_count"] == 20
    assert summary["total_ingested"] == 60  # 20 creators * 3 capped posts

    cached = service.get_cached_matrix(user_id=user_id)
    assert len(cached) == 60


def test_radar_ingestion_anti_overlap_and_cooldown_tracking():
    service = RadarIngestionService()
    user_id = "user_overlap_01"

    # Ingest 3 creators with posts
    c1_posts = [_dummy_row("p1_top", "@c1", 3.0), _dummy_row("p1_second", "@c1", 2.2)]
    c2_posts = [_dummy_row("p2_top", "@c2", 2.8)]
    service.ingest_creator_posts(user_id, "@c1", c1_posts)
    service.ingest_creator_posts(user_id, "@c2", c2_posts)

    # Mark p1_top as used yesterday
    service.record_used_post(user_id, "p1_top")
    # Mark @c1 as recently used (7-day cooldown)
    service.record_used_creator(user_id, "@c1")

    assert "p1_top" in service.get_used_post_ids(user_id)
    assert "@c1" in service.get_recently_used_creators(user_id)

    # Fetch fresh patterns
    fresh = service.fetch_fresh_radar_patterns(user_id=user_id)
    assert fresh["is_fallback"] is False
    assert len(fresh["top_patterns"]) > 0

    # Ensure p1_top was excluded from considered posts
    considered_ids = fresh["considered_post_ids"]
    assert "p1_top" not in considered_ids
    assert "p2_top" in considered_ids


def test_api_proactive_tick_e2e_with_wide_radar_cache():
    from fastapi.testclient import TestClient
    from src.api.app import app, repo
    from src.services.radar_ingestion import radar_ingestion_service

    client = TestClient(app)
    user_id = "user_e2e_radar"

    # Pre-populate radar cache with 15 creators (simulating background cron worker)
    for i in range(15):
        handle = f"@expert_{i}"
        posts = [
            _dummy_row(f"p_{i}_1", handle, 2.5),
            _dummy_row(f"p_{i}_2", handle, 2.0),
        ]
        radar_ingestion_service.ingest_creator_posts(user_id, handle, posts)

    payload = {
        "user_id": user_id,
        "trigger_type": "market_spark",
        "phone_number": "+573009998877",
        "proactive_context": {
            "hours_since_last_ping": 30.0,
            "current_local_hour": 14,
            "silence_streak": 0,
            "confidence": 0.93,
            "source_referent": "@expert_0",
            "thesis": "Sistemas determinísticos con LangGraph",
        },
    }

    start = time.perf_counter()
    response = client.post("/api/proactive/tick", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    data = response.json()
    assert data["dispatched"] is True
    assert data["governor_allowed"] is True
    assert data["message"] is not None
    assert "radar del equipo" in data["message"].lower()
    assert elapsed_ms < 150.0  # Fast execution, zero live scraping

    # Verify conversation retention
    history = repo.get_conversation(user_id)
    assert len(history) >= 1
    assert "radar del equipo" in history[-1].content.lower()

