"""CLI: `tracebench validate <tasks-dir>` and `tracebench run --config <yaml>`."""

from __future__ import annotations

import argparse
import sys

from tracebench.config import load_run_config
from tracebench.runner import RunReport, run
from tracebench.tasks import TaskLoadError, load_tasks


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        tasks = load_tasks(args.tasks_dir)
    except TaskLoadError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    by_family: dict[str, int] = {}
    for task in tasks:
        by_family[task.family.value] = by_family.get(task.family.value, 0) + 1
    print(f"OK: {len(tasks)} task(s) valid")
    for family, count in sorted(by_family.items()):
        print(f"  {family}: {count}")
    return 0


def _print_report(report: RunReport) -> None:
    print(f"run: {report.config.name}")
    print(f"transcripts: {report.n_transcripts}")
    print(
        f"cost: ${report.total_cost_usd:.4f} of ${report.config.budget_usd:.2f} cap"
        + ("  ** HALTED ON BUDGET — results are partial **" if report.halted_on_budget else "")
    )
    print()
    print("per task (mean ± stdev over n runs):")
    for agg in report.by_task:
        print(
            f"  {agg.model_id}  {agg.task_id}  "
            f"{agg.mean_score:.2f} ± {agg.stdev_score:.2f} (n={agg.n})"
        )
    print()
    print("per family (mean of task means):")
    for fam in report.by_family:
        print(
            f"  {fam.model_id}  {fam.family}  "
            f"{fam.mean_of_task_means:.2f} over {fam.n_tasks} task(s)"
        )


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_run_config(args.config)
    report = run(config, args.out)
    _print_report(report)
    print(f"\nwrote results.json + transcripts.jsonl to {args.out}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    from tracebench.report import generate_report

    out = generate_report(args.run_dir, args.out, title=args.title, note=args.note)
    print(f"wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tracebench")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate all task files in a directory")
    p_validate.add_argument("tasks_dir")
    p_validate.set_defaults(func=_cmd_validate)

    p_run = sub.add_parser("run", help="run an eval sweep from a config file")
    p_run.add_argument("--config", required=True)
    p_run.add_argument("--out", required=True, help="output directory for results + transcripts")
    p_run.set_defaults(func=_cmd_run)

    p_report = sub.add_parser("report", help="render a static HTML report from a run directory")
    p_report.add_argument("--run-dir", required=True, help="directory with results.json + jsonl")
    p_report.add_argument("--out", required=True, help="output HTML file path")
    p_report.add_argument("--title", default="tracebench results")
    p_report.add_argument("--note", default="", help="banner note shown at the top of the page")
    p_report.set_defaults(func=_cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
