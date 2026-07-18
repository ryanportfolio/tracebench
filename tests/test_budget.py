from __future__ import annotations

import pytest

from tracebench.budget import BudgetExceededError, BudgetTracker


def test_under_cap_accumulates():
    tracker = BudgetTracker(cap_usd=1.0)
    tracker.charge(0.4)
    tracker.charge(0.4)
    assert tracker.spent_usd == pytest.approx(0.8)


def test_exceeding_cap_raises_but_records_spend():
    tracker = BudgetTracker(cap_usd=1.0)
    tracker.charge(0.9)
    with pytest.raises(BudgetExceededError) as excinfo:
        tracker.charge(0.2)
    assert tracker.spent_usd == pytest.approx(1.1)
    assert excinfo.value.cap_usd == 1.0


def test_exactly_at_cap_is_allowed():
    tracker = BudgetTracker(cap_usd=1.0)
    tracker.charge(1.0)
    assert tracker.spent_usd == pytest.approx(1.0)


def test_negative_cost_rejected():
    tracker = BudgetTracker(cap_usd=1.0)
    with pytest.raises(ValueError):
        tracker.charge(-0.1)


def test_nonpositive_cap_rejected():
    with pytest.raises(ValueError):
        BudgetTracker(cap_usd=0)
