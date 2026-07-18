"""Regrade stored transcripts against the current graders — no model calls.

Grading is deterministic and transcripts carry the full model output, so a
grader fix never requires re-running models: regrade the stored run and the
scores change while every output stays byte-identical. This is the concrete
form of the "same inputs -> same grading, always" guarantee, and it is how
grader bugs get corrected in published results without new API/CLI spend.
"""

from __future__ import annotations

import json
from pathlib import Path

from tracebench.graders import run_checks
from tracebench.models import ProviderResult, Task, Transcript
from tracebench.runner import RunReport, _aggregate
from tracebench.tasks import load_tasks


class RegradeError(ValueError):
    pass


def regrade_run(run_dir: str | Path, tasks_dir: str | Path, out_dir: str | Path) -> RunReport:
    run_dir = Path(run_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    original = RunReport.model_validate_json(
        (run_dir / "results.json").read_text(encoding="utf-8")
    )
    tasks: dict[str, Task] = {t.id: t for t in load_tasks(tasks_dir)}

    regraded: list[Transcript] = []
    for line in (run_dir / "transcripts.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        old = Transcript.model_validate_json(line)
        task = tasks.get(old.task_id)
        if task is None:
            raise RegradeError(
                f"transcript references task {old.task_id!r} not present in {tasks_dir} — "
                "regrade requires the same task set the run used"
            )
        result = ProviderResult(text=old.output_text, tool_calls=old.tool_calls, usage=old.usage)
        checks, score = run_checks(task, result)
        regraded.append(old.model_copy(update={"checks": checks, "score": score}))

    by_task, by_family = _aggregate(regraded)
    report = RunReport(
        config=original.config,
        halted_on_budget=original.halted_on_budget,
        total_cost_usd=original.total_cost_usd,
        n_transcripts=len(regraded),
        by_task=by_task,
        by_family=by_family,
    )
    with (out_dir / "transcripts.jsonl").open("w", encoding="utf-8") as fh:
        for t in regraded:
            fh.write(t.model_dump_json() + "\n")
    (out_dir / "results.json").write_text(
        json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8"
    )
    return report
