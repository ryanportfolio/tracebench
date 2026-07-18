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


def _cmd_regrade(args: argparse.Namespace) -> int:
    from tracebench.regrade import regrade_run

    report = regrade_run(args.run_dir, args.tasks, args.out)
    _print_report(report)
    print(f"\nregraded {report.n_transcripts} transcript(s) -> {args.out} (no model calls)")
    return 0


def _cmd_schema(args: argparse.Namespace) -> int:
    from tracebench.uidata import export_schemas

    for path in export_schemas(args.out):
        print(f"wrote {path}")
    return 0


def _cmd_ui_data(args: argparse.Namespace) -> int:
    from tracebench.uidata import stage_ui_data

    manifest = stage_ui_data(args.runs_dir, args.out, note=args.note)
    print(f"wrote {manifest}")
    return 0


def _cmd_ui(args: argparse.Namespace) -> int:
    from tracebench.uiserver import serve

    serve(args.runs_dir, port=args.port)
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

    p_regrade = sub.add_parser(
        "regrade", help="rescore a stored run with current graders (no model calls)"
    )
    p_regrade.add_argument("--run-dir", required=True, help="directory with results.json + jsonl")
    p_regrade.add_argument("--tasks", required=True, help="tasks directory the run used")
    p_regrade.add_argument("--out", required=True, help="output directory for regraded artifacts")
    p_regrade.set_defaults(func=_cmd_regrade)

    p_schema = sub.add_parser("schema", help="export model JSON Schemas (the UI type contract)")
    p_schema.add_argument("--out", required=True, help="directory to write *.schema.json into")
    p_schema.set_defaults(func=_cmd_schema)

    p_ui_data = sub.add_parser("ui-data", help="stage run directories + manifest for the UI")
    p_ui_data.add_argument("--runs-dir", required=True, help="directory containing run subdirs")
    p_ui_data.add_argument("--out", required=True, help="output data directory")
    p_ui_data.add_argument("--note", default="", help="banner note shown in the UI")
    p_ui_data.set_defaults(func=_cmd_ui_data)

    p_ui = sub.add_parser("ui", help="serve the dashboard UI over local runs")
    p_ui.add_argument("--runs-dir", required=True, help="directory containing run subdirs")
    p_ui.add_argument("--port", type=int, default=8321)
    p_ui.set_defaults(func=_cmd_ui)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
