# JES32 completion results

The original frozen run remains `INCOMPLETE`: it scheduled 32 requests, attempted the first three, and produced two strict-valid receipts plus one strict-invalid receipt. The other 29 slots were not dispatched in that run.

The separately frozen supplement attempted the 30 slots not retained from the original. The completion overlay therefore has 32 selected strict-valid slots from 33 physical attempts. It retains the first two original receipts, excludes the original third invalid receipt, and selects one supplement attempt for each remaining slot. No supplement response used the narrow duplicate-trailer normalization.

| Model | Condition | Positive-support packets | Selected valid | Primary excess Brier | Gate |
| --- | --- | ---: | ---: | ---: | --- |
| glm-5.3 | MARGINAL | 12 | 12 | 0.018896604938 | FAIL |
| glm-5.3 | JOINT | 4 | 4 | 0.000000000000 | PASS |
| qwen3.8-max | MARGINAL | 12 | 12 | 0.000000000000 | PASS |
| qwen3.8-max | JOINT | 4 | 4 | 0.000000000000 | PASS |

The finite-cell gate is **FAIL**. GLM-5.3/MARGINAL excess Brier is 0.018896604938, above the frozen 0.01 limit. This is a finite known-mechanism Judge qualification over the enumerated packets; it does not establish population calibration, population Theory of Mind, Actor strategy, or general model performance.

The original canonical analysis is preserved separately in [original summary](original_summary.json). The completion overlay and strict-only sensitivity are in [completion summary](completion_summary.json). The exact prompts, all 33 safe final-visible response receipts, and their dispatch ledgers are secondary evidence.

The public-only check verifies frozen hashes, source and supplement schedules, receipt bindings, raw strict parsing, the zero-normalization fields, all 32 weights, and each published primary aggregate. Run `python -X utf8 -B scripts/publish_joint_epistemic_simulation.py --verify` from the project root.
