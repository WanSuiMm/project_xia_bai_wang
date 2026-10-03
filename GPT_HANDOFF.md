# Latest incremental review: natural versus strong strategic bluff

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
