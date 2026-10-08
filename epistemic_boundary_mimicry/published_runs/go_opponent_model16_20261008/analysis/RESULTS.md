# Opponent-model replay analysis

Run `opencode_go_20261008_opponent_model16_02`: 16/16 strict-valid forecasts; 16/16 dispatched.

## Forecast probabilities independent of label coverage

| Condition | Complete families | Equal-family mean forecast |
|---|---:|---:|
| B0 | 4 | 0.0373 |
| B1 | 4 | 0.1292 |

Paired B1−B0 forecast change: 0.0919 across 4 complete forecast families.

## Six-question complete-case outcomes

| Condition | Families | Mean forecast | Mean signed error | Admission fraction | Mean-repeat Brier | Brier of mean probability |
|---|---:|---:|---:|---:|---:|---:|
| B0 | 4 | 0.0373 | 0.0373 | 0.0000 | 0.0019 | 0.0016 |
| B1 | 3 | 0.1317 | 0.1317 | 0.0000 | 0.0278 | 0.0263 |

Paired B1−B0 complete-case deltas:
- Forecast: 0.0936 across 3 families.
- Admission fraction: 0.0000 across 3 families.
- Mean-repeat Brier: 0.0259 across 3 families.
- Brier of mean probability: 0.0248 across 3 families.

## Null sensitivity

| B1 Q6 resolved as | B1 signed error | B1 mean-repeat Brier | B1−B0 Brier change |
|---|---:|---:|---:|
| 0 | 0.1292 | 0.0279 | 0.0260 |
| 1 | 0.0875 | 0.0383 | 0.0364 |

## Source-region strata

Available-event figures are pooled descriptive coverage; primary results use complete regions within family, then equal family weighting.
- explicit: available scored B0/B1=12/12, 12/12; complete-family n=4/4; paired n=4; forecast delta=0.0733; Brier delta=0.0162.
- unspecified: available scored B0/B1=12/12, 11/12; complete-family n=4/3; paired n=3; forecast delta=0.1017; Brier delta=0.0313.

## Interpretation limits

- Independent material-family N is four; calls, predictions and answer units are not independent actor outcomes.
- Observed fractions describe these fixed Speaker outputs, not known true conditional behavior probabilities.
- Repeat dispersion describes Judge sampling variability for fixed target answers only.
- Source-region labels are historical analysis metadata and were not shown to the forecaster.
- This hypothesis-guided retrospective replay does not establish population calibration, a stable strategic prior, an internal opponent model or a causal explanation.
