# R0 recovery dispatch snapshot

This is a verified launch snapshot on 2026-10-07, not a completed replay result. The user authorized checking both credentials and using a working credential for the full 84-request queue.

| Check | Result |
|---|---|
| Existing credential, GLM | HTTP 403; subscription ended/payment authorization required |
| Newly supplied credential, GLM | HTTP 200; exact requested model and valid visible JSON |
| Newly supplied credential, Qwen | HTTP 200; exact requested model and valid visible JSON |
| Selected credential | Newly supplied; value not persisted |
| Frozen queue audit | PASS: 84 positions, 14 prompts, seven transcripts, six families |
| Scientific manifest/schedule vs run 01 | Identical except creation timestamp |
| Run 02 launch verification | Live process; four dispatched, two valid answers, one per model |

The three interface checks used unrelated availability prompts and do not count as replay observations. Their sanitized usage/error receipts are under the ignored new run. The new experimental run is `opencode_go_20261007_frozen_replay_r0_84_02`; its dispatch files, response files, manifest/freeze and private launch receipt are durable. The process reads the chosen credential only from its own environment after non-echoing terminal input. No credential value, fingerprint, prefix or account URL is saved in research files or output.

The original failed run 01 is preserved. There has been no result-dependent prompt, parameter, model, weighting, sampling-order or cohort change. The run retains its fixed no-retry rules and will halt undispatched positions if a 401/403/429 occurs. A dispatch without a response is marked `dispatched_no_response` by offline analysis, rather than assumed not sent.

Use explicit run paths from the repository root; the legacy runner's default points at run 01:

```text
python -X utf8 -B scripts/run_frozen_replay_r0.py --audit --run epistemic_boundary_mimicry/runs/opencode_go_20261007_frozen_replay_r0_84_02
python -X utf8 -B scripts/analyze_frozen_replay_r0.py --run epistemic_boundary_mimicry/runs/opencode_go_20261007_frozen_replay_r0_84_02
```

No automatic monitoring or GitHub upload is part of this dispatch. Scientific effects and valid-response completeness remain unassessed until the user requests a results check.
