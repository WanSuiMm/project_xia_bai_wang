# Opponent Strategy Inference OSI48 completion overlay

This package preserves the original cutoff, supplement and two-slot tail as distinct evidence batches. It includes all 48 exact prompts, selected final-visible replies, all 51 safe physical-attempt receipt sets, the frozen source code and protocols, parser-derived results, and source-to-public hash mappings. Provider raw envelopes, hidden reasoning, launch receipts, credentials and machine paths are excluded.

The completion status is **COMPLETE_VALID**: 48/48 selected strict-valid slots. The two named GLM tail requests used a 16384-token output ceiling; the other GLM requests used 4096 and Qwen requests used 8192. Their actual completions used 358 and 575 output tokens. The original-budget endpoint remains 46/48. Treat this as a mixed-budget finite-stimulus result, not a same-budget completion or a general capability claim.

Start with [results](analysis/RESULTS.md), then read [selected summary](analysis/summary.json), [slot selection](selection.json), and [physical attempt ledger](attempt_ledger.json). The previous [original cutoff package](cutoff/README.md) is retained. Source snapshots and the tail amendment are under `supplement01/inputs/` and `tail02/inputs/`.

Verify in a clean checkout with `python -X utf8 -B scripts/publish_opponent_strategy_completion.py --verify`. Verification is offline and uses only this package.
