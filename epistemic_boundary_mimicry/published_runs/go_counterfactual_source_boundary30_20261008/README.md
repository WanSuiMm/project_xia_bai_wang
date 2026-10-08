# CSB30 public evidence

This package contains the completed 30-call Counterfactual Source Boundary qualification: six fictional source families, 18 Qwen Speaker outputs, and 12 GLM Judge outputs. It preserves every exact prompt and final visible reply.

Start with [results](analysis/RESULTS.md), then [canonical analysis](analysis/summary.json) and [public reconstruction record](analysis/public_verification.json). The exact per-call prompts, replies, and safe receipt projections are secondary evidence.

Reader seats were fixed within each family and balanced three per seat. The same saved Bluffer reply appears in both Judge prompts for a family. Results remain descriptive over six authored materials; the frozen analyzer marks manual Reader-fidelity coding as pending.

`source_freeze.json` preserves the pre-request hashes for the scientific inputs and 18 Speaker prompts. `publication.json` separately records original source receipt hashes, public projection hashes, exact prompt hashes, and visible-text hashes. A source receipt hash refers to the original local receipt bytes; it is not presented as the hash of a sanitized public projection.

The source launch directory, credentials, machine paths, host/PID/session values, raw provider bodies, and hidden reasoning are excluded. The public package includes frozen source snapshots for offline reproduction. From the project root, run `python -X utf8 -B scripts/publish_counterfactual_source_boundary.py` to audit the package without network access. `--export` is only for the original local source checkout and refuses to overwrite an existing package.
