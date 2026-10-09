# OSI48 final two-slot completion amendment

The user authorized inspecting the result, completing missing slots if necessary, and uploading only after completion on 2026-10-10.

## Frozen selection

Supplement01 stopped after 45 requests: 44 strict-valid replies, one GLM token-limit truncation, and one unstarted request. Together with the two retained recovery replies, 46 of the original 48 slots are valid. Retain all 46 valid replies, including probability/action errors. Supplement only:

1. `OSI_GLM_PERSISTENT_H4_ONESA_R2`: HTTP 200, requested model returned, `finish_reason=length`, 4096 completion tokens, no final visible text.
2. `OSI_GLM_PERSISTENT_H7_ONESA_R2`: not previously dispatched.

Selection uses completion validity only. No incorrect answer is regenerated.

## Output-budget repair

Both selected GLM requests use `max_tokens=16384`, increased from 4096 to address the observed truncation. All prompt bytes, model ID, temperature .5, endpoint chat/completions, enabled thinking, low reasoning effort, streaming off, timeout 300 seconds, parser rules, and oracle remain unchanged. No posterior feedback, worked example, new repeat, or model fallback is supplied.

This is a two-request amended completion overlay. Its 48 selected observations have mixed output ceilings: 22 GLM replies at 4096, two GLM replies at 16384, and 24 Qwen replies at 8192. Thus a completed overlay must not be labeled a complete execution under the original uniform GLM ceiling. Report the unchanged-budget 46/48 cutoff alongside the amended overlay and note that equal internal reasoning effort is not established by these requested controls.

At most two new physical requests are authorized by this batch, one per selected slot. The cumulative bound is 51 (1 original + 3 credential recovery + 45 supplement01 + 2 final requests), superseding the earlier bounds. Any transport, envelope, model, truncation, or final-format failure stops this small batch without an automatic resend. The pre-existing invalid attempts remain intact.

## Execution and analysis

Run: `epistemic_boundary_mimicry/runs/opencode_go_20261010_opponent_strategy_inference48_tail02`.

The run freezes the exact pending prompts, the 46 retained IDs and their source receipts, configurations, source code, and this amendment before dispatch. Credentials are read through hidden input or the existing environment and never stored. Raw envelopes and hidden reasoning are discarded; safe visible replies, finish reasons, usage, and diagnostic categories are retained.

Offline analysis reuses the registered oracle, weighting and estimands, preserving undefined group results if any selected slot remains invalid/missing. It separately reports selected-slot counts, all physical attempts, the output-ceiling amendment, and the unchanged-budget cutoff. There is no new all-or-nothing scientific pass/fail gate.

```text
python -X utf8 -B scripts/complete_opponent_strategy_tail.py --prepare
python -X utf8 -B scripts/complete_opponent_strategy_tail.py --execute-hidden
python -X utf8 -B scripts/complete_opponent_strategy_tail.py --analyze
```
