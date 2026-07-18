from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.conftest import make_task
from tracebench.models import Check, Message, Provenance, Task


def test_valid_task_builds():
    task = make_task()
    assert task.id == "test-task"
    assert task.family.value == "discussions"


def test_unknown_family_rejected():
    with pytest.raises(ValidationError):
        make_task(family="vibes")


def test_extra_fields_rejected():
    raw = make_task().model_dump()
    raw["surprise"] = True
    with pytest.raises(ValidationError):
        Task.model_validate(raw)


def test_provenance_source_type_restricted():
    with pytest.raises(ValidationError):
        Provenance(source_workflow="x", source_type="private", note="nope")


def test_task_requires_at_least_one_check():
    with pytest.raises(ValidationError):
        make_task(checks=[])


def test_task_requires_at_least_one_message():
    with pytest.raises(ValidationError):
        make_task(messages=[])


def test_check_weight_must_be_positive():
    with pytest.raises(ValidationError):
        Check(type="response_contains", params={"pattern": "x"}, weight=0)


def test_message_role_restricted():
    with pytest.raises(ValidationError):
        Message(role="narrator", content="x")
