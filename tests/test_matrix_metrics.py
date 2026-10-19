"""Tests for matrix metrics: median calculation and relative performance (Task 3)."""
import pytest
from src.matrix.metrics import (
    calculate_account_median,
    calculate_relative_performance,
    RelativePerformanceResult,
)


def test_calculate_account_median_odd_and_even():
    # Odd number of views
    views_odd = [1000, 2500, 5000, 12000, 15000]
    assert calculate_account_median(views_odd) == 5000.0

    # Even number of views
    views_even = [1000, 2000, 4000, 6000]
    assert calculate_account_median(views_even) == 3000.0


def test_calculate_account_median_filters_invalid_data():
    # Discard zeros, negatives, and None values
    views_dirty = [0, None, 10000, 20000, -50, 30000, 0]
    assert calculate_account_median(views_dirty) == 20000.0

    # Empty or only zero views
    assert calculate_account_median([]) == 0.0
    assert calculate_account_median([0, 0, None]) == 0.0


def test_calculate_relative_performance_classifications():
    # Winner: R >= 1.5
    winner = calculate_relative_performance(views=30000, median=20000)
    assert winner.multiplier == 1.5
    assert winner.is_winner is True
    assert winner.classification == "ganador"

    # Outlier winner
    super_winner = calculate_relative_performance(views=60000, median=20000)
    assert super_winner.multiplier == 3.0
    assert super_winner.is_winner is True
    assert super_winner.classification == "ganador"

    # Average: 0.7 <= R < 1.5
    average = calculate_relative_performance(views=20000, median=20000)
    assert average.multiplier == 1.0
    assert average.is_winner is False
    assert average.classification == "promedio"

    # Low: R < 0.7
    low = calculate_relative_performance(views=10000, median=20000)
    assert low.multiplier == 0.5
    assert low.is_winner is False
    assert low.classification == "bajo"


def test_calculate_relative_performance_zero_median():
    res = calculate_relative_performance(views=15000, median=0.0)
    assert res.multiplier == 0.0
    assert res.is_winner is False
    assert res.classification == "indeterminado"
