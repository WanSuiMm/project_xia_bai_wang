# R0 five-position low-reasoning completion supplement

This is an additive, changed-configuration engineering supplement to the [79/84 cutoff snapshot](../go_frozen_replay_r0_20261008/summary.json). It preserves that snapshot's registered analysis and exact primary receipts. The five requests reused the original prompts, temperature, model, token limit, strict parser, and 120-word reason cap; they requested `thinking.type=enabled` and `reasoning_effort=low`. The proxy's handling of that request was not independently verified, so this does not identify a controlled reasoning-effort effect.

The source status remains `INTERRUPTED` because its final status update failed. This package records the derived state separately: all five dispatches have valid response receipts. The new replies are five `ABSTAIN` decisions at p_A=0.5. A first-valid-per-position overlay covers 84/84 distinct positions, with GLM-5.3 blind at 21/21. That overlay does not mean the registered primary run completed successfully; its original result remains 77/84. Any earlier dispatched request without a receipt stays an unknown historical attempt and is not replaced by the new reply.

## Reading route

1. [Prior cutoff summary](../go_frozen_replay_r0_20261008/summary.json) and [unchanged primary analysis](../go_frozen_replay_r0_20261008/analysis.json).
2. [Completion summary and GLM blind overlay](summary.json).
3. [Per-position first-valid selection](selection.json) and [five-request configuration/prompt mapping](completion_manifest.json).
4. [Five allowlisted dispatches](dispatches/) and [five exact visible-response receipts](responses/).
5. [Sanitized completion/status provenance](completion_status.json) and [source hashes](provenance.json).

From the repository root, `python -X utf8 -B scripts/publish_frozen_replay_r0_completion.py` audits this package. The script uses only Python's standard library and local frozen public records; it makes no network/model calls and does not require the private source run. `SHA256SUMS.txt` contains SHA-256LF hashes for every published file except itself.
