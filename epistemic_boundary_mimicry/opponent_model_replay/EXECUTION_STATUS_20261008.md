# OMC16: launch verification snapshot

This is a one-time launch check, not a final result or recurring monitor. Current state is governed by the exact run's dispatch and response receipts.

Original run `opencode_go_20261008_opponent_model16_01`: one dispatched request returned HTTP 403 / payment, zero model answers, 15 unstarted. Its HALTED/error records remain unchanged.

Authorized credential recovery: `opencode_go_20261008_opponent_model16_02`. The [recovery amendment](RECOVERY_20261008.md) documents reuse of the previously authorized newer credential. The original and recovery manifests (creation time excepted), schedule and all 16 forecast prompt bytes match exactly. Original outcomes, models, generation controls and parser are unchanged.

At recovery launch verification: **8 actual dispatch receipts, 7 saved valid forecasts**, all HTTP 200 with exact returned model `glm-5.3`; one request in flight. Status RUNNING, no halt reason. The private launch manifest hash matches the frozen run manifest. No new Speaker or R1 call was sent. Completion, score or hypothesis support is not claimed by this snapshot.

The current evidence must be scored with the frozen source-linked outcomes and unresolved SQ02/B1/Q6, not inferred from selected explanations. Public design and scripts contain no credential; launch, session and machine information remain in ignored private storage. No GitHub upload is requested by the present task.

Offline analysis entry for the recovered run:

```text
python -X utf8 -B scripts/analyze_opponent_model_replay.py --run epistemic_boundary_mimicry/runs/opencode_go_20261008_opponent_model16_02
```
