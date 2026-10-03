# N02 — recovered judge session

Status: `completed`. User explicitly requested recovery of the missing original judge request. The same A/B openings and byte-identical original judge prompt were reused. Speaker follow-ups ran in their restored original Claude conversations; no new opening was generated. The judge used a fresh Arena Direct `gemini-3.8-flash-high` session. The prior failed request remains unchanged and is not counted as a model error.

Recovered endpoint: pick **A**, true access **A**, correct **True**, reported confidence **0.99**. The judge used 1 ASK action, containing three subquestions, before stopping. New requests/replies: **4/4**, plus two inherited openings. Minimum submission gap **42.9s**. Source isolation, exact prompt/opening reuse and original speaker-session checks: **0 audit errors**.

The query asked about the narrow strip's material/attachment, financial terms and whether other instruments/guilds appeared. A distinguished unspecified material/attachment and fee amounts from the stated responsibility rules and illustrative dispute. B continued interpreting “instrument makers” as musical instrument makers: it recalled lutes/viols and explicitly treated measuring balances as possibly belonging to a different guild. The final judge reason focused on this mismatch and A's specific procedure details.

Arena inserted an anonymous comparison on the final judge turn. It was skipped; only the subsequently displayed fixed-model response was captured. This response was distinct from the two anonymous candidates. Platform labels are not independent model-identity verification.

This is one exploratory trajectory. A familiar-world interpretation error in B and source-bounded responding in A occurred in this case; neither establishes a stable policy or an interaction advantage. No passive baseline or token-matched control was run. Keep the failed request and this authorized recovery as separate attempts, without selecting a preferred outcome.

Exact local evidence: excluded `runs/arena_20261003_naturalistic_judge_recovery01/`. Audit with `python -X utf8 -B scripts/analyze_naturalistic_judge_recovery.py`. Other planned cases remain incomplete. No GitHub push or background monitoring.
