# Reusing existing conversations without rerunning full games

Implemented offline scope: [coding report](analysis/offline_coding_20261005/RESULTS.md) and [fixed complete-transcript cohort](analysis/offline_coding_20261005/REPLAY_COHORT.md). The frozen codebook uses answer-event coverage with illustrative issue spans, a narrower first pass than the exhaustive claim-level table proposed below. No claim-level error rates or independent human reliability are established. Seven complete replay inputs are prepared; no new replay was dispatched. This historical route proposal does not supersede the executed codebook.

Offline analysis prepared 2026-10-05. No API calls or new experiments. Inventory and terminal-blind projections are local under `analysis/transcript_reuse_20261005/`; original public snapshots remain unchanged. This inventory covers the OpenCode API EB01–EB06 stage only. Older Arena experiments can be secondary historical evidence, not merged because models, prompts, openings, truth checks and sampling qualification differ.

## What already exists

Canonical selection uses the six published completed/cutoff snapshots. Original failed EB03 prefix is not counted again alongside its continuation; inherited replies are one conversation, not independent samples.

| API group | Complete | Incomplete | Material families | Appropriate use |
|---|---:|---:|---:|---|
| Earlier same-generator Frozen, EB01–EB04 | 4 | 0 | 4 | Three abstentions and one selection; qualitative source/rationale analysis |
| Surface-diverse Frozen, EB05–EB06 | 3 | 1 | 2 | Three selections; incomplete fourth interaction usable before cutoff |
| Strong / Boundary-aware, EB01–EB02 | 5 | 0 | 2, overlapping the first row | Reader/bluffer behavior, query adaptation and presupposition uptake |

Total: 13 canonical trajectories, 12 complete endpoints, six material families, 183 physical request records and 107 visible Speaker answer events. Answers, ASK actions, reciprocal directions and recovered prefixes are not independent subjects. Seven complete Frozen endpoints consist of three abstentions and four selections; six have GLM Judge, one Qwen Judge. The remaining Qwen Frozen has no endpoint. Do not label this a balanced cross-model study or estimate a population effect from these counts.

## Reuse route 1: offline evidence-bound behavioral analysis

All 13 trajectories are usable now. Create a claim-level coding table linking trajectory ID, question index, speaker, exact answer span, own-source span and adjudication. Preserve separate rows for different claims within a compound answer.

- Source relation: explicitly supported, explicitly contradicted, unspecified, or inference with its premises. A source's silence is distinct from a statement that a procedure was not performed.
- Attribution behavior: source assertion, qualified inference, uncertainty or refusal. Overclaim requires both missing source support and presenting the detail as source-backed. Saying a possibility is plausible is not the same event.
- Interrogation behavior: documented follow-up on an earlier answer, unsupported premise introduced by Judge, quotation request, downstream consequence, or provenance question. Categories may overlap; taxonomy is exploratory and frozen before a subsequent confirmatory dataset.
- Rationale support: each substantive terminal claim paired with prior dialogue/source evidence. Distinguish a real discrepancy from a valid detail disclosed later. No causal claim about the Judge's internal computation follows from its rationale.

For Frozen, evaluate each Reader against its own assigned source, never the randomly designated target source. For the genuine Reader in strategic games, use its source. For the Bluffer, distinguish target-source mismatch from internal inconsistency; a coherent invention is not automatically a contradiction. Missing endpoint trajectories contribute question/answer coding only, not final selection or selective accuracy.

Concrete starting evidence: EB02 Boundary-aware uptake of the invented clerk/ledger; EB05 GLM's public-context alignment argument; EB05 Qwen's direct-versus-paraphrased provenance argument; EB06 GLM's late-opening-caution argument even though the supplied source opens with that caution. These are selected qualitative examples, not a systematic frequency estimate. Complete coding needs a stable codebook, checked evidence spans and independent validation before reporting annotation reliability or aggregate rates.

## Reuse route 2: fixed-transcript decision replay, not new Speaker rollouts

Seven complete Frozen dialogues are already projected in `frozen_terminal_blind_dialogues.json`. Each model payload contains only public context and chronological questions/answers. It excludes role setup prompts, private sources, target labels, original confidence, original terminal decision and final rationale. Actual quotations elicited during the dialogue remain: these were visible evidence, not leaked private inputs. IDs and metadata are for offline routing, not Judge text.

For each fixed payload, two fresh independent Judges can receive the same transcript under blind versus informed-random-target instructions. Same model/settings/output request; no additional questions. This would require 7×2 = 14 individual Judge requests, not 14 multi-turn games. It has not been run or costed. A smaller pilot could use four endpoint transcripts, yielding eight individual calls, with the selection rule fixed before new outputs.

Informed instruction must state that sources and seats were frozen before a fair independent target draw, with no target-dependent speaker behavior or external target clue. Ask for probability assigned to A plus selection/abstention and reason. Explain that abstention is available; if decision optimality is scored, specify rewards. A pure guess at .50 is distinct from claiming evidence supports .80.

Use new blind replay as the matched control. Comparing the old active terminal against an informed passive replay alone would confound mechanism disclosure with task format and session history. Replays identify a decision effect conditional on these selected fixed transcripts, not an effect on autonomous interrogation. Original questions can reveal suspicions or contain leading premises; they remain part of the controlled shared payload. The incomplete eighth dialogue is projected separately but excluded from the default endpoint replay cohort.

## Reuse route 3: same facts, alternate presentation

Old source facts can become a locked claim ledger; write an alternate realization preserving every supported/negative/unspecified boundary. Reuse the old source as one arm and run the missing alternative only for an exploratory matched follow-up. This saves runs, but prior outcomes and materials were already inspected, so it is not fresh preregistered confirmation. A stronger prospective comparison freezes both renderings, maps every fact and qualifier, then runs both independently.

Existing different-case Parallel and Diverse transcripts are not a same-facts comparison. Static rewriting of Speaker answers can test evaluation sensitivity but changes the measurement target and does not recreate natural Speaker interaction. Existing dialogue cannot show how a Speaker or adaptive Judge would have behaved under a document it never received.

## Recommended order and limits

First complete offline coding of all canonical trajectories: zero new inference cost. Next, if authorized, use terminal-blind replay for the smallest paired disclosure test. Complete the missing fourth active trajectory only as a separately recorded continuation; it is useful for cohort completeness but is not required to analyze the captured interaction. Invest in new same-fact rollouts only if the claimed presentation mechanism remains the decision-relevant uncertainty.

Current evidence can support observed strategies, checked rationale errors and examples of both abstention and unsupported target attribution. It does not establish a surface causal effect, a robust model ranking, population calibration, an informed-null reasoning failure or active-versus-passive benefit. The originally proposed 16 fresh full games are not a prerequisite for any of the offline reuse routes above.

Offline preparation entry: `scripts/prepare_transcript_reuse_analysis.py`. It verifies available public manifests, deduplicates canonical IDs, counts answered ASK actions and projects terminal-blind payloads. It refuses to overwrite the current analysis directory. Raw evidence paths and normalized hashes are saved in `inventory.json`. No upload or new API launch occurs.
