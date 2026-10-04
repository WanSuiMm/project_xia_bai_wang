# Two failure-selected API recoveries

Original four-slot attempts and the two public endpoints are frozen unchanged.
The user requested repair of Frozen and reverse Boundary-aware only.

Frozen: its original B answer is complete but contains literal newlines inside
the JSON string. Use `json.loads(strict=False)` to decode controls without
changing the text or answer; retain the original failure and a parser amendment
event. Inherit all original role histories, raw assistant blocks and requested
answers. Continue from the next Judge action, without regenerating B.

Reverse Boundary-aware: original GLM setup had null visible content and the
READY marker only in reasoning. Do not promote reasoning to visible output.
Start fresh independent histories with Judge's public-only first ASK, then
combine each Speaker's original private role/source instructions with its
first requested question. Replace the separate READY request with an instruction
to answer immediately in visible JSON. Later routing is unchanged. No source or
initialization is relayed to Judge; no substantive opening is introduced.

Both recoveries use 32768 max tokens, temperature .5, deployment-default reasoning,
no tools, no ASK cap, no automatic semantic retries. Deterministic parsing accepts
literal control characters, whitespace and a single JSON fence only; it does not
extract objects from prose, invent fields or use a repair model. Empty visible
answers remain failures. These are amended, failure-selected attempts and must
not be pooled as uniform original-protocol replicates.

The same transport qualification is inherited, not repeated. New allowance use
is counted separately from inherited original receipts. Stop before another
request at a conservative $1.90 new-usage estimate. A stopped partial is not a
forced decision. Sources, histories and provider receipts remain private.

Repository-root entry:

```powershell
python -X utf8 -B scripts/test_boundary_go_recovery.py
python -X utf8 -B scripts/run_boundary_go_recovery.py --prepare
python -X utf8 -B scripts/run_boundary_go_recovery.py --execute --key-stdin
```

The launcher requires the ignored original run for recovery. Public reproduction
of the two unchanged completed endpoints remains `scripts/analyze_boundary_go_snapshot.py`.
