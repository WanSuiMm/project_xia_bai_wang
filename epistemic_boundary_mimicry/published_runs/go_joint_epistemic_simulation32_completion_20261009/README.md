# Joint Epistemic Simulation32 completion evidence

This package contains the finite known-mechanism Judge qualification and its separately frozen completion overlay. It preserves all 32 exact prompts, all 33 final-visible response receipts, both schedules and configurations, the original incomplete summary, and the completion summary.

Start with [results](analysis/RESULTS.md), then read the [completion summary](analysis/completion_summary.json) and [original registered summary](analysis/original_summary.json). The [attempt ledger](attempt_ledger.json) shows which physical receipt was selected for each fixed slot. Exact prompts and receipts are supporting evidence.

The original run attempted three of 32 requests and remains `INCOMPLETE` with two strict-valid responses and one strict-invalid third response. The supplement made one attempt for each of the other 30 slots. The completion overlay contains 32 strict-valid selected slots from 33 physical attempts; the invalid original third response remains excluded. All 30 supplement responses passed the original strict parser, so the narrow normalization count is zero.

The completed finite-cell gate is `FAIL`: GLM-5.3/MARGINAL primary excess Brier is 0.018896604938, above the frozen 0.01 limit. This qualification covers only the enumerated positive-support packets under the stated known mechanism. It does not establish population calibration, population Theory of Mind, Actor strategy, or general model performance.

The package includes frozen analyzer, runner, parser, prompt-module, and protocol snapshots. Run `python -X utf8 -B scripts/publish_joint_epistemic_simulation.py --verify` from the project root for a public-package-only check. Verification reads this package only and makes no provider request.
