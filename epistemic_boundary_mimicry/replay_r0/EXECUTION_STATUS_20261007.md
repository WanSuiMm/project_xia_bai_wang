# R0 dispatch status: subscription authorization required

The user authorized the complete 84-request replay on 2026-10-07. The seven existing complete Frozen payloads, two conditions, two model deployments and three repeats were frozen before dispatch. No new Speaker was generated. Offline preparation/audit passed for all 84 positions, 14 prompts and six material families.

Run: `opencode_go_20261007_frozen_replay_r0_84_01`, under the ignored `epistemic_boundary_mimicry/runs/` tree. The original manifest, prompt files, freeze hashes, dispatch receipts, HTTP-error receipts and private launch receipt are preserved there.

| Item | Count/status |
|---|---:|
| Planned experimental requests | 84 |
| Dispatched experimental requests | 2 |
| HTTP 403 error receipts | 2 |
| Valid model answers | 0 |
| Undispatched positions | 82 |
| Scientific replay result | None |

One request to each model failed before any answer or token usage was returned. The runner halted the remaining positions under its frozen 401/403/429 rule. HTTP errors are infrastructure failures, not model abstentions, probability reports or negative scientific evidence. Charged usage is unknown because these errors returned no usage record.

A bounded diagnosis then made two minimal interface checks, outside the experimental queue. The first lacked a routing-session header and received HTTP 400. The second supplied the header and received HTTP 403 with the provider's explicit explanation: the Go subscription had ended because its payment method needed authorization. Both checks returned no model answer. Authentication to the model-list endpoint had succeeded, so the failure was traced to subscription entitlement rather than the API key being absent. Account-specific URLs and identifiers are omitted from this status note.

No additional retries, billing changes, purchases or alternative-provider calls were made after the cause was identified. The API credential remains environment-only. The original audit, cohort and formalization draft were not modified.

Offline analysis preserves all missing weights and leaves complete effects, probability means and repeat-variance estimates undefined. Full-cohort completion bounds span the entire allowed risk/effect range and provide no scientific signal. Reproduce locally from the repository root:

```text
python -X utf8 -B scripts/run_frozen_replay_r0.py --audit
python -X utf8 -B scripts/analyze_frozen_replay_r0.py --run epistemic_boundary_mimicry/runs/opencode_go_20261007_frozen_replay_r0_84_01
```

After the user restores the subscription, any recovery must preserve this failed run and record an infrastructure-recovery amendment before dispatch. Use a new run directory with the same payloads, prompt modules, sampling configuration, weights and randomized schedule; all 84 intended valid sampling positions remain to be collected. The failed pre-answer requests are retained as infrastructure attempts, not silently substituted with model results. No outcome-dependent protocol change or sample selection is permitted.

This local preparation/dispatch did not authorize or perform a GitHub upload.
