"""Static HTML report: one self-contained page from a run's output directory.

Reads results.json + transcripts.jsonl (exactly what the runner wrote) and
renders a leaderboard, per-task scores, and a browsable transcript viewer.
No external assets, no JS dependencies — the file works from file:// and
GitHub Pages alike, and stays truthful by construction: everything on the
page comes from the run artifacts, nothing is computed fresh here except
formatting.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from tracebench.models import Transcript
from tracebench.runner import RunReport

_CSS = """
:root {
  --ink: #1a1f2b; --ink-2: #5c6470; --ink-3: #8a919c;
  --surface: #ffffff; --surface-2: #f5f6f8; --line: #e3e6ea;
  --accent: #3667d6; --accent-soft: #dbe5f8;
  --good: #1a7f4e; --bad: #b3382c; --warn-bg: #fdf3d7; --warn-ink: #6b5310;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e8eaee; --ink-2: #a8afba; --ink-3: #7c8490;
    --surface: #14161b; --surface-2: #1d2026; --line: #2c3038;
    --accent: #7da2f0; --accent-soft: #263450;
    --good: #4fc08a; --bad: #e57368; --warn-bg: #3a3312; --warn-ink: #e8d48a;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0 auto; max-width: 1080px; padding: 2rem 1.25rem 4rem;
  font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif;
  color: var(--ink); background: var(--surface);
}
h1 { font-size: 1.5rem; margin: 0 0 .25rem; }
h2 { font-size: 1.1rem; margin: 2.25rem 0 .75rem; }
.sub { color: var(--ink-2); margin: 0 0 1rem; }
.banner {
  background: var(--warn-bg); color: var(--warn-ink);
  border: 1px solid var(--line); border-radius: 8px;
  padding: .6rem .9rem; margin: 1rem 0;
}
.tiles { display: flex; flex-wrap: wrap; gap: .75rem; margin: 1.25rem 0; }
.tile {
  background: var(--surface-2); border: 1px solid var(--line);
  border-radius: 10px; padding: .7rem 1rem; min-width: 130px;
}
.tile .v { font-size: 1.35rem; font-weight: 650; }
.tile .k { color: var(--ink-2); font-size: .8rem; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: .45rem .6rem; border-bottom: 1px solid var(--line); }
th { color: var(--ink-2); font-weight: 600; font-size: .8rem; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.bar-cell { width: 220px; }
.bar { background: var(--accent-soft); border-radius: 4px; height: 10px; position: relative; }
.bar > i {
  display: block; height: 100%; background: var(--accent);
  border-radius: 4px 0 0 4px; min-width: 2px;
}
.bar > i.full { border-radius: 4px; }
.pass { color: var(--good); font-weight: 600; }
.fail { color: var(--bad); font-weight: 600; }
details {
  border: 1px solid var(--line); border-radius: 8px;
  margin: .5rem 0; background: var(--surface-2);
}
details > summary { cursor: pointer; padding: .55rem .8rem; }
details .body { padding: .25rem .9rem .9rem; }
pre {
  background: var(--surface); border: 1px solid var(--line); border-radius: 6px;
  padding: .6rem .8rem; overflow-x: auto; white-space: pre-wrap;
  font-size: .82rem;
}
.meta { color: var(--ink-3); font-size: .8rem; }
code { background: var(--surface-2); padding: .1em .35em; border-radius: 4px; }
footer { margin-top: 3rem; color: var(--ink-3); font-size: .8rem; }
"""


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _bar(score: float) -> str:
    pct = max(0.0, min(1.0, score)) * 100
    full = " full" if pct >= 99.95 else ""
    return f'<div class="bar"><i class="{full.strip()}" style="width:{pct:.1f}%"></i></div>'


def _verdict(passed: bool) -> str:
    return '<span class="pass">✓ pass</span>' if passed else '<span class="fail">✗ fail</span>'


def load_run_dir(run_dir: str | Path) -> tuple[RunReport, list[Transcript]]:
    run_dir = Path(run_dir)
    report = RunReport.model_validate_json(
        (run_dir / "results.json").read_text(encoding="utf-8")
    )
    transcripts = [
        Transcript.model_validate_json(line)
        for line in (run_dir / "transcripts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return report, transcripts


def _render_summary(report: RunReport) -> str:
    models = ", ".join(f"{m.provider}/{m.model_id}" for m in report.config.models)
    tiles = [
        (report.config.name, "run"),
        (str(report.n_transcripts), "transcripts"),
        (f"${report.total_cost_usd:.4f}", f"cost (cap ${report.config.budget_usd:.2f})"),
        (str(report.config.runs_per_task), "runs per task"),
    ]
    tile_html = "".join(
        f'<div class="tile"><div class="v">{_esc(v)}</div><div class="k">{_esc(k)}</div></div>'
        for v, k in tiles
    )
    halted = (
        '<p class="banner">⚠ This run halted on its budget cap — results are partial.</p>'
        if report.halted_on_budget
        else ""
    )
    return f'<div class="tiles">{tile_html}</div><p class="meta">models: {_esc(models)}</p>{halted}'


def _render_family_table(report: RunReport) -> str:
    rows = "".join(
        f"<tr><td>{_esc(f.model_id)}</td><td><code>{_esc(f.family)}</code></td>"
        f'<td class="num">{f.mean_of_task_means:.2f}</td>'
        f'<td class="num">{f.n_tasks}</td>'
        f'<td class="bar-cell">{_bar(f.mean_of_task_means)}</td></tr>'
        for f in report.by_family
    )
    return (
        "<table><thead><tr><th>model</th><th>family</th>"
        '<th class="num">mean of task means</th><th class="num">tasks</th><th></th>'
        f"</tr></thead><tbody>{rows}</tbody></table>"
    )


def _render_task_table(report: RunReport) -> str:
    rows = "".join(
        f"<tr><td>{_esc(t.model_id)}</td><td><code>{_esc(t.task_id)}</code></td>"
        f"<td>{_esc(t.family)}</td>"
        f'<td class="num">{t.mean_score:.2f} ± {t.stdev_score:.2f}</td>'
        f'<td class="num">{t.n}</td>'
        f'<td class="num">{t.min_score:.2f}–{t.max_score:.2f}</td>'
        f'<td class="bar-cell">{_bar(t.mean_score)}</td></tr>'
        for t in report.by_task
    )
    return (
        "<table><thead><tr><th>model</th><th>task</th><th>family</th>"
        '<th class="num">mean ± stdev</th><th class="num">n</th><th class="num">range</th><th></th>'
        f"</tr></thead><tbody>{rows}</tbody></table>"
    )


def _render_transcript(t: Transcript) -> str:
    version = f" · {_esc(t.provider_version)}" if t.provider_version else ""
    checks = "".join(
        f"<tr><td><code>{_esc(c.type)}</code></td><td>{_verdict(c.passed)}</td>"
        f'<td class="num">{c.weight:g}</td><td>{_esc(c.detail)}</td></tr>'
        for c in t.checks
    )
    messages = "".join(
        f"<p class='meta'>{_esc(m.role)}</p><pre>{_esc(m.content)}</pre>" for m in t.input_messages
    )
    tool_calls = (
        "<p class='meta'>tool calls</p><pre>"
        + _esc(json.dumps([tc.model_dump() for tc in t.tool_calls], indent=2))
        + "</pre>"
        if t.tool_calls
        else ""
    )
    overall = _verdict(t.score >= 1.0) if t.score in (0.0, 1.0) else f"{t.score:.2f}"
    return f"""<details>
<summary><code>{_esc(t.task_id)}</code> · {_esc(t.model_id)} · run {t.run_index}
 · score {t.score:.2f} · {overall}</summary>
<div class="body">
<p class="meta">provider {_esc(t.provider)}{version} · seed {t.seed}
 · {t.usage.input_tokens} in / {t.usage.output_tokens} out tokens · ${t.cost_usd:.4f}</p>
{messages}
<p class="meta">output</p><pre>{_esc(t.output_text)}</pre>
{tool_calls}
<table><thead><tr><th>check</th><th>verdict</th><th class="num">weight</th><th>detail</th></tr>
</thead><tbody>{checks}</tbody></table>
</div>
</details>"""


def generate_report(
    run_dir: str | Path,
    out_path: str | Path,
    title: str = "tracebench results",
    note: str = "",
) -> Path:
    report, transcripts = load_run_dir(run_dir)
    note_html = f'<p class="banner">{_esc(note)}</p>' if note else ""
    failures = sum(1 for t in transcripts if t.score < 1.0)
    config_json = _esc(json.dumps(report.config.model_dump(mode="json"), indent=2))

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>{_esc(title)}</h1>
<p class="sub">Replayable agent evals distilled from real developer workflows —
one practitioner's workflow-specific evals, not a general benchmark.
Scores are mean over N runs with spread shown; no single-run claims.</p>
{note_html}
{_render_summary(report)}
<h2>Leaderboard by task family</h2>
{_render_family_table(report)}
<h2>Per-task scores</h2>
{_render_task_table(report)}
<h2>Transcripts ({len(transcripts)}, {failures} below 1.00)</h2>
{"".join(_render_transcript(t) for t in transcripts)}
<h2>Run config</h2>
<details><summary>full config (pinned model IDs and params)</summary>
<div class="body"><pre>{config_json}</pre></div></details>
<footer>Generated by <code>tracebench report</code> from results.json +
transcripts.jsonl · <a href="https://github.com/ryanportfolio/tracebench">source</a></footer>
</body>
</html>
"""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return out_path
