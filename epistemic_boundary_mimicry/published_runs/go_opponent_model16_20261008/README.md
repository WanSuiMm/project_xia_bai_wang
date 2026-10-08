# OMC16 public evidence

Start with [results](../../opponent_model_replay/RESULTS_20261008.md) and [delivery](../../opponent_model_replay/DELIVERY_20261008.md), then [small summary](analysis/summary.json). Exact per-request files are secondary evidence.

16 strict-valid GLM forecasts on eight old Qwen prompts; no new Speakers. Four authored families, two forecast repeats. B0 mean .0373, B1 .1292; every individual probability is below .5. Old coding: 47 clear non-admissions and one unresolved SQ02/B1/Q6. Three-family complete-case scores and four-family forecasts are distinct. No population calibration claim.

The separate [initial failed attempt](failed_attempt.json) is HTTP 403/payment with no visible model reply, not a scientific outcome. Recovery preserves the design. Original hashes and public-copy hashes are separately recorded. Account/session/launch records, credentials, raw error bodies and hidden reasoning are excluded.

From the repository root: `python -X utf8 -B scripts/publish_opponent_model_replay.py`. Default is public-only, offline and credential-free. `--export` requires original private sources and refuses overwrite.
