# Failure taxonomy

Living taxonomy of agent failure modes observed in tracebench runs. Each
bucket links to example transcripts as sweeps land (none published yet —
phase 0). Buckets are seeded from failure patterns observed during the real
workflows the tasks were distilled from; expect the list to change as
transcripts accumulate.

| Bucket | Definition | Example transcripts |
|---|---|---|
| `wrong-tool-selection` | A tool existed for the job; the model picked a different one (or none) | — |
| `argument-hallucination` | Right tool, invented or malformed arguments (paths, flags, API fields that don't exist) | — |
| `silent-step-dropping` | Multi-step instruction; a required step vanishes without acknowledgment | — |
| `unverified-claim-assertion` | States as fact something the provided context does not support | — |
| `premature-give-up` | Recoverable error (transient failure, fixable arguments) treated as terminal | — |
| `runaway-retry` | The opposite: retries a hopeless action past any reasonable budget | — |
| `instruction-drift` | Explicit constraint (format, scope, refusal rule) honored early, lost late | — |

Bucket assignment is part of transcript annotation (see `transcripts/`), done
by hand — this taxonomy is a reading aid, not an automated classifier.
