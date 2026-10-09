# OSI48 cutoff results

The original batch stopped after one HTTP 403 response classified as a payment error. The separate recovery batch stopped after three attempts: two strict-valid Qwen responses and one invalid GLM provider response (HTTP 200, `ValueError`). The original failure remains in its own batch.

| Batch | Planned | Attempts | Receipts | Valid | Invalid | Missing |
|---|---:|---:|---:|---:|---:|---:|
| Original | 48 | 1 | 1 | 0 | 1 | 47 |
| Recovery | 48 | 3 | 3 | 2 | 1 | 45 |

Across both batches there were **4 physical attempts** over **3 unique slots**. The first recovery call repeated the original failed slot; **45 of 48 slots were never attempted**. The two valid replies are both Qwen responses. No complete model-by-condition cell exists, so registered cell endpoints and aggregate oracle contrasts are undefined. Per-slot exact oracle values remain in each frozen schedule.

This is an incomplete cutoff record, not a scientific all-or-nothing verdict. The offline analyzer keeps missing slots unweighted and returns null for incomplete cell aggregates. No paid calls or retries are made by export or verification. See [the attempt ledger](../attempt_ledger.json) and each batch's [registered summary](../original/analysis/summary.json) and [recovery summary](../recovery/analysis/summary.json).
