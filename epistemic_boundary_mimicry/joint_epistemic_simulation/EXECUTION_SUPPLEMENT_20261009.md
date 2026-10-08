# JES32 supplement launch snapshot — 2026-10-09

The user authorized completion of the remaining requests. The [completion amendment](SUPPLEMENT_PROTOCOL_20261009.md) freezes one failed-slot retry and 29 previously unsent requests, retaining the two original strict-valid replies. Original prompts and model parameters remain unchanged; the original halted run and its strict-invalid third receipt remain preserved.

New excluded local run: `opencode_go_20261009_joint_epistemic_simulation32_supplement01`. Its 30 selected requests, all 32 original prompts, parent receipt hashes, code, parser exception and analysis method were frozen at zero new requests. Offline parser/selection and incomplete-overlay checks passed. Preparation and launch are restricted to this one directory and refuse re-use.

The verified status timestamp is `2026-10-08T17:49:21.273482+00:00` (2026-10-09 in Asia/Shanghai):

| Item | Verified snapshot |
| --- | --- |
| Supplement planned calls | 30: 15 per model |
| New dispatched requests | 3 |
| New captured replies | 2 |
| New completion-valid replies | 2 |
| Retained original strict-valid replies | 2 |
| Combined selected valid slots | 4 / 32 |
| Worker state | RUNNING, live |
| Private launch receipt | Saved |
| Launch vs manifest hash | Match |
| Frozen input and receipt audit | PASS |

The first new request retries `JG_GLM_JJ_11_00`. It returned HTTP 200, exact `glm-5.3`, finish `stop`, strict-valid JSON, p_A=.5 and `ABSTAIN`, matching the known JOINT posterior and decision cost. The narrow duplicate-trailer exception was not needed for this reply. This is a dispatch/interface check and one finite-cell observation, not a complete aggregate result. The original first GLM diagnostic report of 1/9 at oracle zero remains retained without regeneration.

The worker sends one attempt per selected slot, records isolated content failures and continues the remaining fixed slots, and halts on infrastructure or unexpected-model failures. No automatic transport retry, replacement model, additional repetition or recurring monitor is active. API keys are hidden launcher input and process environment only; account/session and machine launch records remain excluded.

At completion the worker writes the separate `analysis/completion_summary.json`. The original registered analysis remains INCOMPLETE; the derived first-attempt completion overlay reports strict-only sensitivity, normalization counts, exact predictive weights and per-slot provenance. Missing support never receives a renormalized primary score. Total physical attempts would be 33 if all 30 supplement requests are attempted, for 32 selected slots.

Offline commands from the repository root:

```text
python -X utf8 -B scripts/run_joint_epistemic_supplement.py --audit
python -X utf8 -B scripts/analyze_joint_epistemic_supplement.py
```

This launch snapshot has not been published to GitHub. The earlier cutoff-publication work was interrupted by the user’s completion request.
