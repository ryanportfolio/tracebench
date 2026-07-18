"""Grader registry. Graders are pure functions: (check, result) -> CheckResult.

Deterministic by construction — same inputs, same grade, always. LLM-as-judge
lanes (later phase) will live behind the same interface but are a last resort,
never the default.
"""

from __future__ import annotations

from collections.abc import Callable

from tracebench.models import Check, CheckResult, ProviderResult, Task

Grader = Callable[[Check, ProviderResult], CheckResult]

_REGISTRY: dict[str, Grader] = {}


class UnknownCheckTypeError(ValueError):
    pass


def register(type_name: str) -> Callable[[Grader], Grader]:
    def decorator(fn: Grader) -> Grader:
        if type_name in _REGISTRY:
            raise ValueError(f"grader already registered: {type_name}")
        _REGISTRY[type_name] = fn
        return fn

    return decorator


def get_grader(type_name: str) -> Grader:
    try:
        return _REGISTRY[type_name]
    except KeyError:
        raise UnknownCheckTypeError(
            f"unknown check type: {type_name!r} (registered: {sorted(_REGISTRY)})"
        ) from None


def registered_types() -> list[str]:
    return sorted(_REGISTRY)


def run_checks(task: Task, result: ProviderResult) -> tuple[list[CheckResult], float]:
    """Run every check on the task; return per-check results and weighted score in [0, 1]."""
    results = [get_grader(check.type)(check, result) for check in task.checks]
    total_weight = sum(check.weight for check in task.checks)
    score = sum(r.weight for r in results if r.passed) / total_weight
    return results, score


# Importing builtin registers the built-in graders as a side effect.
from tracebench.graders import builtin as builtin  # noqa: E402
