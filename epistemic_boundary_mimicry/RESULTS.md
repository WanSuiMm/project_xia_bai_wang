# OpenCode Go: two completed endpoints

Four configurations were attempted; two reached a Judge decision. Both completed
games use the same fictional laminated-panel dossier, Qwen3.8 Max speakers and
a GLM-5.3 Judge. No opening statements or Host truth were provided.

| Condition | ASK actions | Pick | Target reader | Confidence | Correct |
|---|---:|---|---|---:|---|
| Strong | 3 | B | A | 0.80 | No |
| Boundary-aware | 8 | A | A | 0.70 | Yes |

The Strong Judge preferred the bluffer's concrete, internally linked account and
bounded omissions. This is a decision rationale, not a validated explanation of
the model's mechanism. Boundary-aware reached the correct pick after eight ASK
actions. These two outcomes do not establish an instruction effect: there is one
independent dossier, no repetitions, no passive baseline, and unbalanced arms.
Do not compare directly with earlier Arena Claude/Gemini results: provider,
models, sampling configuration and protocol differ.

Frozen control ended after two ASK actions because B's complete visible reply
contained literal unescaped newlines inside JSON. The reverse Boundary-aware
slot failed before interrogation: GLM returned no visible setup text, with
the setup marker in its reasoning field. Neither failure is a Judge mistake.
Original attempts remain intact; repair/recovery results are separate.

The initial 8192-token migration pilot is excluded from these results. It had a
thinking-only truncation; a new run froze 32768 tokens and temperature 0.5 after
an unrelated capacity qualification passed for each model. Reasoning is the
deployment default, no model fallback or semantic retries were used, and each
role's private native history remained isolated. Only visible requested answers
were forwarded. The full four-slot attempt used a conservative allowance estimate
of $1.614, not a claim about an additional subscription charge.

Read [protocol](API_PROTOCOL.md), then [public evidence](published_runs/go_two_completed_20261004/README.md).
Recompute hashes, exact relays and scores from repository root:

```powershell
python -X utf8 -B scripts/analyze_boundary_go_snapshot.py
```

Boundary placement, overclaim and underclaim annotations remain pending. No
stable ToM, model ranking, post-training cause or interrogation benefit is claimed.
