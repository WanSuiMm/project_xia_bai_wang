# Latest incremental review: frozen replay and supplementary completion

Review base: `af15fd160e070ec39bb6a60c2d4f64a3474fee8d`.
Evidence head: `918400eb629616bf88eaafc44fe154dd8d468c99`.
This subsequent handoff commit is metadata-only; the evidence head stays fixed.

Read [delivery and interpretation](epistemic_boundary_mimicry/replay_r0/DELIVERY_20261008.md), [original registered results](epistemic_boundary_mimicry/replay_r0/RESULTS_20261007.md), [small completion summary](epistemic_boundary_mimicry/published_runs/go_frozen_replay_r0_completion_20261008/summary.json), then [frozen protocol](epistemic_boundary_mimicry/replay_r0/PROTOCOL_20261007.md) and [five-position engineering amendment](epistemic_boundary_mimicry/replay_r0/SUPPLEMENT05_LOW_PROTOCOL_20261008.md). Exact prompts and allowlisted responses are secondary evidence; do not reread all unchanged trajectories first. The supplied [v1.0 formalization](XiaBaiWang_Statistical_ToM_Formalization_20261007.md) predates collection and does not supersede actual execution records.

New evidence: seven fixed complete dialogues × two models × Blind/Informed × three repeats, 84 original attempts and 77 valid responses. Both models' 42/42 Informed replies are p_A=.5/ABSTAIN. Blind is also mostly null-consistent. Qwen's complete original effect is .008472, concentrated entirely in EB05, with the prespecified conservative interval including zero. GLM original Blind is 14/21; preserve its seven missing positions and fixed-weight completion bounds [.005139, .074583], rather than imputing supplementary replies into the registered primary result.

Recovery evidence is separate: two valid replies in earlier supplements, then five user-authorized low-reasoning requests, all valid p_A=.5/ABSTAIN. The first-valid overlay now covers 84/84 original positions; GLM Blind is 21/21 with descriptive risk .011042. The last five retain exact prompts, model, temperature and parser but request reasoning_effort=low. This is mixed-configuration, failure-selected completion, not 84 clean registered successes or a controlled reasoning intervention. Earlier dispatched-without-response attempts remain unknown. All five new receipts were saved before a final status-file PermissionError; source INTERRUPTED metadata is preserved and hash-bound derived evidence confirms response completion. No outstanding new request.

Unchanged: all old 13 trajectories, six material families, 107 answer events, source-relative audit labels, original terminals, the seven terminal-blind replay payloads and all earlier failed prefixes. Arena and API studies are not pooled. Random target designation is not exclusive original source access. No population calibration, model ranking, general ToM, interrogation benefit or internal Bayesian mechanism is established. The data do not support a stable violation of the explicitly disclosed independent-target mechanism.

Verification from a fresh staged checkout, without private runs or credentials: `python -X utf8 -B scripts/publish_frozen_replay_r0.py` and `python -X utf8 -B scripts/publish_frozen_replay_r0_completion.py` passed. Existing `audit_claim_corpus.py` and `audit_offline_coding.py` also passed. Public hashes, strict parsing, exact-prompt mapping, original-position deduplication, aggregate reproduction and local Markdown links were checked. Staged content passed whitespace, credential, private-URL and machine-path scans. The included standard-library mathematics checks passed in an isolated copy; numerical checks do not replace proofs.

Reviewer questions: Does explicit mechanism disclosure yield appropriately limited null-consistent reporting, without implying general evidence-use ability? How much of the original Blind contrast survives its concentration in EB05 and GLM's informative missingness? Are registered results, same-setting recovery and changed-setting completion kept distinct? Which minimal fixed-transcript control would distinguish correct null reporting from indiscriminate .5 reporting? No additional experiment is launched by this handoff.

# Previous incremental review: all-unit source and interrogation audit

Review base: `5b274e21eeb178b197ae976adc38db889517d51c`.
Evidence head: `6732aec51fafb00ca2073203e618b3b8d575aab5`.
This subsequent handoff commit is metadata-only; the evidence head stays fixed.

Read [audit findings](epistemic_boundary_mimicry/analysis/claim_audit_20261007/RESULTS.md), [small aggregate](epistemic_boundary_mimicry/analysis/claim_audit_20261007/summary.json), then [protocol](epistemic_boundary_mimicry/analysis/claim_audit_20261007/PROTOCOL.md) and [theory/evidence map](epistemic_boundary_mimicry/analysis/claim_audit_20261007/THEORY_EVIDENCE_MAP.md). Exact-offset answer labels, complete terminal units and the primary-reviewed premise ledger are secondary evidence. Do not reread unchanged old raw logs first.

New: all 1,952 operational answer sentence/clause units across 13 canonical API trajectories; all 57 query records; all 72 rationale units across 12 terminals. Primary review fixes rejected foreign propositions incorrectly labeled as Reader contradictions, preceding Bluffer claims incorrectly called Judge-first candidates, and a mixed three-accept/one-reject block previously summarized as wholesale acceptance. Query links and rationale support/target relevance are reviewed separately. The main finding is unsupported inference from text/style to provenance or an independently designated target. Strict Reader/Bluffer candidate comparisons cover 11 grouped opportunities in five trajectories but only two families; no causal uptake effect is estimated. No persistent latent-source mechanism or interrogation benefit is established.

Unchanged: six material families, 107 observed answers, original terminal outcomes, sources, failure/recovery provenance, all earlier evidence and the fixed seven-complete replay payloads. EB06_D2 remains partial. Arena is not pooled with API data. This is retrospective model-assisted review, not atomic-claim population statistics, human reliability or confirmation. Four theoretical objects are mapped to their assumptions/unmeasured parameters; formal new proofs are outside this audit.

Verification: `python -X utf8 -B scripts/audit_claim_corpus.py` runs offline with standard library only. A fresh export of the staged repository reproduced aggregates, hashes and replay-cohort integrity; link/content checks passed. No experimental API calls, continuation or replay requests. The recommended future Blind/Informed replay is not dispatched or fully preregistered here.

Reviewer questions: Are the scope-limited sentence/clause judgments and compound subclaim examples sufficient to support these descriptive findings? Are source mismatch, internal consistency, provenance and target relevance kept distinct? Does the narrow uptake pattern merit a new paired intervention, or should the fixed-transcript informed-null contrast be tested first? Which rationale misreadings recur across families without treating correlated units as independent samples?

# Previous incremental review: offline exploratory coding and fixed replay cohort

Review base: `fbf4616f9fa96dac3eb8746776dbed9b6dccace4`.
Evidence head: `39ab29c9322b2bf7f8b28c4646fc39ca7af0bd44`.
This handoff is metadata-only; the evidence head stays fixed.

Read [coding report](epistemic_boundary_mimicry/analysis/offline_coding_20261005/RESULTS.md), [frozen retrospective codebook](epistemic_boundary_mimicry/analysis/CODEBOOK_20261005.md), [small aggregate](epistemic_boundary_mimicry/analysis/offline_coding_20261005/coding_summary.json), then [seven-dialogue replay cohort](epistemic_boundary_mimicry/analysis/offline_coding_20261005/REPLAY_COHORT.md). Per-event annotations and input JSON are secondary evidence; do not open all long transcripts first.

New: model-assisted first-pass coding of all 13 canonical API trajectories, 107 answer events, 57 ASK actions and 12 terminal rationales across six material families. All 13 have source-boundary language; 12 have at least one evidence-linked follow-up (28 ASK total), descriptive coding only. Rationale evidence support is separate from target relevance. Reviewed examples distinguish misread caution/table statements, unsupported absolute access claims and accurate but non-identifying style observations. Exact spans and selected interpretations were checked; no independent human reliability or exhaustive atomic-claim error rates. Frozen readers use their own source; strategic bluffers use a clearly identified target-source proxy.

Cohort status: all seven complete Frozen dialogues included regardless of original decision; target labels, original terminal/confidence/rationale and private source setup removed from model-facing payloads. EB06_D2 remains partial and excluded from terminal replay; its observed answers stay in interaction coding. No new blind/informed replay, API call or missing-game continuation. Fixing a cohort does not freeze a new prompt, sampling endpoint or establish active-versus-passive effects.

Unchanged: original raw evidence, recoveries, cutoffs, model labels and earlier endpoint claims. Arena studies are not pooled with this API corpus. No causal presentation/instruction effect, population calibration, stable ToM failure or model ranking is established.

Reproduce from a fresh checkout with Python standard library: `python -X utf8 -B scripts/audit_offline_coding.py`. It verifies frozen and evidence hashes, annotation coverage/quotation spans and replay payload shape without credentials or provider calls. Independent staged-checkout audit passed. Preparation scripts refuse to overwrite their existing frozen outputs.

Reviewer questions: do the selected annotations distinguish internal consistency, source fidelity and target designation? Are unsupported rationale inferences separated from actual dialogue misreadings? Is the seven-complete cohort selected only on completeness, with partial evidence retained and correlated material families acknowledged? Which observations warrant a subsequent controlled test, rather than a claim from this retrospective corpus?

# Previous incremental review: surface-diverse Frozen cutoff snapshot

Review base: `a5e0ae4b3bdfae90b3a70e97b677570cb2604d9e`.
Evidence head: `fae8bb8f2f5f7801de8706e19bde659b34289601`.
This handoff is metadata-only; evidence head stays fixed.

Read [results](epistemic_boundary_mimicry/SURFACE_DIVERSE_FROZEN_RESULTS.md), [protocol](epistemic_boundary_mimicry/SURFACE_DIVERSE_FROZEN_PROTOCOL.md), then [public evidence](epistemic_boundary_mimicry/published_runs/go_surface_diverse_cutoff_20261005/README.md). Two new fixed material families × reciprocal Qwen/GLM directions. Three STOP endpoints after 6/2/4 ASK; fourth lacks terminal, with B's sixth answer undispatched at the operational USD 1.90 pre-request limit (actual estimated 1.906307). Not four completed trials. Pre-dispatch compatibility correction involved zero calls and an identical bundle.

Public audit: `python -X utf8 -B scripts/publish_surface_diverse_frozen.py`, no provider calls. Verifies file/source hashes, seat/target seed replay, equal Reader policy, source isolation, exact relays, terminals and missing next request. All earlier Frozen abstentions and original cutoff remain unchanged. Target matches are random-label matches, not authenticity accuracy. Source domains, narrative framing and details changed alongside wording; no causal surface effect is identified. Sequential usage cutoff can bias the completed subset.

Reviewer questions: how does public-context alignment become an unsupported target cue? Does paraphrase framing measure document provenance rather than target designation? EB06's actual source opens with the caution the Judge treated as a late patch; distinguish source fidelity from rhetorical inconsistency. No systematic source-relative coding or perturbation mechanism is claimed. No continuation launched for publication.

# Previous incremental review: two completed Frozen controls

Review base: `876aa4b7478f9b4899e59ca17e5385aab828cf17`.
Evidence head: `7c71ac859dd2a7b9f298dee01f12cbe095a86f70`.
This handoff is metadata-only; the evidence head stays fixed.

Read [aggregate results](epistemic_boundary_mimicry/FROZEN_PAIR_RESULTS.md), [ecological recovery amendment](epistemic_boundary_mimicry/FRESH_FROZEN_RESUME_PROTOCOL.md), [archaeology protocol](ARCHAEOLOGY_FROZEN_PROTOCOL.md), then [visible evidence](epistemic_boundary_mimicry/published_runs/go_frozen_pair_completed_20261004/README.md). EB03 now has a separate four-ASK ABSTAIN endpoint after repairing exactly one missing quote without regenerating any inherited response. The original incomplete cutoff remains unchanged. EB04 is a fresh three-ASK ABSTAIN endpoint without repair. Both use Qwen Readers → GLM Judge.

Reproduce with `python -X utf8 -B scripts/publish_boundary_frozen_pair.py`: public-only hashes, equal Reader policies, source isolation, target assignment, exact routing, one-character repair and inheritance against original cutoff. No provider calls. Sources and seats frozen before independent target draw; Judge not told the mechanism. Shared procedural wording is a potential abstention cue. No independent-author robustness, population effect, model ranking or authenticity inference is established. Earlier endpoints unchanged; source-relative annotation pending.

Reviewer questions: does the repaired fourth question retain exact text and histories? Does shared prose explain recognition of parallel sources? Do the reasons distinguish target-identifying evidence from internally consistent detail? Treat these as two exploratory trajectories, not confirmation of a general mechanism.

# Previous incremental review: fresh ecological Frozen cutoff

Review base: `b1b34e41a6c8925b6180fd867835c053123a332b`.
Evidence head: `f25583f6368d0c563b8a4a0ec3e20b379d2d917e`.
This handoff is metadata-only; the evidence head stays fixed.

Read [cutoff result](epistemic_boundary_mimicry/FRESH_FROZEN_RESULTS.md), [protocol](epistemic_boundary_mimicry/FRESH_FROZEN_PROTOCOL.md), then [public trajectory](epistemic_boundary_mimicry/published_runs/go_fresh_frozen_cutoff_20261004/README.md). EB03 has two fresh 320-word fictional ecological notes, sources and seats frozen before independent target draw. Qwen readers / GLM Judge: three complete ASK rounds, then malformed visible Judge JSON intended for the next question. HTTP 200/stop; no max-token signal, quota error, terminal decision or inferred abstention. Nine valid replies and the tenth invalid raw text are preserved; invalid query never relayed.

Reproduce with `python -X utf8 -B scripts/publish_boundary_fresh_frozen.py`: file/source hashes, identical reader policies, source isolation, exact routing and reproducible parse failure. No private records or provider calls required. Judge is not told this is a random-label control. Prior seven completed endpoints unchanged. This incomplete attempt cannot support a termination-behavior conclusion or be counted as a wrong pick. Reviewer questions: is the protocol failure faithfully preserved without reconstruction? Do source and seat provenance exclude target cues? Keep unknown generation mechanism distinct from knowingly ignoring an explicit null.

# Previous incremental review: second-case three endpoints

Review base: `5d47a93c6a9b283059d94b6e6feada72eb2fb09d`.
Evidence head: `01044ac5b400510264cd7eeb8d851c02cedac3ce`.
This handoff is metadata-only; the evidence head stays fixed.

Read [second-case results](epistemic_boundary_mimicry/CASE02_RESULTS.md), [protocol](epistemic_boundary_mimicry/CASE02_API_PROTOCOL.md), then [three public records](epistemic_boundary_mimicry/published_runs/go_case02_three_20261004/README.md). EB02 is the frozen storm boarding-slip background. Qwen speakers / GLM Judge: Strong 3 ASK correct A .70; Boundary-aware 3 ASK correct A .95; Frozen 9 ASK pick A .70, matching only the arbitrary target. Reverse remains unstarted. Strong reuses ten original physical requests, including quota 429, and one authorized identical-history Judge continuation gives its terminal.

Public-only reproduction: `python -X utf8 -B scripts/publish_boundary_case2.py`. Exact visible prompts/replies, both used sources, 429 and inheritance hashes are included; reasoning, private sessions/accounts and credentials are excluded. First-case four endpoints remain unchanged. Two independent dossier backgrounds, seven endpoint configurations, unbalanced arms and mixed recovery histories prevent causal effects, population accuracy, rankings or a confirmatory-study claim. Source-boundary coding remains pending.

Reviewer questions: does the Boundary-aware bluffer actually absorb nonexistent details from leading queries? Is the Judge's claim that source readers cannot do this too strong? Does Frozen's editorial-derivation argument supply target-linked information or only unsupported stylistic preference? Does Strong's boundedness rationale correspond to the source? The results preserve these as behavioral observations and stated rationales, not established mechanisms.

# Previous incremental review: reverse Boundary-aware endpoint

Review base: `502b96e25fe3ea55a15f16eef6784309677ce469`.
Evidence head: `1731be7377eea316a39eb10b665c9f1d7081b568`.
This handoff is metadata-only; the evidence head stays fixed.

Read [reverse result](epistemic_boundary_mimicry/REVERSE_RECOVERY_RESULTS.md), [four-slot coverage](epistemic_boundary_mimicry/RESULTS.md), then [public dialogue](epistemic_boundary_mimicry/published_runs/go_reverse_recovery_20261004/README.md). GLM speakers / Qwen Judge: two ASK, wrong pick A at .78; B read the target source. Seven new calls, no inherited answers. Original empty visible READY retained; revised fresh sessions start Judge first and combine each Speaker's private initialization with its first requested question. No reasoning is promoted to visible evidence.

Reproduce with `python -X utf8 -B scripts/publish_boundary_reverse.py`: source/file hashes, exact amended routing, returned model labels, no READY, ASK count and gold. Export is an allowlisted projection; hidden reasoning, private session/account data and credentials are omitted. All four selected slots have endpoints under mixed original/recovery protocols on one dossier; prior three endpoints and public snapshots are unchanged. No causal condition effect, ranking, stable ToM or controlled Arena comparison. Source-boundary coding remains pending. Reviewer questions: did public-context wording misleadingly imply identifiers that the real dossier omits? Are the Judge's specificity-based claims supported by the original source? Which claims survive the Judge-first protocol difference?

# Previous incremental review: Frozen negative-control recovery

Review base: `cb654352fdd57d1736b1c115fd54ab8b34591603`.
Evidence head: `cdc65bc64b429343aa492a2846044fe638f00807`.
This handoff is metadata-only; the evidence head stays fixed.

Read [Frozen result](epistemic_boundary_mimicry/FROZEN_RECOVERY_RESULTS.md), [recovery amendment](epistemic_boundary_mimicry/API_RECOVERY_PROTOCOL.md), then [public evidence](epistemic_boundary_mimicry/published_runs/go_frozen_recovery_20261004/README.md). Qwen readers / GLM Judge, four ASK then ABSTAIN. Eight original messages are inherited, including the complete B answer that failed strict parsing; seven new calls add two ASK and the terminal. Literal JSON controls are decoded deterministically with raw text unchanged; no inherited answer is regenerated.

Both sources and exact visible dialogue are published; private reasoning and account/session/credential fields are omitted. Public audit: `python -X utf8 -B scripts/publish_boundary_frozen.py` checks hashes, inheritance, routing and terminal. Prior Strong/Boundary-aware two-endpoint snapshot is unchanged; no reverse result is added. One arbitrary-target identifiability control supports a descriptive expected abstention, not statistical chance accuracy, model ranking or a causal comparison. Source-relative boundary coding remains pending. Reviewer questions: does the public context supply any target-linked anchor? Does the Judge's unsupported claim about independent invention affect its abstention rationale? Are differing source facts treated symmetrically?

# Previous incremental review: Boundary Mimicry API qualification

Review base: `23ce2e4d1a38e27bcf8e126dc2d0553e3b8bf52d`.
Evidence head: `d5c93be40ad74aae24c34b810fda28f978297463`.
This subsequent handoff is metadata-only; the evidence head stays fixed.

Read [results](epistemic_boundary_mimicry/RESULTS.md), [API protocol](epistemic_boundary_mimicry/API_PROTOCOL.md), then [two public endpoints](epistemic_boundary_mimicry/published_runs/go_two_completed_20261004/README.md). Strong: three ASK, wrong pick B, .80; Boundary-aware: eight ASK, correct pick A, .70. Both use Qwen3.8 Max speakers / GLM-5.3 Judge and the same fictional source. Four slots attempted, two endpoint failures excluded: unescaped control characters in Frozen visible JSON and no visible GLM setup reply in the reverse slot. No repair results are included in this snapshot.

Exact visible prompts/replies, the used source and Host labels are published through an allowlist; hidden reasoning, account/session identifiers and credentials are omitted. Reproduce hashes, relays and scoring with `python -X utf8 -B scripts/analyze_boundary_go_snapshot.py`. The acquisition runner needs an ignored private bundle; it is not the public reproduction entry point. Prior studies and frozen cutoffs are unchanged.

Claim limits: one independent dossier, no repetition, no passive baseline, unbalanced arms, provider/model/protocol changes relative to Arena. No causal condition effect, stable ToM, model ranking or cross-platform comparison. Boundary scoring remains pending. Review questions: does the Strong Judge's stated contradiction withstand source/transcript review? Which specificity and omission cues actually distinguish the two accounts? Does eight-ASK success supply new evidence beyond earlier answers?

# Previous incremental review: remaining slots completed, question limit amended

Review base: `0c25bd34d4250f1a347117f5e76729f5476f4383`.
Evidence head: `1a1b432d78f5b85c004389da95c87c718ef9f476`.
This subsequent handoff is metadata-only; the evidence head stays fixed.

Read [completed aggregate](strategic_bluff_pilot/COMPLETED_RESULTS.md), [completion and cap amendment](strategic_bluff_pilot/COMPLETION04_PROTOCOL.md), then [aggregate JSON](strategic_bluff_pilot/completion_analysis.json). [Eight endpoint receipts](strategic_bluff_pilot/published_runs/eight_completed_20261004/README.md) are secondary evidence. The prior six-endpoint snapshot is unchanged.

New evidence is only the two previously missing slots. S02_D2_strong reuses complete original A/B openings in their original sessions with a fresh Claude Judge; after six ASK actions, the user removes the ten-ASK cap and the Judge receives that amendment. It stops after seven ASK actions, pick B, confidence .78, correct. S02_D1_natural starts fresh A/B/J, with an uncapped initial Gemini Judge, and stops from the openings alone: zero ASK, pick A, confidence .99, correct. One blank-response UI retry preserves the exact prompt; anonymous comparisons are skipped and only fixed-model final visible outputs are recorded. User handles security verification. There is no pending request or monitor.

Completion is now eight configured slots, natural 4/4 correct and strong 4/4 correct, across two independent source backgrounds. All 23 original and recovery attempt records remain distinguishable: 121 physical submissions, 95 distinct complete replies, six retained partial outputs; inherited openings counted once. Public-only reproduction (`python -X utf8 -B scripts/analyze_strategic_snapshot.py --completed`) checks manifest/source hashes, exact role prompts and relays, first-completed selection and scoring with zero audit errors. A no-provider regression check confirms that the old branch rejects an eleventh ASK while the uncapped branch accepts it.

Changed claim: no remaining missing endpoint for these eight configured slots. Unchanged boundaries: failure-selected recovery is not an unbiased sample; source backgrounds are shared; correct picks do not validate reasons; no instruction-component or post-training mechanism, model ranking, robust ToM or interrogation-gain conclusion. The protocol is now mixed: six capped endpoints and two amended completions. The final natural endpoint contains no interrogation, so it cannot be evidence of interrogation benefit. No model calls for publication; older studies and frozen cutoffs remain unchanged.

Reviewer questions: does strong's repeated elaboration actually maintain consistency across the seven ASK actions? Does the Judge's source-boundary rationale match the source evidence? How much does the zero-ASK natural outcome rely on opening specificity? Do not compare the cap amendment causally with the capped runs.

# Previous incremental review: natural versus strong strategic bluff

Review base: `4fecfe4b919b442f1eb1c8baf0fbee6bbff6f4ce`.
Evidence head: `526ab5d32d2b93e339d8303e27f67bd91035aed3`.
This handoff is metadata-only; the evidence head stays fixed.

Read [six-endpoint results](strategic_bluff_pilot/SNAPSHOT_RESULTS.md), [protocol](strategic_bluff_pilot/PROTOCOL.md), [retry amendments](strategic_bluff_pilot/RETRY_PROTOCOL.md), then [aggregate JSON](strategic_bluff_pilot/snapshot_analysis.json). Open [individual receipts](strategic_bluff_pilot/published_runs/six_completed_20261004/README.md) only to challenge a particular claim. They contain source and gold labels; never forward them wholesale to tested roles.

New evidence: two new fictional dossiers, reciprocal Claude Sonnet 5 High / Gemini 3.1 Pro Preview arms, matched natural/strong Bluffer instruction packages with unchanged Knower and Judge instructions. Six of eight slots have first-completed endpoints, natural 3/3 and strong 3/3 correct; ASK counts are 1, 1, 2, 4, 1, 4 in snapshot filename order. Two missing terminal decisions remain unscored. The 21-record attempt ledger retains all original and authorized retry/recovery statuses, counting inherited openings once: 99 physical submissions, 74 distinct complete replies, six retained partial outputs. Public receipt hashes, source isolation, exact question/answer relays and scoring reproduce without private local runs, with zero audit errors. Original cutoffs are unchanged.

Claim boundary: only two independent backgrounds; failure-selected recovery completion does not estimate a population effect. The intervention combines win framing, explicit fabrication permission and strategic uncertainty handling. Natural Bluffers also fabricate; correct Judge picks can rely on unsupported packet-number assumptions. No component effect, post-training mechanism, model ranking, robust adversarial ToM or interaction gain is established. The own-partial-response retry affects incomplete S02_D1_natural, not the six exported endpoints. Direct menu labels are observed; backend identity and sampling settings are unverified. No model calls were made during publication. Prior Naturalistic Study 1 and v0.1–v0.4 evidence and claims remain unchanged.

Reviewer questions: do the source-boundary cues actually support each decision rationale? Does the strong instruction package change observed bluff behavior in the two complete S01 pairs? Which behavioral comparisons survive failure-based selection and shared-source dependence? Keep these exploratory; do not infer the missing endpoints. Reproduce with `python -X utf8 -B scripts/analyze_strategic_snapshot.py` from repository root.

# Previous incremental review: Naturalistic Study 1 — nine completed configurations

Review base: `34d8563e161ed2700985599693ba48f04ac19654`.
Evidence head: `69300849e94b559963c9ec39371a44917e4cd04d`.
This subsequent handoff is metadata-only; the evidence head stays fixed.

Minimal reading order: [snapshot results](naturalistic_study_1/SNAPSHOT_RESULTS.md), [protocol](naturalistic_study_1/PROTOCOL.md), [collection scope](naturalistic_study_1/COLLECTION_SCOPE.md), then [snapshot_analysis.json](naturalistic_study_1/snapshot_analysis.json). [Individual public receipts](naturalistic_study_1/published_runs/nine_completed_20261003/README.md) are secondary: open a specific trajectory to challenge a claim. They contain source dossiers and access labels; do not forward them wholesale to a tested role.

New experiment: two isolated same-model speakers, one receiving a fresh fictional dossier and one only the shared familiar-world context, with a different-model judge freely interrogating A, B or both. Host relays exact answers without truth checks. Judge chooses when to stop or abstain, capped at ten ASK actions. Observed Direct labels are Claude `claude-sonnet-5-high`, GPT `gpt-5.5-instant` and Gemini `gemini-3.8-flash-high`; deployment identity and sampling settings remain unverified.

Coverage: 9 unique completed planned configurations across 5 dossiers. Original cutoff N01_D1, seven serial-continuation completions, and one explicitly authorized N02_D1 fresh-judge recovery on identical inherited openings are counted once each. The failed N02 judge attempt stays separate. All nine picks match initial access; ASK counts in configuration order are 2,6,1,5,1,1,5,1,2. Confidence is an uncalibrated self-report. BOTH counts once even with multiple subquestions. Reciprocal configurations share dossiers, so the independent background count is five, not nine.

The original plan had 24 configurations. The user reduced collection to 12 completed configurations before this publication; three more remain. N04_D1 and N06_D1 are platform-missing, N06_D2 is partial at a human security challenge. The original rate-limit cutoff, serial continuation and specific N02 recovery have separate attempt records in the public compact coverage ledger. There is no background monitor and no model call for publication. Only sources N01–N05 are published; remaining fresh sources stay private.

Claim boundary: 9/9 is a completed-subset descriptive result, not a population accuracy or reliably maintained-bluff detection estimate. Some bluff replies openly limit available detail and hedge. N03_D1's judge overstates such a limitation as an explicit access admission; the actual speaker does not literally state it was denied source access. N01_D2 and N04_D2 contain judge questions with source-unsupported premises; the informed speaker identifies the gaps. N05_D2's judge claims source agreement despite never seeing the dossier. Judge rationales are data, not verified explanations of valid cues.

Post-hoc candidates include source-bounded uncertainty, concrete-detail probing and N02's measuring-versus-musical-instrument interpretation error. No stable taxonomy is established. There is no passive, human, matched-token, self-model or matched actor–observer control; interrogation improvement, family ranking and ToM dissociations remain untested. v0.1–v0.4 evidence and conclusions are unchanged, and H2 remains paused.

Code route: `scripts/naturalistic_arena_operator.mjs` constructs isolated prompts and records UI sends/captures; `scripts/export_naturalistic_snapshot.py` publishes an allowlisted fixed snapshot with unchanged prompt/final visible reply strings; `scripts/analyze_naturalistic_snapshot.py` checks public hashes, source isolation, exact opening/follow-up relay, ASK counts and terminal scoring. Public evidence excludes account/UI DOM, private session URLs, tab IDs, reasoning panels and anonymous candidate text. Original session reuse was checked locally; excluded links cannot be independently rechecked from the public slice. Visible Markdown-rendered reply capture is not asserted to match generation-stream bytes.

Reproduce from the repository root: `python -X utf8 -B scripts/analyze_naturalistic_snapshot.py`. Python standard library only. Public-only reproduction matched the canonical summary with zero audit errors; Node syntax, staged whitespace, privacy, evidence hashes and Markdown links passed. Other preparation/local-analysis scripts require excluded full local inputs and are not the public-snapshot reproduction route.

Reviewer questions: How much do detail/availability cues simplify the task? Does a boundary-probing question induce the very fabrication later used as evidence? Can a later controlled comparison distinguish interrogation policy from opening-detail asymmetry and token budget? Which post-hoc pattern actually repeats across independent dossiers? Do missingness, explicit recovery and dependence between reciprocal directions stay visible?

## Previous incremental review: v0.4 Active Verification

Review base: `ffb335bc8bc5a5b5d88c53f7bd22630cb18e32eb`.
Evidence head: `1497eb14a96b6b70c68ea7e94adb5641e6866bd8`.
This subsequent handoff is metadata-only; the evidence head stays fixed.

Read [v0.4 results](v0_4_active/RESULTS.md), then [protocol](v0_4_active/PROTOCOL.md), then [analysis.json](v0_4_active/analysis.json). [Public evidence](v0_4_active/published_runs/arena_20261003_active01/README.md) is secondary: open individual receipts only to challenge a specific metric. It contains role cards and Host truth; do not forward the full directory to a tested judge.

New experiment: six fresh binary fixtures; isolated GLM-5.2 (max) speakers generate once and freeze accounts plus eight predictions; three independent Gemini-3.8-Flash-high judges per case receive only accounts initially. VERIFY reveals the selected frozen predictions and deterministic Host truth, then the judge can verify again, stop or abstain. This is live revelation of frozen answers, not strategic speaker adaptation. Arena Direct labels were observed; backend and sampling settings remain unverified.

Coverage: 12 speaker sends, 10 replies, four usable pairs. Twelve judge conversations started out of 18 planned; 26 judge sends produced 20 replies and 14 verifications. Six trajectories reached terminal decisions, six failed on the platform, six could not start because a speaker was missing. No resends or replacements; no new model calls for publication.

Observed metrics: diagnostic first queries 7/7 across three backgrounds; evidence-consistent updates 10/10, with four missing next updates; completed identifiable decisions 3/3 across only two backgrounds; equivalent-control abstention 3/3 on one background, zero queries. Completed identifiable costs were 2,3,2 against the oracle prediction-table lower bound of one. The actual judge must infer candidate consequences from accounts, so extra verification is a cost difference, not proof of irrational stopping. Negative controls publish the permitted-mode rule and are deliberately easy. No stable failure, population accuracy, ToM, causal or model-ranking claim follows from this partial screen.

H2 is paused; v0.1–v0.3 frozen evidence and conclusions are unchanged. Source map: `v0_4_active/core.cjs` builds prompts, parses replies, computes `diagnostic`/`observation` and audits trajectories; `scripts/prepare_active_verification.py` freezes the bundle and refuses overwrite; `scripts/analyze_active_verification.py` recomputes summaries, falling back to public evidence; `scripts/export_active_run.py` projects an allowlist while preserving exact submitted prompts and final JSON replies. Account/UI data, reasoning panels, sessions, screenshots and anonymous candidate text are excluded. The bundle is stored without newline conversion to preserve its original byte hash.

Reproduce from repository root with Python and Node.js on PATH: `python -X utf8 -B scripts/analyze_active_verification.py`. Public-only reproduction and exact receipt/Host audits passed; publication privacy, manifest hashes and Markdown links passed.

Reviewer questions: Are missing terminal decisions excluded transparently rather than scored as errors? Is the oracle information advantage explicit? Are the simple control and shared-speaker replicates kept separate from broader knowledge-access claims? Does the small observed near-ceiling result justify a separately designed harder task rather than claiming a reasoning failure here?

## Prior incremental review: H2 qualification and neutral retry

Review base: `c1423db801814b0d5da663bd9676ab0ad3bee347`.
Evidence head: `9a5783a64a4402af507f4a0974af080a97506fff`.
This handoff update is metadata-only; the evidence head remains fixed.

Start with [amended comparison](v0_3_h2/RETRY_RESULTS.md), then [original cutoff report](v0_3_h2/RESULTS.md), [frozen protocol](v0_3_h2/PROTOCOL.md) and [explicit retry amendment](v0_3_h2/RETRY_PROTOCOL.md). Open [retry_analysis.json](v0_3_h2/retry_analysis.json) for the small canonical result; exact prompts and public receipts are secondary evidence.

New work reuses the L01V1 transcript verbatim. Neutral is the exact historical N prompt; salient only reorders existing notation/fixed-input sentences before the inventory and changes paragraph breaks. No words or outcome evidence were added. The original A boundary-description error is unchanged. Frozen hashes and the public-word/non-public-content audits are in [bundle.json](v0_3_h2/bundle.json).

The initial two sends captured salient p(A)=0.10; neutral timed out at cutoff. The user then explicitly authorized one fresh neutral rerun, which returned p(A)=0.50 and insufficient evidence. The amended difference is -0.40, but the historical neutral p(A)=0.10 was not roughly reproduced. Frozen verdict: `HISTORICAL_PATTERN_NOT_ROUGHLY_REPRODUCED`. Original cutoff evidence is separate and unchanged. There were three sends, two captured replies, no additional variants or quality-based selection.

No presentation causal effect, task-designer mechanism, H1 result or population inference follows. Sampling/deployment variability and different send times remain unresolved. v0.1/v0.2 evidence and conclusions are unchanged; no new model calls were made for publication.

Code route: `scripts/prepare_h2_probe.cjs` freezes prompts and refuses overwrite; `scripts/analyze_h2_probe.py` audits receipts and implements frozen qualification thresholds; `scripts/export_h2_runs.py` preserves research strings with allowlists; `scripts/verify_publication.py` checks staged privacy, links and manifest hashes. From repository root, with Python and Node.js available, run `python -X utf8 -B scripts/analyze_h2_probe.py` and `python -X utf8 -B scripts/analyze_h2_probe.py --neutral-retry`. Both reports were reproduced using published evidence only. The original prompt freeze remains unchanged; do not rerun its preparation script to overwrite it.

Reviewer questions: Does the amended report keep original failure and authorized retry distinct? Does it resist interpreting the observed difference as an identified salience effect? Does the future design need repetitions and an error-free transcript before a mechanism claim?

## Prior handoff: grounded-card pilots (background only)

Review base: `5e834c2d1bab02e958c821687970dfd765ffa195` (published v0.1 pilot).
Evidence head: `c0f2d891ced947fc040f75af5514a2acadb0d8d2`.
This handoff is a later metadata-only commit; the evidence head stays fixed.

## Minimal reading order

1. [Other-domain results](v0_2_other/RESULTS.md), then [interpretation](v0_2_other/INTERPRETATION.md).
2. [Math results](v0_2_math/RESULTS.md).
3. [Other-domain protocol](v0_2_other/PROTOCOL.md) and [math protocol](v0_2_math/PROTOCOL.md) for frozen design and operational deviations.
4. Inspect the small `analysis.json` and `bundle.json` in each domain directory as needed. Open published logs only to challenge a specific claim; they contain host truth and private prompts and must not be forwarded wholesale to game roles.

## New evidence and unchanged claims

The user-authorized follow-ups add five planned background pairs (ten versions) with domain-grounded public contexts and two alternative private cards per background. Mathematical card checks were verified by exhaustive cycle enumeration on the selected test graphs. Math has 19/28 game replies plus one prior; other domains have 46/112 plus four priors. Four individual versions completed, but no full two-version background pair completed. Missing steps are platform failures, not incorrect model answers.

Language L01V1: interaction P0–P3 stayed at 50% for informed A; fresh N assigned A 10% and selected B; fresh E assigned A 99%. B maintained a coherent alternative rule; A had one boundary-description wording error despite correct transformations.

Ecology E01V2: both initial commitment sets matched truth (collision). N/E assigned informed B 80%/85%, mostly citing details and wording; independent checks did not distinguish the speakers. Anthropology T01V1 assigned informed A 96% at P3, 95% at N and 99% at E. These are descriptive cases, not estimates of population accuracy or causal effects.

v0.1 frozen code, evidence and reported conclusions are unchanged. No general ToM, real-world deception detection, domain ranking, grounding causal effect or active-questioning causal effect is established. The original proposal texts are archived separately under `docs/v0_2_proposal/`; they are not the executed protocol.

## Source and reproduction map

- `scripts/prepare_selvar_pilot.py` / `prepare_other_pilots.py`: deterministic bundle generation, refusing overwrite.
- `v0_2_math/console.js` / `v0_2_other/console.js`: `stepsFor`, `buildPrompt`, `diagnostic` and parsers define role routing and initial-commitment scoring.
- `scripts/check_selvar_cards.py`: selected graph sanity check.
- `scripts/analyze_selvar.py` / `analyze_other_pilots.py`: exact prompt/capture audits and descriptive summaries; automatically use published evidence if local raw runs are absent.
- `scripts/render_other_results.py`: Markdown table from canonical JSON.
- `scripts/export_v02_runs.py`: unchanged prompt/reply exports with field allowlists, omitting UI DOM, anonymous candidates, accounts and private sessions.
- `scripts/verify_publication.py`: staged content/links/privacy checks and public prompt/reply hashes.

From repository root, with Python 3.10+ and Node.js on PATH:

```powershell
python -X utf8 -B scripts/check_selvar_cards.py
python -X utf8 -B scripts/analyze_selvar.py
python -X utf8 -B scripts/analyze_other_pilots.py
python -X utf8 -B scripts/render_other_results.py
```

Both published-only audits reproduced canonical summaries. No new model requests were made for publication. Backend deployment, temperature and tool availability remain unverified; fixed Direct UI labels were observed. Platform comparisons were skipped; only restored fixed-label replies were forwarded. Same-conversation no-output recovery deviations are explicitly retained in the other-domain protocol and logs.

## Reviewer questions

1. Do the claims clearly distinguish card access from lucky correct commitments and plausible procedural details?
2. Does the language N error support only a case-level observation, with A's wording error and B's internal consistency preserved?
3. Does ecology's collision invalidate using E as a distinguishing positive control here?
4. Are partial pairs, adaptive judge questions and platform interventions sufficiently separated from any causal or independent-sample interpretation?
