# Second-case follow-up: EB02 boarding slips

The user requested the existing second case, with the same four slots as case one;
not the proposed 36-trajectory study and not the two additional reverse case-one
slots. EB02 is the previously frozen fictional river-district boarding-slip dossier.
Sources, target designation, seats and private role instructions remain unchanged.

Preserve the original frozen bundle order after filtering:

1. EB02_D1_boundary_aware: Qwen speakers / GLM Judge.
2. EB02_D1_symmetric_frozen: Qwen readers / GLM Judge.
3. EB02_D1_strong: Qwen speakers / GLM Judge.
4. EB02_D2_boundary_aware: GLM speakers / Qwen Judge.

Uniform new protocol: fresh isolated sessions, Judge first, private Speaker
initialization combined with its first requested question, no READY or opening.
Judge freely selects A/B/BOTH and ASK/STOP/ABSTAIN after the required first ASK.
Host supplies no truth. Strict=False JSON control parsing, no prose extraction
or answer repair. Max tokens 32768, temperature .5, stream false, tools off,
deployment-default reasoning. Exact same already-qualified API transport/model
pair; no redundant qualification generations. No model fallback or semantic retry.

Run sequentially and preserve every physical response. No question-count cap.
Stop before another request if conservative new allowance use reaches $1.90;
partials remain incomplete rather than becoming forced decisions. No overage is
enabled. Endpoint output records correct/wrong/abstain, ASK count, confidence
when present, usage and any platform/protocol failure. Boundary coding is pending.

This adds one independent case to the first-case pilot. Four slots per case are
not independent dossiers; reciprocal condition coverage remains unbalanced and
case-one protocol was mixed. Do not claim a causal condition effect, model ranking,
confirmatory significance, or a controlled comparison to older Arena runs.
Original evidence remains intact; all raw new outputs stay in a new ignored run.

Repository-root commands (private frozen bundle required):

```powershell
python -X utf8 -B scripts/run_boundary_go_case2.py --prepare
python -X utf8 -B scripts/audit_boundary_go_case2.py
python -X utf8 -B scripts/run_boundary_go_case2.py --execute --key-stdin
```
