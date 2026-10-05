# Offline exploratory coding and fixed replay cohort

This is retrospective, model-assisted first-pass annotation of the existing canonical API corpus, not a new model experiment or a confirmatory analysis. Read this report, then `coding_summary.json`, then selected `annotations/` files. The original evidence and recovery lineage remain unchanged. The user subsequently authorized GitHub delivery of these artifacts; neither analysis nor delivery makes experimental provider calls.

## Coverage and interpretation

The corpus contains 13 canonical trajectories from six material families: five complete strategic trajectories, seven complete Frozen trajectories, and one partial Frozen trajectory. Coding covers all 107 observed Speaker answers and 57 ASK actions; terminal reasoning is available for 12 trajectories. Continuations are merged with their original trajectory rather than counted as additional samples.

| Corpus slice | Trajectories | Observed answers | ASK actions | Terminal rationales |
|---|---:|---:|---:|---:|
| Strategic Strong / Boundary-Aware | 5 | 32 | 19 | 5 |
| Frozen, including partial | 8 | 75 | 38 | 7 |
| Total | 13 | 107 | 57 | 12 |

The [frozen codebook](../CODEBOOK_20261005.md) separates source support from target relevance. Frozen readers are checked against their own finite source. Strategic bluffers are compared with the target source only as a documentary proxy; a mismatch is not automatically an internal contradiction or a failed bluff. Exact quotations are checked mechanically, followed by review of flagged interpretations. These annotations are not independent human double coding, and no reliability coefficient is claimed.

Issue spans are illustrative findings within answer events, not an exhaustive census of atomic claims. Counts in `coding_summary.json` describe flagged events and trajectories, not claim-level error rates. An unflagged answer is not certified entirely correct. Ambiguous findings remain in the annotations and are excluded from definite issue counts. ASK categories can overlap; evidence-linked follow-ups require a cited earlier answer.

## Decision-relevant observations

First-pass descriptive counts: all 13 trajectories contain at least one explicit source-boundary statement; 12 contain a follow-up linked to a specific earlier answer (28 of 57 ASK actions). These counts describe this selected corpus and the coding rule, not independence, effectiveness or correct boundary placement. The final mechanical audit reports zero errors across all 13 annotations and the seven replay payloads.

* **Boundary language is not itself evidence of correct boundaries.** The strategic cases contain both source-consistent limitations and confidently attributed details absent from the reference. Compare the cited source and answer spans, rather than simply counting expressions of uncertainty.
* **Rationale support and identification must be scored separately.** In Frozen, a reader can quote its own source correctly, yet fidelity, style or proximity to public-context wording does not identify an independently random target designation. This limitation does not imply every stylistic observation is factually false.
* **Some apparent inconsistencies are misreadings.** In EB06_D1, the Judge treats an opening caution as a late addition, although the source opens with that caution and the first answer already states its substance. It also conflates denying a formal table layout with denying that a sheet was mentioned. See [annotation](annotations/EB06_D1_symmetric_frozen.json).
* **A plausible access inference need not prove access.** EB04's Judge argues that public context alone could not produce shared framework sentences. The context omits those sentences, but the absolute impossibility claim is not established by this transcript. See [annotation](annotations/EB04_D1_symmetric_frozen.json).
* **Candidate-detail affirmation is observable without a causal claim.** In EB02 Boundary-Aware, the Judge requests a present-or-absent check for newly introduced names and a storm-bell; B affirms them while A rejects them. They are absent from the supplied source. This supports a documentary mismatch and an interrogation pattern, but the Judge's stronger claim that such agreement is impossible for any source reader is unsupported. See [annotation](annotations/EB02_D1_boundary_aware.json).

These are candidate interaction phenomena supported by particular spans. The corpus does not estimate causal instruction effects, autonomous-interrogation benefits, model rankings or population accuracy. Trajectory lengths, initialization and recovery histories differ. Reciprocal directions and repeated conditions within a material family are correlated; 107 answer events are not 107 independent experimental samples. Annotation was not blinded to already available outcomes.

## Fixed preparation for later decision replay

[REPLAY_COHORT.md](REPLAY_COHORT.md) fixes all seven complete Frozen dialogues without selecting on original outcome, confidence or rationale. They span six material families and have six GLM Judges and one Qwen Judge. The partial EB06_D2 record contributes observed interaction evidence but has no terminal score and is excluded from this replay cohort.

`replay_cohort.json` contains hashed payloads with public context and ordered questions/answers only. Private source inputs, role setup, target label, original decision, confidence and rationale are omitted. Speaker quotations and original leading questions remain visible. `freeze.json` binds the codebook, inventory, inputs and cohort before annotation. This fixes the cohort, not a future blind/informed prompt, sampling plan or statistical endpoint. A new matched blind replay would be needed to compare with an informed-null replay; the historical active Judge is not that matched control.

## Verification

From the repository root, run `python -X utf8 -B scripts/audit_offline_coding.py`. It verifies frozen hashes, all event indices, cited text spans, issue schema and replay payload shape, and regenerates `coding_summary.json`. It performs no provider calls. Mechanical validation checks quotation integrity and coverage; it does not independently validate every scientific interpretation.
