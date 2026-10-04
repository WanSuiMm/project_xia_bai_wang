# Surface-diverse Frozen snapshot: three endpoints, one usage cutoff

Two new source families, two reciprocal Qwen3.8 Max / GLM-5.3 directions. Three of four configured trajectories completed; all three selected a speaker, none abstained. The fourth stopped at the batch's operational allowance protection, without a terminal decision. This is a small exploratory snapshot, not four completed trials or a confirmatory study.

| Family | Readers → Judge | ASK actions | Terminal | Confidence | Endpoint status |
|---|---|---:|---|---:|---|
| EB05 bridge-access tokens | Qwen → GLM | 6 | B | .60 | Completed |
| EB05 bridge-access tokens | GLM → Qwen | 2 | A | .80 | Completed |
| EB06 seed-wrapping trial | Qwen → GLM | 4 | A | .70 | Completed |
| EB06 seed-wrapping trial | GLM → Qwen | 6 | None | — | Usage cutoff; sixth ASK awaits B answer |

Batch ended at estimated allowance use USD 1.906307 after the previous request crossed the USD 1.90 pre-request threshold. The missing B request was never dispatched. Fourth slot has 17 captured replies and no endpoint; six ASK actions are not six completed joint question-answer rounds. No platform error or malformed reply appears in these captured requests. The last slot is not scored as wrong, correct or abstention.

## Design and interpretation

Both readers genuinely received their own finite document. All texts and seats were frozen before independent random target draws; target never enters role prompts. The Judge was not told the random-label mechanism. Target matches are arbitrary-label matches, not knowledge-access accuracy. This control tests behavior on insufficient target-identifying evidence, not which reader actually possesses a source.

EB05 documents have 309 and 293 words; EB06 has 291 and 288. No shared contiguous 12-word span within either pair. The texts were separately composed by the same investigator with roughly matched fact slots, not independently authored or IID source samples. They differ in organization, narrative framing, facts and omissions. Those differences can affect Reader behavior. The no-shared-span check does not certify complete surface independence or matched cognitive difficulty.

The earlier [ecological/archaeology pair](FROZEN_PAIR_RESULTS.md) abstained, whereas this completed subset made three selections. Sources, domains and framing also changed, so this is not a causal effect of removing parallel wording or a reliable abstention-rate estimate. Two families, not four independent families; reciprocal directions are repeated configurations within families. Missingness from a sequential cost limit can bias the completed subset.

## Evidence-bound rationale observations

- EB05 Q→G: Judge recognized that both accounts were stable and source-anchored, then favored wording alignment with public context. It assumed the public brief was a paraphrase of the designated target. That assumption is not the experiment's generation mechanism; target is independently randomized.
- EB05 G→Q: Judge preferred direct quotations over what B described as a paraphrased account. B did quote its actual supplied document while qualifying whether those were the underlying note's own words. Such provenance framing does not identify the randomly designated target.
- EB06 Q→G: Judge interpreted B's opening follow-up caution as a late-added patch. B's supplied source actually starts: “The Larch Mere nursery's May 2022 report opens with a caution about its follow-up”. Therefore its being reported later in conversation does not establish source fabrication. This check does not establish that every B answer was correct or invalidate every other rationale component. A denial of an attached table is also distinct from denying the source's reference to an observation sheet.

These are observations and source checks, not established internal reasoning mechanisms. No intervention isolates public-context alignment, document framing or contradiction detection. Source-relative behavioral annotation remains pending.

## Reading and verification

Read this summary, [frozen protocol](SURFACE_DIVERSE_FROZEN_PROTOCOL.md), then [allowlisted evidence](published_runs/go_surface_diverse_cutoff_20261005/README.md). Materials: `scripts/prepare_surface_diverse_frozen.py`; launch/routing: `scripts/run_surface_diverse_frozen.py`; public audit: `scripts/publish_surface_diverse_frozen.py`.

```sh
python -X utf8 -B scripts/publish_surface_diverse_frozen.py
```

No API calls: verifies hashes, text sizes, shared-span check, source isolation, equal Reader policies, seed replay, exact routing, terminal decisions and the missing next request. Pre-dispatch suffix01 interface failure made zero provider requests; suffix02 fixed a missing hash compatibility field with the same exact bundle. Original private records are unchanged. Provider reasoning, account/session identifiers and machine execution receipts are excluded. Earlier results remain unchanged; no continuation is launched by publication.
