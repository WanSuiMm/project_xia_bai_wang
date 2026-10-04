# Frozen control: amended recovery completed

The GLM-5.3 Judge returned **ABSTAIN after four ASK actions** against two
Qwen3.8 Max readers. Each speaker had an independent same-generator fictional
source. Host designated A's source as target, but the Judge received no
truth-linked anchor identifying that designation.

Judge's rationale: both accounts remained specific and internally coherent;
their differing names, dates and counts could belong to parallel source records.
Without an external anchor, the transcript did not justify picking either as
the Host-designated target reader. This abstention agrees with the control's
identifiability rationale. It is one exploratory trajectory, not a statistical
demonstration of chance accuracy or general boundary reasoning.

The Judge also claimed the accounts could not have been independently invented
from public context. That inference is not verified and is not a project claim.
Source-relative consistency and boundary placement annotation remain pending.

## Recovery provenance

The original trajectory failed after its second ASK because a complete visible
B reply contained literal unescaped JSON string newlines. The original record
is unchanged. An authorized separate recovery accepts those controls with
`json.loads(strict=False)`, preserves exact raw text and native role histories,
and resumes without regenerating the inherited answer.

Eight original messages are inherited; seven new physical calls add two ASK
actions and the final abstention. Sampling remains max tokens 32768, temperature
0.5, deployment-default reasoning, no openings, tools, Host truth or ASK cap.
This is an amended failure-selected recovery, not a uniform original-protocol
replicate or a comparison with the two published Strong/Boundary-aware endpoints.

Local receipt/routing audit: zero errors. It checks frozen hashes, unchanged
inherited prompts and visible text, native histories, model IDs, sampling,
exact question/answer routing, ASK counts and terminal scoring.

```powershell
python -X utf8 -B scripts/publish_boundary_frozen.py
```

The [public recovery evidence](published_runs/go_frozen_recovery_20261004/README.md)
includes both used sources and exact visible dialogue with original failure and
inheritance provenance. It is a separate snapshot; the two-endpoint Strong and
Boundary-aware snapshot is unchanged. Full native histories and provider receipts
remain in the ignored local run. The public audit checks source/message hashes,
inheritance, routing, model labels, parsed answers, ASK count and terminal.
