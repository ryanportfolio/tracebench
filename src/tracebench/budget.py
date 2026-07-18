"""Hard spend cap. The runner stops — it does not warn and continue."""

from __future__ import annotations


class BudgetExceededError(RuntimeError):
    def __init__(self, spent_usd: float, cap_usd: float) -> None:
        super().__init__(f"budget exceeded: spent ${spent_usd:.4f} of ${cap_usd:.4f} cap")
        self.spent_usd = spent_usd
        self.cap_usd = cap_usd


class BudgetTracker:
    def __init__(self, cap_usd: float) -> None:
        if cap_usd <= 0:
            raise ValueError("budget cap must be positive")
        self.cap_usd = cap_usd
        self.spent_usd = 0.0

    def charge(self, cost_usd: float) -> None:
        """Record spend. Raises once total spend crosses the cap.

        The charge is recorded before raising so the final cost report is
        accurate even on the run that blew the budget.
        """
        if cost_usd < 0:
            raise ValueError("cost cannot be negative")
        self.spent_usd += cost_usd
        if self.spent_usd > self.cap_usd:
            raise BudgetExceededError(self.spent_usd, self.cap_usd)
