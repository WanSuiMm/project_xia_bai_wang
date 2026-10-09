# OSI48 missing-slot completion amendment

Authorized on 2026-10-09 after the user requested completing the missing results and explicitly canceled GitHub delivery. This amendment authorizes collection only; no upload is performed.

## Selection and evidence preservation

The original batch `_01` stopped after one HTTP 403/payment receipt. Credential recovery `_02` stopped after three attempts: two strict-valid Qwen replies and one HTTP 200 GLM envelope/extraction failure. The raw GLM envelope was discarded, so the exact cause is unknown.

Retain the two strict-valid recovery observations regardless of their probabilities or decisions. Freeze all other 46 original scheduled slots, in their original relative order, before dispatch. Each selected slot receives one new attempt. This selection depends only on delivery/format validity, never correctness. Preserve both earlier batches and every new failed attempt. This new authorization supersedes the earlier 49-attempt recovery cap: the present bound is 46 new calls and 50 cumulative physical attempts (1 original + 3 recovery + 46 supplement). The combined 48-slot result is a completion overlay, not a clean 48-physical-call experiment.

Prompts remain byte-identical. Model IDs, endpoints, temperature, token limits, reasoning controls, independent sessions, loss function, oracle, estimands, and strict/redundant-trailer parsers remain unchanged. No new Speaker, worked example, corrective feedback, or extra repetition is introduced.

## Collection repair

The earlier collector could discard the returned model, finish reason, and usage when extracting visible content failed. The new collector records those safe fields before extraction, plus fixed-category decoding/extraction diagnostics. It does not retain raw envelopes, error prose, credentials, or hidden reasoning.

For chat/completions, a null visible-content field accompanied by an explicit token-limit finish is recorded as a received, truncated answer rather than an unexplained provider-envelope failure. A provider text-block list may be concatenated only when every block is an ordinary text block. This changes envelope handling, not acceptance of the Judge's answer: incomplete or malformed final JSON remains invalid.

The first selected experimental request is the interface check and counts among the 46 attempts. It must produce a valid response before the remaining 45 are launched. It is not an extra paid smoke call. A failed check halts and preserves evidence for an explicitly documented repair. Other provider/delivery/model failures halt; isolated schema failures are retained and collection continues. A token-limit truncation halts to avoid repeatedly spending the batch on the same unresolved budget problem. There is no hidden retry, model fallback, or probability repair.

## Provenance and analysis

New run: `epistemic_boundary_mimicry/runs/opencode_go_20261009_opponent_strategy_inference48_supplement01`.

The manifest binds parent receipts, retained IDs, pending schedule, unchanged API settings, all exact prompts, this amendment, collection code, and offline analysis code before the first new request. API credentials enter only through `OPENCODE_GO_API_KEY` in the process environment. Session and host/PID information is private.

The offline analyzer reconstructs a derived 48-slot view using the two retained parent observations and each selected slot's new receipt. It reports original and supplementary physical attempts separately. Missing/invalid cells retain undefined primary group endpoints, following the frozen protocol. No renormalization, correctness selection, or new scientific pass/fail threshold is allowed.

Entry points from the project root:

```text
python -X utf8 -B scripts/run_opponent_strategy_completion.py --prepare
python -X utf8 -B scripts/run_opponent_strategy_completion.py --first
python -X utf8 -B scripts/run_opponent_strategy_completion.py --launch
python -X utf8 -B scripts/analyze_opponent_strategy_completion.py
```
