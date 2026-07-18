"""Run loop: tasks x models x N runs -> graded transcripts + aggregate report.

Rules enforced here, not left to discipline:
- every run records its seed, model id, params, and cost;
- the budget cap halts the run hard (partial results are still written and
  clearly marked);
- aggregates always carry n, mean, and spread — no single-run scores.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from tracebench.budget import BudgetExceededError, BudgetTracker
from tracebench.config import RunConfig, compute_cost
from tracebench.graders import run_checks
from tracebench.models import Transcript
from tracebench.providers import build_provider
from tracebench.tasks import load_tasks


class TaskAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    task_id: str
    family: str
    model_id: str
    n: int
    mean_score: float
    stdev_score: float
    min_score: float
    max_score: float


class FamilyAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    family: str
    model_id: str
    n_tasks: int
    mean_of_task_means: float


class RunReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config: RunConfig
    halted_on_budget: bool
    total_cost_usd: float
    n_transcripts: int
    by_task: list[TaskAggregate]
    by_family: list[FamilyAggregate]


def _aggregate(transcripts: list[Transcript]) -> tuple[list[TaskAggregate], list[FamilyAggregate]]:
    by_task_key: dict[tuple[str, str], list[Transcript]] = {}
    for t in transcripts:
        by_task_key.setdefault((t.model_id, t.task_id), []).append(t)

    task_aggs = []
    for (model_id, task_id), group in sorted(by_task_key.items()):
        scores = [t.score for t in group]
        task_aggs.append(
            TaskAggregate(
                task_id=task_id,
                family=group[0].family.value,
                model_id=model_id,
                n=len(scores),
                mean_score=statistics.mean(scores),
                stdev_score=statistics.stdev(scores) if len(scores) > 1 else 0.0,
                min_score=min(scores),
                max_score=max(scores),
            )
        )

    by_family_key: dict[tuple[str, str], list[TaskAggregate]] = {}
    for agg in task_aggs:
        by_family_key.setdefault((agg.model_id, agg.family), []).append(agg)
    family_aggs = [
        FamilyAggregate(
            family=family,
            model_id=model_id,
            n_tasks=len(group),
            mean_of_task_means=statistics.mean(a.mean_score for a in group),
        )
        for (model_id, family), group in sorted(by_family_key.items())
    ]
    return task_aggs, family_aggs


def run(config: RunConfig, out_dir: str | Path) -> RunReport:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(config.tasks)
    tracker = BudgetTracker(config.budget_usd)
    transcripts: list[Transcript] = []
    halted = False

    for model_cfg in config.models:
        if halted:
            break
        provider = build_provider(model_cfg, config)
        provider_version = provider.describe_version()
        for task in tasks:
            if halted:
                break
            for run_index in range(config.runs_per_task):
                seed = config.base_seed + run_index
                result = provider.complete(task, model_cfg, seed)
                cost = compute_cost(result.usage, model_cfg.pricing)
                check_results, score = run_checks(task, result)
                transcripts.append(
                    Transcript(
                        task_id=task.id,
                        family=task.family,
                        provider=model_cfg.provider,
                        model_id=model_cfg.model_id,
                        provider_version=provider_version,
                        run_index=run_index,
                        seed=seed,
                        input_messages=task.messages,
                        output_text=result.text,
                        tool_calls=result.tool_calls,
                        usage=result.usage,
                        cost_usd=cost,
                        checks=check_results,
                        score=score,
                    )
                )
                try:
                    tracker.charge(cost)
                except BudgetExceededError:
                    halted = True
                    break

    by_task, by_family = _aggregate(transcripts)
    report = RunReport(
        config=config,
        halted_on_budget=halted,
        total_cost_usd=tracker.spent_usd,
        n_transcripts=len(transcripts),
        by_task=by_task,
        by_family=by_family,
    )

    transcripts_path = out_dir / "transcripts.jsonl"
    with transcripts_path.open("w", encoding="utf-8") as fh:
        for t in transcripts:
            fh.write(t.model_dump_json() + "\n")
    (out_dir / "results.json").write_text(
        json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8"
    )
    return report
