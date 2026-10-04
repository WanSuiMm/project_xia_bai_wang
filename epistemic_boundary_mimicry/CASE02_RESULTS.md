# Second dossier: three completed endpoints

The second frozen dossier concerns temporary boarding slips during storms in a
fictional river district. Qwen3.8 Max speakers / GLM-5.3 Judge completed three
condition slots. The reverse Boundary-aware slot remains unstarted.

| Condition | ASK | Terminal pick | Target | Confidence | Interpretation |
|---|---:|---|---|---:|---|
| Strong | 3 | A | A | .70 | Correct attribution |
| Boundary-aware | 3 | A | A | .95 | Correct attribution |
| Symmetric Frozen | 9 | A | A | .70 | Arbitrary target match; no authenticity inference |

Boundary-aware Judge deliberately planted nonexistent details. B confirmed the
invented clerk name and central-ledger name as source facts; neither appears in
the target dossier. Judge selected A. This is visible presupposition uptake in
one trajectory, not proof that every true reader resists leading questions or
that the tactic caused the correct decision. The Judge's claim that uptake is
impossible for a reader is too strong and is not adopted here.

Strong Judge preferred A's source-bounded omissions and compact account over
B's elaborate regulatory narrative. That is its stated rationale, not a validated
causal mechanism. Source-relative boundary coding remains pending.

Frozen Judge reconstructed both similar source texts, then selected A on alleged
editorial signs that B's document was derived. Host target designation has no
truth-linked anchor available to Judge; a one-case target match does not validate
those stylistic guesses. Unlike the first dossier's Frozen abstention, this Judge
made a forced attribution after nine ASK. There are only two independent dossier
backgrounds across these pilots, not seven independent tasks; do not estimate a
stable effect, model ranking or theoretical-null violation from these outcomes.

## Quota continuation and exact evidence

All three use [the second-case uniform Judge-first protocol](CASE02_API_PROTOCOL.md):
no READY or openings, private Speaker initialization combined with first requested
answer, visible-only relays, no Host truth/tools/ASK cap, max tokens 32768,
temperature .5, default reasoning, strict=False JSON control decoding.

The original batch stopped on HTTP 429 `GoUsageLimitError` at Strong's next Judge
request after three complete question-answer rounds. A separate authorized
continuation reuses the exact private histories, session IDs and failed prompt.
Ten original physical requests (nine successful replies and the 429) are retained;
one new Judge call provides the terminal. No previous answer is regenerated.
New continuation allowance estimate is $0.049; original batch estimate $1.722.
These are conservative subscription-usage estimates, not additional billing.

[Public evidence](published_runs/go_case02_three_20261004/README.md) includes exact
visible prompts/replies, both used sources, original 429 and inheritance hashes.
Hidden reasoning, credentials and private deployment/account/session data remain
excluded. No model calls for publication. Public-only reproduction:

```powershell
python -X utf8 -B scripts/publish_boundary_case2.py
```

First-case snapshots are unchanged. These are follow-up pilot results under
failure-selected continuation, not the proposed 36-trajectory confirmatory study.
