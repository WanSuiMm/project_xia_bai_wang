# Second-case three-endpoint snapshot

Read [results](../../CASE02_RESULTS.md), then [protocol](../../CASE02_API_PROTOCOL.md).
Boundary-aware: 3 ASK, correct .95. Strong: 3 ASK, correct .70. Frozen: 9 ASK,
pick A .70, matching only the arbitrary Host designation. The reverse slot has
no endpoint and is not inferred. Open individual trajectories only to challenge
a specific claim.

Exact visible text, used sources and gold labels are included; never send the
whole Host snapshot to a tested role. Strong retains its failed 429 physical
request (`reply=false`) and the later identical-prompt continuation. Native
thinking, provider response IDs, account/session data and credentials are omitted.
`manifest.json` binds file contents; the bundle hashes inherited Strong messages.

Public-only verification with no model calls or private local runs:

```powershell
python -X utf8 -B scripts/publish_boundary_case2.py
```
