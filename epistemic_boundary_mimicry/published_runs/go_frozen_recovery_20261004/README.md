# Frozen control: four ASK, then ABSTAIN

Read [result](../../FROZEN_RECOVERY_RESULTS.md), then [recovery protocol](../../API_RECOVERY_PROTOCOL.md).
The trajectory contains 15 visible messages: eight inherited original messages
and seven new calls. Exact raw text is preserved, including the original invalid
JSON string newlines. Only the decoding rule changes; the B answer is not regenerated.

`bundle.json` contains the two used sources, Host labels, initial role prompts,
original failure and hashes of inherited message text. `manifest.json` binds
the public files. Sources and target labels are Host evidence; never send this
whole snapshot to a tested role. Hidden reasoning, accounts, session identifiers,
provider response IDs and credentials are excluded.

Public-only reproduction, without API calls or local private runs:

```powershell
python -X utf8 -B scripts/publish_boundary_frozen.py
```
