from __future__ import annotations

import pytest

from tests.conftest import make_result, make_task
from tracebench.graders import UnknownCheckTypeError, get_grader, run_checks
from tracebench.models import Check, ToolCall


def check(type_: str, **params) -> Check:
    weight = params.pop("weight", 1.0)
    return Check(type=type_, params=params, weight=weight)


class TestResponseContains:
    def test_pass(self):
        grader = get_grader("response_contains")
        assert grader(check("response_contains", pattern="wor.d"), make_result("world")).passed

    def test_fail(self):
        grader = get_grader("response_contains")
        assert not grader(check("response_contains", pattern="absent"), make_result()).passed

    def test_case_insensitive(self):
        grader = get_grader("response_contains")
        c = check("response_contains", pattern="HELLO", case_insensitive=True)
        assert grader(c, make_result("hello world")).passed

    def test_case_sensitive_by_default(self):
        grader = get_grader("response_contains")
        assert not grader(check("response_contains", pattern="HELLO"), make_result()).passed


class TestResponseNotContains:
    def test_pass_when_absent(self):
        grader = get_grader("response_not_contains")
        assert grader(check("response_not_contains", pattern="absent"), make_result()).passed

    def test_fail_when_present(self):
        grader = get_grader("response_not_contains")
        assert not grader(check("response_not_contains", pattern="hello"), make_result()).passed


class TestToolCallMade:
    def test_pass_by_name(self):
        grader = get_grader("tool_call_made")
        result = make_result(tool_calls=[ToolCall(name="gh_api", arguments={"path": "/repos"})])
        assert grader(check("tool_call_made", name="gh_api"), result).passed

    def test_fail_wrong_name(self):
        grader = get_grader("tool_call_made")
        result = make_result(tool_calls=[ToolCall(name="read_file")])
        assert not grader(check("tool_call_made", name="gh_api"), result).passed

    def test_arguments_subset_match(self):
        grader = get_grader("tool_call_made")
        result = make_result(
            tool_calls=[ToolCall(name="gh_api", arguments={"path": "/repos", "method": "GET"})]
        )
        c = check("tool_call_made", name="gh_api", arguments={"path": "/repos"})
        assert grader(c, result).passed

    def test_arguments_mismatch_fails(self):
        grader = get_grader("tool_call_made")
        result = make_result(tool_calls=[ToolCall(name="gh_api", arguments={"path": "/orgs"})])
        c = check("tool_call_made", name="gh_api", arguments={"path": "/repos"})
        assert not grader(c, result).passed

    def test_missing_expected_argument_fails(self):
        grader = get_grader("tool_call_made")
        result = make_result(tool_calls=[ToolCall(name="gh_api", arguments={})])
        c = check("tool_call_made", name="gh_api", arguments={"path": "/repos"})
        assert not grader(c, result).passed


class TestNoToolCalls:
    def test_pass(self):
        grader = get_grader("no_tool_calls")
        assert grader(check("no_tool_calls"), make_result()).passed

    def test_fail(self):
        grader = get_grader("no_tool_calls")
        result = make_result(tool_calls=[ToolCall(name="gh_api")])
        assert not grader(check("no_tool_calls"), result).passed


class TestRunChecks:
    def test_weighted_score(self):
        task = make_task(
            checks=[
                Check(type="response_contains", params={"pattern": "hello"}, weight=3.0),
                Check(type="response_contains", params={"pattern": "absent"}, weight=1.0),
            ]
        )
        results, score = run_checks(task, make_result("hello"))
        assert [r.passed for r in results] == [True, False]
        assert score == pytest.approx(0.75)

    def test_all_pass_scores_one(self):
        task = make_task()
        _, score = run_checks(task, make_result("hello"))
        assert score == 1.0

    def test_unknown_check_type_raises(self):
        task = make_task()
        task.checks[0].type = "vibes_check"
        with pytest.raises(UnknownCheckTypeError):
            run_checks(task, make_result())
