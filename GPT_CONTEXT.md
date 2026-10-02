# Review context

Current status: `partial_completion_platform_block`; formal completed clean cases P01/P02/P04, contaminated incomplete case P03. Frozen protocol v0.1.0; synthetic deterministic 3-bit cards, exactly four of eight outcomes PASS. Twenty formal cards and two practice cards prepared; only the first four formal cards attempted. Publication does not claim all 20 ran.

Each case has two independent same-model speaker chats, exactly one receiving the full private card, and a second model as judge. P0 precedes three jointly phrased questions sent separately to speakers; P1/P2/P3 are the same judge's updates. Fresh N/E judges receive the same dialogue with no previous verdicts. Only E receives three outcomes fixed before the opening commitments. Seat access is the target, not internal knowledge or moral deception.

Read `RESULTS.md`, then the published run README, then `docs/01_SPEC.md` and `docs/04_IDENTIFIABILITY.md`. Do not read all raw JSON first. All paths below are relative to `xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/`:

| Concept | Source symbol / evidence |
|---|---|
| Frozen cases, roles, reference outcomes | `data/HOST_ONLY/cases.json`; per-case `case_sha256` |
| Prompt construction, isolation and order | `tools/console.js`: `buildPrompt`, `stepsFor`, `dialogue`, `parseObject` |
| Offline host UI | `START_HERE.html`, `tools/build_console.py` |
| Reproduce frozen pack | `tools/regenerate_data.py`, `tools/build_frozen_bundle.py` (use a new empty output directory) |
| Scoring, contamination, uncertainty | `tools/analyze.py`: `HARD_FLAGS`, `load_records`, `summarize`, `render_report` |
| Live capture auxiliary code | `published_runs/arena_20261002_direct_pilot01/operator_capture.py` (loopback only; does not contact Arena) |
| Capture audit | Same run's `audit_capture.py` and `capture_audit.json` |
| Actual prompts and JSON replies | Same run's `logs/*.json`: `sent_prompts`, `raw` |
| Full rendered replies and anonymous candidates | `rendered_full_by_step`, `rendered_sessions`, `platform_observations`, `capture_errors` |
| Synthetic tests, not model experiments | `tests/test_pilot.py`, `tests/test_console.js` |

Actual UI model labels were fixed to Claude Sonnet 5.5 high and Gemini 3.8 Flash high. Temperature, hidden tool configuration and backend model identity are unverified. Arena sometimes inserts anonymous comparisons even in Direct mode. P02 skipped such candidates and captured the restored labeled response; P03 accidentally passed a candidate to P2 and is explicitly excluded. Public release strips private conversation URLs, screenshots and machine identifiers while hash-verifying prompt/reply strings unchanged.

Review questions: Are clean-case N/E claims limited to the evidence? Is uncertainty reasonable without verified outcomes? Does P03 remain excluded under `unexpected_model_change`? Do actual prompt receipts match the frozen protocol? Do code and documentation distinguish synthetic fixtures, practice, complete experiments and missing stages?
