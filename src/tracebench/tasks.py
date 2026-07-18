"""Task file loading and validation.

Tasks live as YAML files under a directory (one task per file). Validation is
strict; a malformed task fails the whole load with the offending path named.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from tracebench.graders import get_grader
from tracebench.models import Task


class TaskLoadError(ValueError):
    pass


def load_task_file(path: str | Path) -> Task:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        task = Task.model_validate(raw)
    except Exception as exc:
        raise TaskLoadError(f"{path}: {exc}") from exc
    for check in task.checks:
        try:
            get_grader(check.type)
        except Exception as exc:
            raise TaskLoadError(f"{path}: {exc}") from exc
    return task


def load_tasks(tasks_dir: str | Path) -> list[Task]:
    tasks_dir = Path(tasks_dir)
    if not tasks_dir.is_dir():
        raise TaskLoadError(f"tasks directory not found: {tasks_dir}")
    paths = sorted(tasks_dir.rglob("*.yaml"))
    if not paths:
        raise TaskLoadError(f"no task files (*.yaml) under {tasks_dir}")
    tasks = [load_task_file(p) for p in paths]
    ids = [t.id for t in tasks]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise TaskLoadError(f"duplicate task ids: {duplicates}")
    return tasks
