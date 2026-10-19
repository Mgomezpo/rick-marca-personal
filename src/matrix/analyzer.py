"""Winning patterns extractor and dual market radar (referents + discovery)."""
from typing import List, Dict, Any, Optional
from collections import defaultdict

from src.matrix.models import MatrixRow
from src.graph.state import WinningPattern


def find_winning_patterns(
    rows: List[MatrixRow],
    min_multiplier: float = 1.5,
    min_pieces: int = 1,
) -> List[WinningPattern]:
    """
    Extracts winning empirical patterns from matrix rows with R >= min_multiplier.
    Groups by (hook_type, format, emotion) and computes average multiplier and supporting evidence.
    """
    winners = [r for r in rows if r.relative_performance >= min_multiplier]
    if not winners:
        return []

    groups: Dict[tuple, List[MatrixRow]] = defaultdict(list)
    for row in winners:
        key = (row.hook_type, row.format, row.emotion)
        groups[key].append(row)

    patterns: List[WinningPattern] = []
    for (hook_type, fmt, emotion), group_rows in groups.items():
        if len(group_rows) < min_pieces:
            continue

        avg_r = round(sum(r.relative_performance for r in group_rows) / len(group_rows), 2)
        examples = [r.hook_text for r in group_rows if r.hook_text][:3]

        pattern = WinningPattern(
            pattern_id=f"pat_{hook_type}_{fmt}_{emotion}".replace(" ", "_"),
            tipo_hook=hook_type,
            formato=fmt,
            emocion=emotion,
            rendimiento_relativo_promedio=avg_r,
            piezas_respaldo=len(group_rows),
            ejemplos=examples,
        )
        patterns.append(pattern)

    # Sort descending by relative performance, then by number of pieces
    patterns.sort(key=lambda p: (p.rendimiento_relativo_promedio, p.piezas_respaldo), reverse=True)
    return patterns


class MarketRadar:
    """
    Dual market radar service:
    1. Referentes de cabecera (brand_referents)
    2. Radar de nicho (discovery de tendencias)
    With graceful degradation / fallback on slow network or missing data.
    """

    DEFAULT_PATTERNS = [
        WinningPattern(
            pattern_id="pat_default_confesion",
            tipo_hook="confesion_error",
            formato="historia_personal",
            emocion="vulnerabilidad",
            rendimiento_relativo_promedio=2.2,
            piezas_respaldo=5,
            ejemplos=[
                "Le pagué dos mil dólares a una agencia y casi me quiebran.",
                "El mayor error que cometí al lanzar mi primer producto.",
            ],
        ),
        WinningPattern(
            pattern_id="pat_default_quiebre",
            tipo_hook="quiebre_creencia",
            formato="demostracion_mecanismo",
            emocion="autoridad",
            rendimiento_relativo_promedio=1.8,
            piezas_respaldo=4,
            ejemplos=[
                "Hacer más contenido no te dará más clientes.",
                "Por qué los tutoriales paso a paso ya no convierten.",
            ],
        ),
    ]

    def analyze_dual_radar(
        self,
        referents_rows: List[MatrixRow],
        discovery_rows: List[MatrixRow],
    ) -> Dict[str, Any]:
        """
        Analyze both referents and discovery matrix rows.
        Returns top patterns, per-source breakdown, and fallback indicator.
        """
        referents_patterns = find_winning_patterns(referents_rows)
        discovery_patterns = find_winning_patterns(discovery_rows)

        combined_rows = referents_rows + discovery_rows
        all_patterns = find_winning_patterns(combined_rows)

        if not all_patterns:
            return {
                "referents_patterns": [],
                "discovery_patterns": [],
                "top_patterns": self.DEFAULT_PATTERNS,
                "top_pattern": self.DEFAULT_PATTERNS[0],
                "is_fallback": True,
            }

        return {
            "referents_patterns": referents_patterns,
            "discovery_patterns": discovery_patterns,
            "top_patterns": all_patterns,
            "top_pattern": all_patterns[0],
            "is_fallback": False,
        }

    def analyze_wide_radar(
        self,
        referents_rows: List[MatrixRow],
        discovery_rows: List[MatrixRow],
        max_posts_per_creator: int = 3,
        excluded_post_ids: Optional[List[str]] = None,
        recently_used_handles: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes wide & fresh analysis:
        Capping posts per creator, filtering out previously used post_ids (anti-solapamiento),
        and forcing rotation across creators.
        """
        combined = referents_rows + discovery_rows
        sampled = sample_wide_radar(
            combined,
            max_posts_per_creator=max_posts_per_creator,
            excluded_post_ids=excluded_post_ids,
        )
        rotated = rotate_creator_patterns(sampled, recently_used_handles)
        patterns = find_winning_patterns(rotated)

        if not patterns:
            return {
                "top_patterns": self.DEFAULT_PATTERNS,
                "top_pattern": self.DEFAULT_PATTERNS[0],
                "total_posts_considered": len(rotated),
                "is_fallback": True,
            }

        return {
            "top_patterns": patterns,
            "top_pattern": patterns[0],
            "total_posts_considered": len(rotated),
            "is_fallback": False,
        }


def sample_wide_radar(
    rows: List[MatrixRow],
    max_posts_per_creator: int = 3,
    excluded_post_ids: Optional[List[str]] = None,
) -> List[MatrixRow]:
    """
    Inverts the scraping equation:
    Instead of 40 videos from 2 creators (deep & repetitive),
    samples top `max_posts_per_creator` (e.g. 3) from each creator across a wide pool.
    Excludes previously used post IDs to eliminate duplicate analysis and overlap.
    """
    excluded = set(excluded_post_ids or [])
    filtered_rows = [r for r in rows if r.post_id not in excluded]

    by_creator: Dict[str, List[MatrixRow]] = defaultdict(list)
    for r in filtered_rows:
        by_creator[r.account_handle].append(r)

    sampled: List[MatrixRow] = []
    for handle, creator_rows in by_creator.items():
        creator_rows.sort(key=lambda x: x.relative_performance, reverse=True)
        sampled.extend(creator_rows[:max_posts_per_creator])

    return sampled


def rotate_creator_patterns(
    rows: List[MatrixRow],
    recently_used_handles: Optional[List[str]] = None,
) -> List[MatrixRow]:
    """
    Prevents mono-creator bias by pushing recently used creator handles to the back,
    forcing rotation across different creators.
    """
    recent = set(recently_used_handles or [])
    fresh = [r for r in rows if r.account_handle not in recent]
    cooldown = [r for r in rows if r.account_handle in recent]

    return fresh + cooldown

