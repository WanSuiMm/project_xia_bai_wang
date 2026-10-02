# Incremental review: grounded-card pilots

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
