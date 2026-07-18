from __future__ import annotations

import pytest

from tests.conftest import make_task
from tracebench.tasks import TaskLoadError, load_task_file, load_tasks

VALID_TASK_YAML = """\
id: sample-001
family: tool_use
title: sample
provenance:
  source_workflow: gh-api-queries
  source_type: public
  note: sample fixture
messages:
  - role: user
    content: list open issues
tools:
  - name: gh_api
    description: call the GitHub API
    input_schema:
      type: object
checks:
  - type: tool_call_made
    params:
      name: gh_api
"""


def write_task(directory, name, text):
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def test_load_valid_task_file(tmp_path):
    path = write_task(tmp_path, "sample.yaml", VALID_TASK_YAML)
    task = load_task_file(path)
    assert task.id == "sample-001"
    assert task.tools[0].name == "gh_api"


def test_malformed_yaml_names_file(tmp_path):
    path = write_task(tmp_path, "bad.yaml", "id: [unclosed")
    with pytest.raises(TaskLoadError, match="bad.yaml"):
        load_task_file(path)


def test_missing_provenance_rejected(tmp_path):
    text = VALID_TASK_YAML.replace("provenance:", "not_provenance:")
    path = write_task(tmp_path, "bad.yaml", text)
    with pytest.raises(TaskLoadError):
        load_task_file(path)


def test_unknown_check_type_rejected_at_load(tmp_path):
    text = VALID_TASK_YAML.replace("type: tool_call_made", "type: vibes_check")
    path = write_task(tmp_path, "bad.yaml", text)
    with pytest.raises(TaskLoadError, match="vibes_check"):
        load_task_file(path)


def test_load_tasks_recurses_and_sorts(tmp_path):
    (tmp_path / "sub").mkdir()
    write_task(tmp_path / "sub", "a.yaml", VALID_TASK_YAML)
    write_task(tmp_path, "b.yaml", VALID_TASK_YAML.replace("sample-001", "sample-002"))
    tasks = load_tasks(tmp_path)
    assert [t.id for t in tasks] == ["sample-002", "sample-001"]


def test_duplicate_ids_rejected(tmp_path):
    write_task(tmp_path, "a.yaml", VALID_TASK_YAML)
    write_task(tmp_path, "b.yaml", VALID_TASK_YAML)
    with pytest.raises(TaskLoadError, match="duplicate"):
        load_tasks(tmp_path)


def test_empty_dir_rejected(tmp_path):
    with pytest.raises(TaskLoadError, match="no task files"):
        load_tasks(tmp_path)


def test_missing_dir_rejected(tmp_path):
    with pytest.raises(TaskLoadError, match="not found"):
        load_tasks(tmp_path / "nope")


def test_committed_example_tasks_are_valid():
    tasks = load_tasks("tasks")
    assert any(t.id == "disc-000-schema-example" for t in tasks)
    # make_task used here only to prove fixtures and real tasks share one schema
    assert type(tasks[0]) is type(make_task())
