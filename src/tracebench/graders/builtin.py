"""Built-in deterministic graders.

Each grader reads its parameters from `check.params` and grades one
`ProviderResult`. Keep these boring and exact: a grader bug is a false claim
about model behavior.
"""

from __future__ import annotations

import re
from typing import Any

from tracebench.graders import register
from tracebench.models import Check, CheckResult, ProviderResult


def _result(check: Check, passed: bool, detail: str) -> CheckResult:
    return CheckResult(type=check.type, passed=passed, weight=check.weight, detail=detail)


@register("response_contains")
def response_contains(check: Check, result: ProviderResult) -> CheckResult:
    """Pass if the response text matches `pattern` (regex, search semantics)."""
    pattern = check.params["pattern"]
    flags = re.IGNORECASE if check.params.get("case_insensitive", False) else 0
    matched = re.search(pattern, result.text, flags) is not None
    return _result(check, matched, f"pattern {pattern!r} {'found' if matched else 'not found'}")


@register("response_not_contains")
def response_not_contains(check: Check, result: ProviderResult) -> CheckResult:
    """Pass if the response text does NOT match `pattern` (regex)."""
    pattern = check.params["pattern"]
    flags = re.IGNORECASE if check.params.get("case_insensitive", False) else 0
    matched = re.search(pattern, result.text, flags) is not None
    return _result(
        check, not matched, f"pattern {pattern!r} {'found (bad)' if matched else 'absent'}"
    )


def _arguments_match(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    """Every expected key must be present in actual with an equal value.

    Subset semantics: extra actual keys are allowed so tasks can pin only the
    arguments that matter.
    """
    return all(key in actual and actual[key] == value for key, value in expected.items())


@register("tool_call_made")
def tool_call_made(check: Check, result: ProviderResult) -> CheckResult:
    """Pass if a tool call with `name` (and optional `arguments` subset) was made."""
    name = check.params["name"]
    expected_args = check.params.get("arguments")
    for call in result.tool_calls:
        if call.name != name:
            continue
        if expected_args is None or _arguments_match(expected_args, call.arguments):
            return _result(check, True, f"tool {name!r} called with matching arguments")
    made = [c.name for c in result.tool_calls]
    return _result(check, False, f"no matching call to {name!r} (calls made: {made})")


@register("no_tool_calls")
def no_tool_calls(check: Check, result: ProviderResult) -> CheckResult:
    """Pass if the model made zero tool calls."""
    made = [c.name for c in result.tool_calls]
    return _result(check, not made, f"tool calls made: {made}" if made else "no tool calls")
