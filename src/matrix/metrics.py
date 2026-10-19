"""Account median and relative performance metrics calculation."""
from typing import Sequence, Optional, Union
from pydantic import BaseModel, Field


class RelativePerformanceResult(BaseModel):
    """Result of relative performance calculation (R = views / median)."""
    multiplier: float = Field(..., description="Multiplicador relativo R")
    is_winner: bool = Field(..., description="True si R >= 1.5x")
    classification: str = Field(..., description="'ganador', 'promedio', 'bajo' o 'indeterminado'")


def calculate_account_median(views_list: Sequence[Optional[Union[int, float]]]) -> float:
    """
    Calculate the exact median views for an account, discarding 0, negative or None values.
    Returns 0.0 if there are no valid positive views.
    """
    if not views_list:
        return 0.0

    valid_views = [
        float(v) for v in views_list
        if v is not None and isinstance(v, (int, float)) and v > 0
    ]

    if not valid_views:
        return 0.0

    valid_views.sort()
    n = len(valid_views)
    mid = n // 2

    if n % 2 == 1:
        return float(valid_views[mid])
    else:
        return float((valid_views[mid - 1] + valid_views[mid]) / 2.0)


def calculate_relative_performance(views: float, median: float) -> RelativePerformanceResult:
    """
    Calculate relative performance multiplier R = views / median.
    - R >= 1.5x -> 'ganador' (is_winner = True)
    - 0.7x <= R < 1.5x -> 'promedio' (is_winner = False)
    - R < 0.7x -> 'bajo' (is_winner = False)
    - median <= 0 -> 'indeterminado' (is_winner = False, multiplier = 0.0)
    """
    if median <= 0 or views <= 0:
        return RelativePerformanceResult(
            multiplier=0.0,
            is_winner=False,
            classification="indeterminado",
        )

    multiplier = round(views / median, 2)
    if multiplier >= 1.5:
        classification = "ganador"
        is_winner = True
    elif multiplier >= 0.7:
        classification = "promedio"
        is_winner = False
    else:
        classification = "bajo"
        is_winner = False

    return RelativePerformanceResult(
        multiplier=multiplier,
        is_winner=is_winner,
        classification=classification,
    )
