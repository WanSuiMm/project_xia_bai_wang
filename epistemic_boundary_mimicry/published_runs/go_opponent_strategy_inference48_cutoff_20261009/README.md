# Opponent Strategy Inference OSI48 cutoff evidence

This public package preserves the two frozen 48-slot batches, exact prompts, schedules and per-slot oracle values, source snapshots, dispatch and prompt receipts, and safe final-visible response fields. Provider raw bodies, private launch records, credentials, and hidden reasoning are not part of the response projection.

Start with [cutoff results](analysis/RESULTS.md), then inspect the [attempt ledger](attempt_ledger.json) and the [original summary](original/analysis/summary.json) and [recovery summary](recovery/analysis/summary.json). The frozen source code and protocol inputs are under each batch's `inputs/` directory.

The original run contains one HTTP 403/payment failure. The recovery run contains three receipts: two strict-valid Qwen responses and one invalid GLM provider response with HTTP 200 and `ValueError`. Across both batches there were four physical attempts, including one repeated slot, and 45 of 48 unique slots were never attempted. No complete cell or aggregate oracle contrast is available.

Run `python -X utf8 -B scripts/publish_opponent_strategy_inference.py --verify` from the project root. Verification uses only the published package's frozen parser, analyzer, and inputs; it makes no provider request.
