# tracebench

[![CI](https://github.com/ryanportfolio/tracebench/actions/workflows/ci.yml/badge.svg)](https://github.com/ryanportfolio/tracebench/actions/workflows/ci.yml)
[![Live results](https://img.shields.io/badge/results-live%20dashboard-blue)](https://ryanportfolio.github.io/tracebench/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Can your AI coding agent admit it's wrong?**

tracebench replays moments from my agent sessions where things went
sideways. A `git fetch` failed silently and the agent reported "nothing to
pull, every origin commit is local" from stale cached refs. An agent
insisted "I can't touch the hosting platform" while the CLI it needed sat
installed and authenticated. Each task freezes one of those decision points
and scores what today's agent products do next.

- **Session-derived.** Each task file names its source workflow, what was
  altered in reconstruction, and how much weight that provenance claim
  carries. Nothing private is published; reconstructed tasks are labeled
  ([privacy rule](#privacy-rule)).
- **Reproducible.** Grading is deterministic: weighted pattern checklists,
  no hidden judge. Re-run scoring over the published transcripts and you
  get identical numbers; CI verifies this on every push and weekly
  ([`scripts/check_regrade_drift.py`](scripts/check_regrade_drift.py)).
- **Receipts included.** Every transcript, check verdict, score, and grader
  change is committed here. Failures are annotated, not hidden.

## Results at a glance

Agent-product lane: each model driven through its own CLI (`claude -p`,
`codex exec`), N=3 runs per task; scores are means of task means.

| Task family | What it tests | claude-sonnet-5 (Claude Code CLI) | gpt-5.6-sol (Codex CLI) |
|---|---|---:|---:|
| `discussions` (10 tasks) | verify facts before answering; refuse when unverifiable | 1.00 | 1.00 |
| `correction` (8 tasks) | own mistakes and self-correct under user pushback | 0.96 | 0.81 |

`discussions` is **saturated**: every run passes every check for both
products. It stays in the weekly sweep as a regression canary; the
discriminating signal today is in `correction`. The upcoming tool-use and
long-horizon families use injected failures so they don't saturate.

Headline finding: both products deny a destructive action they didn't take
and propose safe read-only checks, but rarely notice their own earlier
claim rested on stale state after a silently failed fetch (`corr-208`,
hardest task: 0.78 vs 0.63). Per-run failure analysis:
[`results/runs/*/NOTES.md`](results/runs/).

**Explore every transcript in the [live dashboard](https://ryanportfolio.github.io/tracebench/).**

New results land weekly: a scheduled sweep re-runs both CLIs, checks
reproducibility, and publishes a dated run (`results/runs/sched-*`).

## What this measures

Four task families, each traced to a specific workflow:

| Family | Where it came from | Graded on |
|---|---|---|
| `discussions` | Side workflow: agent-assisted answering of public GitHub Discussions | Factual verification behavior, refusal when unverifiable, instruction following |
| `correction` | Frozen decision points harvested from months of agent sessions (reconstructed, labeled) | Correction uptake, evidence-based updating vs sycophancy, capability self-modeling, trust in subagent claims, ground-truthing under pressure |
| `tool_use` | Agent workflow steps: `gh api` queries, file edits, multi-step git flows | Tool selection, argument correctness, error recovery after an injected tool failure |
| `long_horizon` | Multi-step pipelines (scout → rank → read → draft) | Completion without human rescue, budget discipline, silent step-dropping |

v1 targets 20-30 tasks. Each task file records provenance, the exact
prompt and context, available tools, and the grading spec.

## Method

- **Deterministic grading first.** Exact tool-call checks, schema
  validation, citation-resolution checks. LLM-as-judge only where
  unavoidable (prose quality), with a committed rubric, a judge from a
  different provider than the model under test, and a human-labeled
  agreement set measuring judge reliability first.
- **No single-run scores.** N≥3 runs per task per model; results report
  mean and spread. Seeds fixed where the API supports them, recorded
  either way.
- **Pinned configs.** Exact model IDs and params live in committed run
  configs; no score without its config.
- **Failures are the product.** Every failure ships as an annotated
  transcript: what happened, a hypothesis for why, and its bucket in the
  [failure taxonomy](taxonomy.md). A run where everything passes teaches
  nothing.
- **Budget discipline.** Hard per-run spend cap; the runner halts rather
  than overspend and prints a cost report.
- **Grader fixes never re-run models.** Transcripts store full output;
  `tracebench regrade` rescores a stored run with zero model calls, so the
  published board stays on one grader version. Every grader-bug round is
  documented in `results/runs/*/NOTES.md`.

Scores double as training-data filters for a planned small SFT/DPO
post-training project, with this suite as the before/after measuring stick.

## Two lanes: raw API vs agent product

Same tasks, two lanes, answering different questions:

| | API lane | Agent-product lane |
|---|---|---|
| Drives | Provider APIs directly | Local agent CLIs headlessly (`claude -p`, `codex exec`) |
| Measures | The model, params pinned in config | The model **plus** its product harness (vendor system prompt, tools, scaffolding) |
| Pinned by | Exact model ID + params | Model ID + recorded CLI version (`provider_version` in every transcript) |
| Determinism | Fixed seeds where supported | None promised: no temperature/seed control; N≥3 and spread do the work |
| Cost | Metered per token, budget-capped | Subscription; zero marginal cost, modest headless volume only |

Agent-product results include the product harness by construction; that is
the point, since that is how these agents get used. They are always labeled
product-level, never model-level. Two caveats: harnesses change over time
(hence the recorded CLI version), and machine-level agent config can
influence behavior even though each run executes in an isolated empty
directory. Tasks that define their own tools run only in the API lane,
where the tool schema can be injected.

## Privacy rule

Nothing from private repositories appears in any published task, fixture,
or transcript. Tasks come from public sources or synthetic reconstructions;
when a private-workflow failure inspires a task, it is rebuilt from public
or synthetic material and the provenance note says so
(`source_type: synthetic_reconstruction`).

## Honest limits

A solo project. Results are one practitioner's workflow-specific evals:
signal about these workflows, not a general benchmark. N is small;
statistics are descriptive (mean, spread), not significance claims.
Anything unverifiable is reported as "could not verify", never guessed. The
goal is understanding failure modes, not ranking vendors.

## Results UI

Two presentation layers over the same artifacts (`results.json` +
`transcripts.jsonl`):

- **Dashboard** (`ui/`, React + TypeScript): run picker, family
  leaderboard, per-task table, transcript explorer with filters and
  full-text search. Serve it locally:

  ```sh
  npm --prefix ui install && npm --prefix ui run build   # once
  uv run tracebench ui --runs-dir .tmp/runs              # http://127.0.0.1:8321
  ```

  Deploys to GitHub Pages on every push to `main`, serving the committed
  published runs: <https://ryanportfolio.github.io/tracebench/>

- **Static report** (`tracebench report --run-dir … --out report.html`):
  one self-contained HTML file per run; the archival layer, committed
  alongside published results, works from `file://` forever.

The UI's TypeScript types are generated from the harness's pydantic models
via exported JSON Schema; CI fails if models, schemas, or generated types
drift.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync --dev
uv run pytest                     # test the harness itself
uv run tracebench validate tasks  # validate all committed task files
uv run tracebench run --config configs/dryrun.yaml --out .tmp/dryrun
```

The dry run uses the mock provider: zero API spend, but the full pipeline
(load → complete → grade → aggregate → cost report) executes end-to-end.

## Repository layout

```
src/tracebench/    harness: models, providers, graders, runner, budget, CLI
tasks/             task files (YAML, one per task); see tasks/README.md
configs/           committed run configs (model IDs, params, pricing, budget)
tests/             pytest suite for the harness (graders are code; code gets tests)
results/           published scored results per run (curated, committed)
transcripts/       published annotated failure transcripts (curated, committed)
taxonomy.md        living failure taxonomy, linking to example transcripts
```

## Roadmap

- ✅ **Phase 0**: scaffold, harness, mock provider, CI, agent-product lane
  adapters (Claude Code, Codex CLI).
- ✅ **Phase 1**: 10 discussions tasks from public threads, deterministic
  graders, both CLI lanes swept and published (saturated at 1.00).
- ✅ **Phase 2**: correction family (8 tasks), both lanes swept, grader
  calibration trail published; weekly automated sweeps + CI
  reproducibility gate.
- **Phase 3**: tool-use family with injected failures; API lane end-to-end.
- **Phase 4**: long-horizon family; LLM-judge lane with agreement check;
  taxonomy v1 populated with example transcripts.
- **Phase 5**: transcript annotation polish; trace-teardown write-ups from
  the best failures.

## Links

- Author / write-ups: [corewise.academy/about](https://corewise.academy/about)

## License

[MIT](LICENSE)
