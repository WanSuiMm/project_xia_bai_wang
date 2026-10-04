# Fresh Frozen cutoff, no endpoint

Start with [result/status](../../FRESH_FROZEN_RESULTS.md) and [protocol](../../FRESH_FROZEN_PROTOCOL.md).
Three completed ASK rounds, then one malformed next-question Judge reply.
The trajectory preserves all ten physical replies, nine valid and one invalid;
the last is never relayed. `bundle.json` includes both sources, Host designation
and generation/seat/target seeds. Do not forward this Host evidence to tested roles.
Hidden reasoning, account/session identifiers, credentials and machine paths are omitted.

Public-only verification, no API calls:

```powershell
python -X utf8 -B scripts/publish_boundary_fresh_frozen.py
```
