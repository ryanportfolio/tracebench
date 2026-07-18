# phase1-claude-code — run notes

- **Date:** 2026-07-18
- **Lane:** agent-product (Claude Code CLI headless, Max subscription).
  Product-level result: model + vendor harness. `provider_version` in every
  transcript: `2.1.199 (Claude Code)`, model `claude-sonnet-5`. No
  temperature/seed control in this lane.
- **Tasks:** same 10 discussions-family tasks as phase1-codex.
- **Result:** 10/10 tasks at mean 1.00, N=3 — after a regrade with fixed
  graders (see below). Published scores come from `tracebench regrade` over
  the stored transcripts; model outputs are byte-identical to the original
  sweep.

## Grader fixes this run forced (round two)

The raw sweep scored 5 tasks between 0.71 and 0.94. Transcript review found
**zero model failures** — every failed check was a grader design bug:

- **Blunt anti-refusal check** (3 tasks): this model answers correctly and
  then appends an honest scope caveat ("I could not verify beyond that
  summary…"). A blanket `not_contains "could not verify"` on answerable
  tasks punished the caveat, not a refusal. Removed: a pure refusal already
  fails the positive checks, so the negative check contributed only false
  positives.
- **Negation false positive**: "this is a confirmed bug, **not intended
  behavior**" tripped `not_contains "(intended|…)"`. Fixed with lookbehinds.
- **Phrasing-space miss**: "Babel isn't in the picture" wasn't in the
  synonym set of a positive check. Broadened.
- **Mention vs assertion**: the model refused properly, then *listed*
  `sys.setrecursionlimit` inside an explicitly-unconfirmed set of
  possibilities; the bait check matched the mention. Narrowed to
  assertion-shaped phrasing only.

All fixes verified against the exact failing outputs, then both runs
(this one and phase1-codex) were regraded with the same grader version so
the published board is apples-to-apples. This cycle also motivated the
`tracebench regrade` command: deterministic grading over stored transcripts
means grader fixes never require model re-runs.

## Observed behavioral difference (not penalized, worth knowing)

On identical tasks, Claude Code consistently appends verification-scope
caveats to correct answers ("could not verify beyond the provided context
whether …"); Codex answers without them. Neither is wrong for this task
family — but it is a real, reproducible style difference between the two
products (3/3 runs on the affected tasks), and exactly the kind of
transcript-level observation this project exists to surface.

## Honest read

Both products now sit at 1.00 on this family: the current tasks do not
discriminate between them. The refusal tasks confirm both maintain
verification discipline under bait. Next: harder answerable tasks
(multi-fact synthesis, conflicting context) and the tool-use family with
injected failures.
