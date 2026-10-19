"""Tests for Wide & Fresh Radar and Anti-Overlap Deduplication (Inverting the Equation)."""
import pytest
from src.matrix.models import MatrixRow
from src.matrix.analyzer import (
    sample_wide_radar,
    rotate_creator_patterns,
    MarketRadar,
)


def _make_dummy_row(post_id: str, handle: str, r: float, hook: str = "Hook de prueba") -> MatrixRow:
    return MatrixRow(
        post_id=post_id,
        account_handle=handle,
        views=int(r * 10000),
        account_median=10000.0,
        relative_performance=r,
        hook_text=hook,
        hook_type="revelacion_contraria",
        format="Reel",
        emotion="curiosidad",
        duration_seconds=45,
    )


def test_sample_wide_radar_caps_posts_per_creator():
    # 2 creators with 10 posts each (old deep vertical)
    rows = []
    for i in range(10):
        rows.append(_make_dummy_row(f"p_casi_{i}", "@casidonovan", 2.0 + (i * 0.1)))
        rows.append(_make_dummy_row(f"p_other_{i}", "@other_creator", 1.8 + (i * 0.1)))

    assert len(rows) == 20

    # Wide sampling capping to top 3 per creator
    wide_sample = sample_wide_radar(rows, max_posts_per_creator=3)
    assert len(wide_sample) == 6  # 3 from casidonovan + 3 from other_creator

    # Check that it kept the highest performing ones
    casi_posts = [r for r in wide_sample if r.account_handle == "@casidonovan"]
    assert len(casi_posts) == 3
    # The highest R should be included
    assert max(r.relative_performance for r in casi_posts) >= 2.9


def test_sample_wide_radar_excludes_used_post_ids():
    rows = [
        _make_dummy_row("post_101", "@casidonovan", 2.5),
        _make_dummy_row("post_102", "@casidonovan", 2.1),
        _make_dummy_row("post_201", "@creator_b", 2.4),
        _make_dummy_row("post_301", "@creator_c", 2.8),
    ]

    # Exclude post_101 (already used in yesterday's script)
    filtered = sample_wide_radar(
        rows,
        max_posts_per_creator=3,
        excluded_post_ids=["post_101"],
    )

    post_ids = [r.post_id for r in filtered]
    assert "post_101" not in post_ids
    assert "post_102" in post_ids
    assert "post_201" in post_ids
    assert "post_301" in post_ids


def test_rotate_creator_patterns_forces_rotation():
    rows = [
        _make_dummy_row("p1", "@casidonovan", 3.0),
        _make_dummy_row("p2", "@creator_b", 2.2),
        _make_dummy_row("p3", "@creator_c", 2.0),
    ]

    # If @casidonovan was used in the last script, rotation puts other creators first
    rotated = rotate_creator_patterns(
        rows,
        recently_used_handles=["@casidonovan"],
    )

    # First creator in list should NOT be @casidonovan
    assert rotated[0].account_handle != "@casidonovan"
    assert rotated[-1].account_handle == "@casidonovan"


def test_market_radar_wide_integration():
    radar = MarketRadar()
    referents = [
        _make_dummy_row("p_ref_1", "@ref1", 2.2),
        _make_dummy_row("p_ref_2", "@ref1", 1.9),
        _make_dummy_row("p_ref_3", "@ref1", 1.7),
        _make_dummy_row("p_ref_4", "@ref1", 1.6),  # 4th post should be trimmed if max=3
    ]
    discovery = [
        _make_dummy_row("p_disc_1", "@disc1", 2.5),
        _make_dummy_row("p_disc_2", "@disc2", 2.3),
    ]

    result = radar.analyze_wide_radar(
        referents_rows=referents,
        discovery_rows=discovery,
        max_posts_per_creator=3,
        excluded_post_ids=["p_disc_1"],
    )

    assert result["total_posts_considered"] == 4  # 3 from ref1 + 1 from disc2 (disc1 was excluded)
    assert not result["is_fallback"]


def test_wide_fresh_pool_20_creators_with_cooldown_and_exclusion():
    """
    Validates the Master Plan specification:
    - Pool of 20 accounts with 5 posts each (100 posts)
    - Capped to max 3 posts per creator
    - Excludes posts used in last 30 days
    - Applies 7-day cooldown to recently used creators, pushing them to the end
    """
    radar = MarketRadar()
    all_rows = []
    excluded_posts = []

    # Generate 20 creators with 5 posts each (R from 1.5 to 3.0)
    for c_idx in range(20):
        handle = f"@creator_{c_idx:02d}"
        for p_idx in range(5):
            post_id = f"post_c{c_idx:02d}_p{p_idx}"
            r = 1.6 + (p_idx * 0.25)
            # Mark first post of creators 0-4 as excluded (simulating used in last 30 days)
            if c_idx < 5 and p_idx == 4:
                excluded_posts.append(post_id)
            all_rows.append(_make_dummy_row(post_id, handle, r))

    assert len(all_rows) == 100
    assert len(excluded_posts) == 5

    # 3 creators used in the last 7 days
    recent_creators = ["@creator_00", "@creator_01", "@creator_02"]

    # Execute wide radar analysis
    result = radar.analyze_wide_radar(
        referents_rows=all_rows[:50],
        discovery_rows=all_rows[50:],
        max_posts_per_creator=3,
        excluded_post_ids=excluded_posts,
        recently_used_handles=recent_creators,
    )

    assert not result["is_fallback"]
    assert result["total_posts_considered"] == 60  # 20 creators * 3 posts = 60

    # Also verify direct sampling function respects max 3 and exclusions
    sampled = sample_wide_radar(
        all_rows,
        max_posts_per_creator=3,
        excluded_post_ids=excluded_posts,
    )
    for exc in excluded_posts:
        assert all(r.post_id != exc for r in sampled)

    # Verify each creator has at most 3 posts
    from collections import Counter
    counts = Counter(r.account_handle for r in sampled)
    assert all(count <= 3 for count in counts.values())

    # Verify rotation: none of the 3 recent creators appear in the front of rotated list
    rotated = rotate_creator_patterns(sampled, recently_used_handles=recent_creators)
    fresh_count = len(sampled) - sum(counts[c] for c in recent_creators)
    front_creators = set(r.account_handle for r in rotated[:fresh_count])
    for rec in recent_creators:
        assert rec not in front_creators

