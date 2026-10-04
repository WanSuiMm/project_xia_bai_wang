# Reverse Boundary-aware endpoint

Read [result](../../REVERSE_RECOVERY_RESULTS.md), then [recovery protocol](../../API_RECOVERY_PROTOCOL.md).
`EB01_D2_boundary_aware.json` preserves exact visible prompts and replies: GLM
speakers / Qwen Judge, two ASK, pick A at .78, target B, wrong. `bundle.json`
contains only the used source, Host gold, role instructions and original empty
visible setup failure. No thinking, account/session IDs or credentials are included.
Do not send this Host evidence wholesale to tested roles.

Public-only verification, no private runs or API calls:

```powershell
python -X utf8 -B scripts/publish_boundary_reverse.py
```
