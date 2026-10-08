# JES32 bounded completion amendment — 2026-10-09

The user requested completion of the remaining requests after the original run stopped. This is a failure-selected engineering supplement to [the frozen protocol](PROTOCOL_20261008.md), not a new scientific condition or a clean original 32-call run.

## Selection frozen before new requests

Parent: `opencode_go_20261008_joint_epistemic_simulation32_01`. Its first two scheduled requests have strict-valid replies. The third, `JG_GLM_JJ_11_00`, returned HTTP 200, finish `stop`, a schema-valid leading JSON object, and a duplicate footer; the original receipt remains strict-invalid. The following 29 requests were not sent. The parent has three physical attempts, two strict-valid replies and a halted status. This is a formatting failure, not a truncation or quota outcome. The saved text alone does not establish whether the model or provider added the duplicate.

Retain the first two valid replies unchanged. Make exactly one new attempt at each of the remaining 30 original slots, in the original order (schedule positions 3–32). The failed third slot is called again; its original leading JSON is not retroactively accepted. Every prompt is byte-identical to the parent. Model IDs, native endpoints, temperature, reasoning controls, caps, timeout, single-call policy, seed, oracle and scoring weights are unchanged. There are no additional qualification calls, Speaker generations, repetitions or fallback models. If all requests are attempted, total physical calls are 3 original + 30 supplement = 33, for 32 selected slots.

New run: `opencode_go_20261009_joint_epistemic_simulation32_supplement01` under excluded local `epistemic_boundary_mimicry/runs/`.

## Narrow formatting amendment

Preserve the complete visible response, finish reason, original strict `parsed` and `parse_status`, plus independently recomputed completion fields. The original strict parser and original artifacts remain unchanged.

1. Accept strict-valid JSON exactly as before.
2. Otherwise, only when the original status is `invalid_response`, parse the leading JSON object with the original strict schema. Require a permitted non-truncated finish.
3. Require the entire remaining text, after stripping outer whitespace, to have this exact shape (LF line separators):

   ```text
   <|assistant|>_p_A:<JSON number>
   decision:<A or B or ABSTAIN>
   reason:<exact original reason>_
   ```

4. The repeated probability must be a finite, non-Boolean JSON number in [0,1], numerically identical to the leading object's probability. Decision and reason must be identical strings. The entire trailer must be consumed. Duplicate JSON keys, substantive additions, changed values, Markdown wrappers, truncation and arbitrary trailing commentary remain invalid.
5. Record acceptance as `strict` or `identical_duplicate_trailer`, never overwrite raw text or a strict-invalid status.

This deterministic, answer-independent exception was chosen after observing the original failure. It is frozen before supplementation and explicitly reported as a post-failure engineering amendment. It does not repair or improve a substantive prediction. Completion summaries must also expose strict-only sensitivity and normalization counts.

## Collection and stopping

One new attempt per selected slot, maximum concurrency one, no automatic re-generation or transport retry. A received reply with an isolated content/schema failure or truncation is recorded and the remaining fixed slots continue. A transport failure, non-200 HTTP outcome, invalid provider envelope or unexpected returned model halts the worker; such positions are not model outcomes and are not silently resubmitted. Credential input is hidden and transient; launch, account/session and machine receipts remain private and excluded.

The first requested supplement slot is the interface check within the 30, not an extra paid smoke. Offline tests cover original strict rejection, exact duplicate acceptance, contradictory footer rejection, duplicate keys, non-finite/Boolean numbers, arbitrary trailing text and truncated finishes. Freeze selected slots, all 32 original prompts, parent receipt hashes, parameters, parser, collector, analyzer and this amendment before sending any new request.

## Analysis

Retain the two original strict-valid endpoints; use only the single supplement attempt for each of the other 30 planned slots. Never choose the more accurate of multiple attempts. Keep the original registered run's incomplete analysis separate. The derived completion table is a failure-selected, format-amended overlay with per-slot provenance and all failed receipts retained.

Apply the original prior-predictive weights, posterior ground truth and per-model/per-mechanism metrics. A cell's primary weighted excess Brier score and practical gate exist only when its entire positive support has valid endpoints; missing/invalid mass is not renormalized. Overall completion requires all 32 selected slots. Report strict-only coverage and scores in parallel. One call per slot cannot estimate API sampling variance or justify a population, adaptive-interrogation, Actor-simulation or general ToM conclusion.

Commands from the repository root:

```text
python -X utf8 -B scripts/run_joint_epistemic_supplement.py --self-test
python -X utf8 -B scripts/run_joint_epistemic_supplement.py --prepare
python -X utf8 -B scripts/run_joint_epistemic_supplement.py --audit
python -X utf8 -B scripts/run_joint_epistemic_supplement.py --launch-hidden
python -X utf8 -B scripts/analyze_joint_epistemic_supplement.py
```

Among the listed commands, only `--launch-hidden` starts a worker that sends the bounded requests; the others are offline. The unlisted `--execute` mode is the launcher's internal worker entry and requires the private launch receipt, matching manifest hash and untouched prepared state. At completion, the worker writes `analysis/completion_summary.json` inside the new run. Frozen parent files are never edited.
