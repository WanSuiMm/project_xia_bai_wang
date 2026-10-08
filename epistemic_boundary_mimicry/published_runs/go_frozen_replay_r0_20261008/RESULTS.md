# R0 Frozen replay analysis

This report summarizes one fixed 7-transcript R0 queue. It is an offline analysis of the receipts present in this run directory; it does not make provider calls.

## Coverage and primary risk

The primary metric is family-equal-weight excess Brier risk against the known null $p_A^*=0.5$: $\sum_j w_j/3\sum_r(p_{A,jr}-0.5)^2$. Each EB05 transcript has weight 1/12; each other transcript has weight 1/6.

Missing, invalid, truncated, refusal, tool-use, or undispatched responses remain missing. The report does not renormalize valid responses. For incomplete cells, it shows the observed weighted contribution and the completion range $[obs, obs+0.25\times missing\ weight]$.

| Model | Condition | Planned | Valid | Missing | Fixed-null risk / partial contribution and completion range |
|---|---:|---:|---:|---:|---|
| `glm-5.3` | blind | 21 | 14 | 7 | 部分贡献 0.005139; 缺失权重 0.277778; 界 [0.005139, 0.074583] |
| `glm-5.3` | informed | 21 | 21 | 0 | 0.000000 |
| `qwen3.8-max` | blind | 21 | 21 | 0 | 0.008472 |
| `qwen3.8-max` | informed | 21 | 21 | 0 | 0.000000 |

## Blind minus Informed

Effects are reported separately by model. Incomplete outcomes use the exact completion interval $[B_{lower}-I_{upper}, B_{upper}-I_{lower}]$.

| Model | Complete effect | Observed contribution difference | Completion bounds | 95% fixed-queue Hoeffding interval |
|---|---:|---:|---:|---|
| `glm-5.3` | — | 0.005139 | [0.005139, 0.074583] | — |
| `qwen3.8-max` | 0.008472 | 0.008472 | [0.008472, 0.008472] | [-0.144768, 0.161712] (half-width 0.153239845434) |

The Hoeffding interval is shown only when every planned Blind and Informed request for that model is valid. It assumes independent new-session outputs and a stable deployment; its scope is this fixed queue. With the registered weights and three repeats, the half-width is 0.153239845434. It does not support population generalization or comparisons between models.

## Per-family effects

Family risks use equal transcript weights within each family and equal replicate weights. Partial families retain their missing-slot weight and show completion ranges.

| Model | Family | Blind risk | Informed risk | Blind − Informed |
|---|---|---:|---:|---:|
| `glm-5.3` | EB01 | 0.000000 | 0.000000 | 0.000000 |
| `glm-5.3` | EB02 | 部分贡献 0.000000; 缺失权重 0.333333; 界 [0.000000, 0.083333] | 0.000000 | 部分差 0.000000; 界 [0.000000, 0.083333] |
| `glm-5.3` | EB03 | 部分贡献 0.000000; 缺失权重 0.333333; 界 [0.000000, 0.083333] | 0.000000 | 部分差 0.000000; 界 [0.000000, 0.083333] |
| `glm-5.3` | EB04 | 0.000000 | 0.000000 | 0.000000 |
| `glm-5.3` | EB05 | 部分贡献 0.030000; 缺失权重 0.666667; 界 [0.030000, 0.196667] | 0.000000 | 部分差 0.030000; 界 [0.030000, 0.196667] |
| `glm-5.3` | EB06 | 部分贡献 0.000833; 缺失权重 0.333333; 界 [0.000833, 0.084167] | 0.000000 | 部分差 0.000833; 界 [0.000833, 0.084167] |
| `qwen3.8-max` | EB01 | 0.000000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | EB02 | 0.000000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | EB03 | 0.000000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | EB04 | 0.000000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | EB05 | 0.050833 | 0.000000 | 0.050833 |
| `qwen3.8-max` | EB06 | 0.000000 | 0.000000 | 0.000000 |

## Transcript cells and repeat-bias estimate

The reported $B=(\bar p_A-0.5)^2-s^2/3$ uses the unbiased sample variance with denominator 2 and is defined only when all three repeats in that transcript × model × condition cell are valid. Negative values are retained. Partial-cell probability means and $B$ are left undefined.

| Model | Transcript | Family | Condition | Valid / 3 | Cell excess Brier | Mean $p_A$ | Sample variance | $B$ |
|---|---|---|---|---:|---:|---:|---:|---:|
| `glm-5.3` | `EB01_D1_symmetric_frozen` | EB01 | blind | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `glm-5.3` | `EB01_D1_symmetric_frozen` | EB01 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `glm-5.3` | `EB02_D1_symmetric_frozen` | EB02 | blind | 2/3 | 部分贡献 0.000000; 缺失权重 0.333333; 界 [0.000000, 0.083333] | — | — | — |
| `glm-5.3` | `EB02_D1_symmetric_frozen` | EB02 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `glm-5.3` | `EB03_D1_symmetric_frozen` | EB03 | blind | 2/3 | 部分贡献 0.000000; 缺失权重 0.333333; 界 [0.000000, 0.083333] | — | — | — |
| `glm-5.3` | `EB03_D1_symmetric_frozen` | EB03 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `glm-5.3` | `EB04_D1_symmetric_frozen` | EB04 | blind | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `glm-5.3` | `EB04_D1_symmetric_frozen` | EB04 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `glm-5.3` | `EB05_D1_symmetric_frozen` | EB05 | blind | 1/3 | 部分贡献 0.030000; 缺失权重 0.666667; 界 [0.030000, 0.196667] | — | — | — |
| `glm-5.3` | `EB05_D1_symmetric_frozen` | EB05 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `glm-5.3` | `EB05_D2_symmetric_frozen` | EB05 | blind | 1/3 | 部分贡献 0.030000; 缺失权重 0.666667; 界 [0.030000, 0.196667] | — | — | — |
| `glm-5.3` | `EB05_D2_symmetric_frozen` | EB05 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `glm-5.3` | `EB06_D1_symmetric_frozen` | EB06 | blind | 2/3 | 部分贡献 0.000833; 缺失权重 0.333333; 界 [0.000833, 0.084167] | — | — | — |
| `glm-5.3` | `EB06_D1_symmetric_frozen` | EB06 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB01_D1_symmetric_frozen` | EB01 | blind | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB01_D1_symmetric_frozen` | EB01 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB02_D1_symmetric_frozen` | EB02 | blind | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB02_D1_symmetric_frozen` | EB02 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB03_D1_symmetric_frozen` | EB03 | blind | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB03_D1_symmetric_frozen` | EB03 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB04_D1_symmetric_frozen` | EB04 | blind | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB04_D1_symmetric_frozen` | EB04 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB05_D1_symmetric_frozen` | EB05 | blind | 3/3 | 0.100833 | 0.183333 | 0.000833 | 0.100000 |
| `qwen3.8-max` | `EB05_D1_symmetric_frozen` | EB05 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB05_D2_symmetric_frozen` | EB05 | blind | 3/3 | 0.000833 | 0.516667 | 0.000833 | 0.000000 |
| `qwen3.8-max` | `EB05_D2_symmetric_frozen` | EB05 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB06_D1_symmetric_frozen` | EB06 | blind | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |
| `qwen3.8-max` | `EB06_D1_symmetric_frozen` | EB06 | informed | 3/3 | 0.000000 | 0.500000 | 0.000000 | 0.000000 |

## Action/report consistency and null regret

Expected null loss uses the fair-target mechanism: choosing A or B has expected loss 0.5; ABSTAIN has loss 0.25. Null regret subtracts the optimal null loss 0.25. Report/action incoherence counts a decision outside the expected-loss minimizers under the reported $p_A$; at exactly 0.25 or 0.75 both boundary minimizers are accepted.

| Model | Condition | A | B | ABSTAIN | Incoherent / valid | Mean expected null loss | Mean null regret |
|---|---|---:|---:|---:|---:|---:|---:|
| `glm-5.3` | blind | 1 | 1 | 12 | 0/14 (0.000000) | 0.285714 | 0.035714 |
| `glm-5.3` | informed | 0 | 0 | 21 | 0/21 (0.000000) | 0.250000 | 0.000000 |
| `qwen3.8-max` | blind | 0 | 3 | 18 | 0/21 (0.000000) | 0.285714 | 0.035714 |
| `qwen3.8-max` | informed | 0 | 0 | 21 | 0/21 (0.000000) | 0.250000 | 0.000000 |

## Missing and invalid receipts

Missing slots by reason: `parse_status_invalid_json_or_schema` 1, `parse_status_truncated` 5, `receipt_status_transport_unknown` 1.

| Request | Transcript | Model | Condition | Replicate | Reason |
|---|---|---|---|---:|---|
| `EB05_D1_symmetric_frozen_glm-5.3_r3_blind` | `EB05_D1_symmetric_frozen` | `glm-5.3` | blind | 3 | `parse_status_invalid_json_or_schema` |
| `EB05_D2_symmetric_frozen_glm-5.3_r2_blind` | `EB05_D2_symmetric_frozen` | `glm-5.3` | blind | 2 | `parse_status_truncated` |
| `EB02_D1_symmetric_frozen_glm-5.3_r3_blind` | `EB02_D1_symmetric_frozen` | `glm-5.3` | blind | 3 | `parse_status_truncated` |
| `EB06_D1_symmetric_frozen_glm-5.3_r1_blind` | `EB06_D1_symmetric_frozen` | `glm-5.3` | blind | 1 | `receipt_status_transport_unknown` |
| `EB03_D1_symmetric_frozen_glm-5.3_r3_blind` | `EB03_D1_symmetric_frozen` | `glm-5.3` | blind | 3 | `parse_status_truncated` |
| `EB05_D2_symmetric_frozen_glm-5.3_r3_blind` | `EB05_D2_symmetric_frozen` | `glm-5.3` | blind | 3 | `parse_status_truncated` |
| `EB05_D1_symmetric_frozen_glm-5.3_r1_blind` | `EB05_D1_symmetric_frozen` | `glm-5.3` | blind | 1 | `parse_status_truncated` |

## Scope

This report contains fixed-queue descriptions only. It reports no p-values or population-level inference, does not rank the two models, and contains no noisy-cue observations. Raw response paths, raw payloads, and visible response text are not copied into the analysis outputs.
