# Latest incremental review: H2 qualification and neutral retry

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
