# Reverse Boundary-aware recovery

GLM-5.3 speakers were interrogated by Qwen3.8 Max. After **two ASK actions**,
the Judge selected **A at confidence 0.78**, but the target reader was **B**.
This is a wrong attribution in one amended recovery trajectory.

The Judge's stated reason favors A's invented names, panel identifiers, tray and
room labels, and documentary details as a closer match to the shared public
context. B reported the actual Corda/foldglass source, which omitted individual
panel identifier values. That rationale is evidence of what the Judge said;
it does not establish that specificity caused the decision or validate the
Judge's interpretation of the source. Source-relative annotation remains pending.

Original failure: GLM A's private READY request returned empty visible content.
The READY marker in private reasoning was not forwarded or treated as a reply.
The authorized [recovery amendment](API_RECOVERY_PROTOCOL.md) starts fresh role
histories with the public-only Judge first. Each Speaker receives its original
private initialization together with the first requested question; no separate
READY request and no substantive opening. Only visible requested answers reach
the Judge. Max tokens 32768, temperature .5, default reasoning, no tools, Host
truth or ASK cap. Literal JSON controls are decoded with `strict=False`.

The recovery has seven new physical calls and no inherited answers. Exact
prompts, source, visible responses and original failure provenance are in the
[public snapshot](published_runs/go_reverse_recovery_20261004/README.md).
Public-only audit checks hashes, routing, model IDs, no READY, ASK count and gold:

```powershell
python -X utf8 -B scripts/publish_boundary_reverse.py
```

All four selected slots now have endpoints, under mixed original/recovery
protocols. This is one independent dossier and unbalanced model/condition
coverage. It is not a population accuracy estimate, reciprocal model ranking,
causal instruction effect, or controlled comparison with Arena Claude/Gemini.
The Frozen ABSTAIN remains a distinct identifiability control, not a forced pick.
