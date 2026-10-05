# Fixed terminal-blind replay cohort

Selection rule frozen before any new decision replay: include every complete canonical Frozen trajectory in the API EB01–EB06 inventory. No filtering on original choice, abstention, confidence or rationale. Seven eligible dialogues from six material families. The partial eighth dialogue is retained for exploratory interaction coding and excluded from the default terminal replay cohort.

| ID | Original Judge | ASK actions | Eligibility |
|---|---|---:|---|
| EB01_D1_symmetric_frozen | GLM-5.3 | 4 | Complete |
| EB02_D1_symmetric_frozen | GLM-5.3 | 9 | Complete |
| EB03_D1_symmetric_frozen | GLM-5.3 | 4 | Complete, documented syntax continuation |
| EB04_D1_symmetric_frozen | GLM-5.3 | 3 | Complete |
| EB05_D1_symmetric_frozen | GLM-5.3 | 6 | Complete |
| EB05_D2_symmetric_frozen | Qwen3.8 Max | 2 | Complete |
| EB06_D1_symmetric_frozen | GLM-5.3 | 4 | Complete |
| EB06_D2_symmetric_frozen | Qwen3.8 Max | 6 | Excluded: incomplete usage cutoff |

`replay_cohort.json` contains the exact prepared payload for each included dialogue and a payload hash. The model-facing `payload` has only public context and ordered questions/answers. Administrative IDs/hashes are not model input. Recipient labels A/B in questions identify whom the Judge asked, not the Host target. Removed: original terminal, confidence, final rationale, score, target label, role setup and unobserved private source inputs. Quotations speakers actually gave remain visible evidence. Original leading questions remain part of the transcript; this cohort does not erase their effects.

`freeze.json` binds codebook, corpus inventory, annotation inputs and cohort bytes. Scope is preparation only: no new Judge requests or API expense. Original complete/incomplete evidence and recovery lineage remain unchanged. No blind/informed prompt, reward scheme, sampling replication count or new statistical endpoint has been frozen by fixing this cohort; those require a subsequent explicit execution protocol.

Same-transcript disclosure replay can identify a decision change conditional on this exploratory cohort. It cannot establish effects on autonomous interrogation, general source populations, model rankings or the independent causal effect of document style. Informed-null .50 alone would not establish general mathematical understanding. Original Judge histories differ from fresh replay; a fresh blind replay is required as matched control for disclosure.
