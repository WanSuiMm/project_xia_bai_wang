# OpenCode Go R0 Frozen replay: public cutoff snapshot

This directory publishes the frozen primary queue and the incomplete recovery supplements as of 2026-10-08. The primary 84-slot analysis stays fixed; supplemental responses are reported separately and do not change its registered estimates.

## Reading route

1. [Delivery note](../../replay_r0/DELIVERY_20261008.md) and [frozen protocol/results](../../replay_r0/RESULTS_20261007.md).
2. [Primary analysis](analysis.json) and its [rendered report](RESULTS.md).
3. [Coverage, conditional counts, slot weights, and cutoff summary](summary.json).
4. [Supplement dispatch/status ledger and original-request mapping](supplemental_status.json), plus the [primary attempt ledger](dispatch_ledger.json).
5. [Frozen manifest](manifest.json), [cohort](cohort.json), [prompt modules](prompt_modules.json), the 14 exact prompts in `prompts/`, and all 84 allowlisted primary receipts in `responses/`.
6. [Source freeze/reference hashes](provenance.json) and [published-file SHA-256LF list](SHA256SUMS.txt).

## What the records show

The registered primary run attempted all 84 frozen slots and contains 77 valid responses. Its analyzer output is reproduced from these public records. The seven excluded slots remain visible with their original receipt statuses and exact visible text. In the original EB05 D1, GLM blind replicate 3, the retained visible reply contains a fenced JSON object with a 121-word reason; after removing the fence the JSON parses, but the frozen receipt remains `invalid_json_or_schema` and the analyzer's 120-word reason cap is exceeded.

Two later supplements add two distinct first-valid responses for originally invalid positions, yielding 79/84 distinct positions with a valid answer for descriptive cutoff accounting. Those supplement records remain outside `analysis.json` and `RESULTS.md`. Supplement 07 halted after two dispatches, including one HTTP 429. Supplement 06 has a source status of `RUNNING` but is published as an incomplete snapshot: the process was absent at the publication snapshot, a lock file remained, one dispatched slot has no response and is marked `dispatched_no_response` with unknown outcome, and three slots were not dispatched. This does not mark either supplement complete.

Only the provider-visible answer text is included; hidden reasoning is not stored. Billing for transport failures and dispatched requests without a response is unknown. The package contains no credentials, private account links, local machine paths, host identifiers, or process identifiers.

## Audit and dependencies

The exporter and offline auditor are [`scripts/publish_frozen_replay_r0.py`](../../../scripts/publish_frozen_replay_r0.py). From the repository root, run `python -X utf8 -B scripts/publish_frozen_replay_r0.py` to audit this directory. The check uses Python's standard library and the local `scripts/analyze_frozen_replay_r0.py`; it makes no network or model calls and does not require the private source run. `SHA256SUMS.txt` hashes each published file except itself after normalizing text line endings to LF.
