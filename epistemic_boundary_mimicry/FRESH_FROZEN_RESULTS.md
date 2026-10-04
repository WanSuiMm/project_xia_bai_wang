# Fresh ecological Frozen control: incomplete

**No terminal result.** The run stopped on protocol failure after three complete
ASK-and-answer rounds. The next GLM-5.3 Judge response was meant to request a
fourth question but contained an unterminated JSON string. The original visible
text is preserved, rejected by the frozen parser and never sent to Speakers.
It is not STOP, ABSTAIN, a correct pick or a wrong pick.

| Field | Observed value |
|---|---|
| New case | EB03, fictional moth resting positions after shade-screen moves |
| Readers / Judge | Qwen3.8 Max / GLM-5.3 |
| Complete ASK actions | 3 |
| Physical calls | 10 |
| Valid visible replies | 9 |
| Final invalid reply | Judge, next-question response |
| HTTP / finish reason | 200 / `stop` |
| Parser failure | Unterminated string starting at line 1, column 44 |
| Terminal / target score | Missing / unscored |
| Conservative allowance estimate | $0.183 |

This was not HTTP 429 or the local usage ceiling, and the provider did not flag
max-token truncation. Its `stop` flag does not make malformed visible JSON valid.
No response was regenerated or repaired for publication.

[Protocol](FRESH_FROZEN_PROTOCOL.md): two fresh 320-word sources and a random seat
assignment were frozen before independent target designation. Both readers receive
the same policy and only their own source. Judge receives no target-linked truth
and is not told the label's random generation mechanism. Therefore this blind
control cannot measure knowingly ignoring an explicitly disclosed null. The
sources come from the same procedural template, not independently authored prose.

[Public cutoff evidence](published_runs/go_fresh_frozen_cutoff_20261004/README.md)
contains exact prompts and visible answers, including invalid final text, both
used sources and randomization provenance. Private reasoning, credentials and
account/session identifiers are excluded. Reproduce without API calls:

```powershell
python -X utf8 -B scripts/publish_boundary_fresh_frozen.py
```

The seven previous endpoints remain unchanged. This new attempt adds a third
source background but no completed endpoint, so it cannot support a claim about
abstention, forced attribution or target identifiability behavior at termination.
