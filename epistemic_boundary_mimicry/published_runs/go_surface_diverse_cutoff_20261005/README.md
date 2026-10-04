# Four-slot surface-diverse Frozen snapshot

Start with [results](../../SURFACE_DIVERSE_FROZEN_RESULTS.md), then [protocol](../../SURFACE_DIVERSE_FROZEN_PROTOCOL.md). Three completed selections and one incomplete usage-cutoff trajectory.

- `bundle.json`: actual public context, four supplied source texts, role prompts, fixed sampling and target seeds.
- `randomization.json`: frozen seat assignments and seeds.
- `EB05_D1_symmetric_frozen.json`, `EB05_D2_symmetric_frozen.json`, `EB06_D1_symmetric_frozen.json`: three complete visible trajectories and terminal rationale.
- `EB06_D2_symmetric_frozen.json`: 17 captured visible replies, six ASK actions, no terminal; B's sixth answer remains undispatched.
- `summary.json`: actual batch usage cutoff and zero-call pre-dispatch compatibility correction.
- `manifest.json`: normalized LF UTF-8 hashes for snapshot JSON files.

This is an allowlisted exact visible-text projection. Private reasoning, native assistant blocks, credentials, account/session data and machine paths are omitted. Sources are disclosed as used pilot materials, not reusable fresh confirmatory questions. Do not interpret arbitrary target matches as source-authenticity scores.

Public-only audit from repository root: `python -X utf8 -B scripts/publish_surface_diverse_frozen.py`. No model calls or private data required.
