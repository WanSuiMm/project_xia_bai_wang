# CSB30 launch verification

This is a historical launch snapshot, not a completed result. The user authorized the six-family, 30-call Counterfactual Source Boundary qualification on 2026-10-08. Collection runs separately from all earlier studies.

Read the [frozen protocol](PROTOCOL_20261008.md) first. Local run ID: `opencode_go_20261008_counterfactual_source_boundary30_01` under `epistemic_boundary_mimicry/runs/`. Raw sources, provider receipts, session mappings and machine launch records remain local and Git-ignored.

## Verified dispatch

At the launch check, the saved status timestamp was `2026-10-08T20:15:26.372282+08:00`:

| Item | Verified value |
| --- | --- |
| Planned provider requests | 30: 18 Speakers, 12 Judges |
| State | RUNNING |
| Dispatched requests | 4 |
| Saved replies | 3 |
| Strict-valid replies | 3 |
| Worker process | Live |
| Durable launch receipt | Saved locally |
| Manifest hash vs. launch receipt | Match |

The first scheduled request, `SP_CS02_READER_V0`, returned the exact model ID `qwen3.8-max`, a complete visible response (`end_turn`) and strict-valid answer JSON. This was a scheduled experimental call and counted within the 30; no additional paid smoke was sent. GLM Judge delivery was not yet verified at this snapshot.

## Frozen scope and interpretation

Six fresh fictional source pairs differ by one sentence giving an otherwise omitted arbitrary identifying detail. Each family has two independent Qwen Reader calls, one Qwen Strong Bluffer call and two independent GLM Judge calls. The identical saved Bluffer answer is reused across the two packets; Reader seats are fixed within pairs and balanced across families. Judges receive neither source nor version labels nor the other packet.

Offline source construction, prompt isolation, schedule/dependency binding and strict-parser checks passed before dispatch, including an independent design check. Inputs, prompts, code and analysis hashes were frozen before the first request.

The endpoint is a qualification of the source manipulation and blind attribution behavior. A Judge sees only one hidden-version packet and cannot directly observe the paired source-conditioned dependence. One draw per cell does not estimate response distributions or establish marginal/joint simulation. Target-detail semantic coding and all complete-family metrics remain pending.

No automatic retries, fallback models, extra conditions, repetitions, recurring monitor or GitHub publication were launched. The worker stops at a delivery, model-ID, truncation or schema failure and preserves the receipt.

## Local entry commands

Run from the standalone repository root. These commands inspect evidence without calling a provider:

```powershell
python -X utf8 -B scripts/run_counterfactual_source_boundary.py --audit
python -X utf8 -B scripts/analyze_counterfactual_source_boundary.py
```

The analyzer reports delivery coverage and descriptive attribution metrics. It does not substitute gold-substring presence for semantic Reader-fidelity coding. The prepared run and frozen evidence must not be overwritten.
