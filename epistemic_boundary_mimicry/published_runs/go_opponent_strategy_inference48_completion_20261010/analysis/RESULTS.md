# OSI48 completion overlay results

The selected-slot overlay is **48/48 strict-valid** across 51 physical attempts. It contains 46 retained replies under the original per-model settings (22 GLM at a 4096-token ceiling and 24 Qwen at 8192), plus two fixed-slot GLM replies with a 16384-token output ceiling. The 48 prompts are unchanged. This is a complete mixed-budget overlay; the original-budget endpoint remains 46/48, with GLM Persistent at 10/12.

| Model | Condition | Valid / planned | Posterior MSE ↓ | Posterior MAE ↓ | Expected decision loss ↓ | Excess decision loss ↓ |
|---|---|---:|---:|---:|---:|---:|
| glm-5.3 | PERSISTENT | 12/12 | 0.07029953 | 0.07800211 | 0.25497512 | 0.16169154 |
| glm-5.3 | REFRESHED | 12/12 | 0.00000000 | 0.00000000 | 0.25000000 | 0.00000000 |
| qwen3.8-max | PERSISTENT | 12/12 | 0.00000578 | 0.00069420 | 0.09328358 | 0.00000000 |
| qwen3.8-max | REFRESHED | 12/12 | 0.00000000 | 0.00000000 | 0.25000000 | 0.00000000 |

## Two amended GLM slots

| Request | p(A) | Oracle p(A) | Absolute error | Decision | Oracle action match | Within 1e-4 | Output tokens | Cap |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| OSI_GLM_PERSISTENT_H4_ONESA_R2 | 0.50000000 | 0.50000000 | 0.00000000 | ABSTAIN | True | True | 358 | 16384 |
| OSI_GLM_PERSISTENT_H7_ONESA_R2 | 0.02750000 | 0.01492537 | 0.01257463 | B | True | False | 575 | 16384 |

The H7 reply is strict-valid and its action matches the oracle action, while its probability estimate does not fall within 1e-4 of the oracle probability. The H4 reply used 358 output tokens; the H7 reply used 575. Those two outcomes do not establish that the earlier 4096-token truncation was caused by the cap. The tail IDs were fixed by the prior invalid and unstarted slots; no answer was selected by score.

The original-budget endpoint remains incomplete: 46/48 valid slots, including 10/12 GLM Persistent slots. The mixed-budget overlay completes slot coverage but does not replace that original-budget record. There are 12 selected stimuli per cell; these calls are not 48 independent task families. No claim is made about general model capability, internal reasoning, or a causal effect of the output cap.

The [attempt ledger](../attempt_ledger.json), [selected-slot summary](summary.json), and [two amended replies](../tail02/responses/) preserve the audit trail. Run `python -X utf8 -B scripts/publish_opponent_strategy_completion.py --verify` from the project root.
