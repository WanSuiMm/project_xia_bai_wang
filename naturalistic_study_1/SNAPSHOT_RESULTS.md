# Naturalistic Study 1 — nine completed configurations

Publication cutoff: 2026-10-03. **9 unique configurations completed across 5 dossiers; all 9 terminal picks were correct, with 0 abstentions.** This is a descriptive completed subset of the original 24-configuration plan. The user reduced the collection target to 12 completed configurations; 3 more remain at this cutoff. Collection is awaiting human security verification, with no background monitor.

The original cutoff contributes N01_D1, the serial continuation contributes seven completed configurations, and the separately authorized fresh N02 judge recovery contributes N02_D1 once. Original failed attempts remain distinct. In particular N04_D1 and N06_D1 are missing; N06_D2 is partial at a security challenge. Missingness is not a model error and its full attempt statuses are preserved in [coverage](published_runs/nine_completed_20261003/attempt_coverage.json). Do not select whichever attempt has the preferable judgment.

C = `claude-sonnet-5-high`, G = `gpt-5.5-instant`, M = `gemini-3.8-flash-high`. These are observed Arena Direct labels; backend versions and sampling settings are unverified. Same-model speakers use independent sessions. Judge sees dialogue only, without the dossier or Host truth.

| Configuration | Speakers → Judge | True access | Pick | Reported confidence | ASK actions | Attempt |
|---|---|---|---|---:|---:|---|
| [N01_D1](published_runs/nine_completed_20261003/trajectories/N01_D1.json) | C → G | B | B | 0.97 | 2 | original cutoff |
| [N01_D2](published_runs/nine_completed_20261003/trajectories/N01_D2.json) | G → C | A | A | 0.92 | 6 | serial continuation |
| [N02_D1](published_runs/nine_completed_20261003/trajectories/N02_D1.json) | C → M | A | A | 0.99 | 1 | N02 recovery |
| [N02_D2](published_runs/nine_completed_20261003/trajectories/N02_D2.json) | M → C | B | B | 0.78 | 5 | serial continuation |
| [N03_D1](published_runs/nine_completed_20261003/trajectories/N03_D1.json) | G → M | B | B | 0.99 | 1 | serial continuation |
| [N03_D2](published_runs/nine_completed_20261003/trajectories/N03_D2.json) | M → G | A | A | 0.995 | 1 | serial continuation |
| [N04_D2](published_runs/nine_completed_20261003/trajectories/N04_D2.json) | G → C | A | A | 0.88 | 5 | serial continuation |
| [N05_D1](published_runs/nine_completed_20261003/trajectories/N05_D1.json) | C → M | A | A | 0.99 | 1 | serial continuation |
| [N05_D2](published_runs/nine_completed_20261003/trajectories/N05_D2.json) | M → C | B | B | 0.97 | 2 | serial continuation |

ASK actions range from 1 to 6. BOTH counts once, and questions may contain several subquestions; this is not an equal-token or equal-subquestion cost metric. Reciprocal configurations share a dossier, so nine configurations are not nine independent background samples.

Important cue limitation: in N03_D1 the uninformed speaker said "I can’t reliably give the report’s exact trench coordinates, layer numbers, object count, or associated finds from what I have available" and that supplying them "would be invention." This is a strong detail-availability cue, not a literal statement that it was denied source access. The judge overstated it as an explicit no-access admission. Other trajectories contain hedging or detail asymmetry. The observed 9/9 cannot establish successful detection of a consistently maintained bluff. The N05_D2 judge said its chosen speaker matched the original dossier, but it had no access to that dossier; that is a judge claim, not an independent truth check.

Question-premise caution: N01_D2 asked for a cargo-declaration mismatch procedure absent from the dossier; the informed speaker flagged the gap while the bluff supplied a plausible procedure. The judge later criticized a mismatch-related detail it had itself prompted. N04_D2 similarly asked where a lamp was stored until the next year although storage was unspecified. Such probes can reveal source boundaries, but the judge’s premise and verdict rationale are not source truth. These observations are tied to the exact trajectory records, not independently coded causal mechanisms.

Candidate observations include source-bounded uncertainty, requests for names/dates and concrete examples, and an instrument-category error in the N02 bluff. These are post-hoc case observations, not a stable behavioral taxonomy or preregistered mechanism. There is no passive baseline, human baseline, matched token budget, self-model condition or matched actor–observer test. Interrogation improvement, cross-family rankings and ToM dissociations remain untested.

Receipt/manifest/routing audit errors: **0**. Reproduce from repository root with `python -X utf8 -B scripts/analyze_naturalistic_snapshot.py` (Python standard library only). Read [protocol](PROTOCOL.md), [scope amendment](COLLECTION_SCOPE.md), then [published evidence](published_runs/nine_completed_20261003/README.md). Exact submitted prompts and visible final replies are preserved; visible Markdown-rendered capture is not asserted to equal the original generation byte stream. Only N01–N05 sources are published; unused fresh sources remain private. No new model calls were made for publication.
