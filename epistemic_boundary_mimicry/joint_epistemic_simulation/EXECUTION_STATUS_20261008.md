# JES32 historical launch snapshot

The user authorized the small known-mechanism joint-response qualification on 2026-10-08. Read the [frozen protocol](PROTOCOL_20261008.md) for the exact generating process and practical posterior-recovery criterion. This page records dispatch, not a completed result.

New local run ID: `opencode_go_20261008_joint_epistemic_simulation32_01`, under the excluded `epistemic_boundary_mimicry/runs/` directory. All 32 prompts, the exhaustive oracle table, schedule, protocol and collection/analysis/parser/transport snapshots were frozen before any request.

At launch verification, the saved status timestamp was `2026-10-08T23:03:12.322682+08:00`:

| Item | Verified snapshot |
| --- | --- |
| Planned requests | 32 Judge calls, 16 per model |
| Mechanism support per model | MARGINAL 12, JOINT 4 |
| State | RUNNING |
| Dispatched requests | 2 |
| Saved replies | 1 |
| Strict-valid replies | 1 |
| Worker | Live |
| Durable private launch receipt | Saved |
| Manifest vs launch receipt hash | Match |

The first scheduled request, `JG_GLM_JM_10_11`, returned exact model `glm-5.3`, HTTP 200, finish `stop` and strict-valid JSON. It is included in the 32, not an additional paid smoke. The observed A vector is 10 and B vector 11 under MARGINAL. The correct posterior is p_A=0; GLM reported 0.1111111111111111 and chose B. Its visible reason invokes an unsupported “both non-readers” possibility despite the stated exactly-one-Reader mechanism. This is one partial observation, not a model-level conclusion or an aggregate gate result. Frozen inputs and scoring are unchanged. Qwen delivery has not yet been verified at this snapshot.

Offline finite-space and mocked-request checks passed with zero network calls: correct support/weights/posteriors, identical response rendering, host metadata excluded from Judge prompts, exact model-specific request parameters and strict JSON handling. An independent mathematical design review confirmed the .75/.50 optimal forced accuracies and .125/.25 Bayes Brier risks under the disclosed assumptions.

Primary scoring is predictive-weighted posterior squared error, separately for each model/mechanism. Missing cells never receive a renormalized primary score. Correct ambiguity and abstention remain distinct from wrong identity selection. The qualification is limited to this exhaustive finite battery and one call per cell; it does not establish spontaneous Actor simulation, adaptive interrogation or strategic ToM.

Entry commands from the standalone repository root:

```text
python -X utf8 -B scripts/run_joint_epistemic_simulation.py --audit
python -X utf8 -B scripts/analyze_joint_epistemic_simulation.py
```

Both commands are offline. No extra Speaker rollout, naturalistic main study, automatic retry, fallback model, recurring monitor or GitHub publication was launched. API credentials and private machine/session/launch records remain excluded from code and scientific documentation.
