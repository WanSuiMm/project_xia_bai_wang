# R0 infrastructure recovery: credential availability

Authorized on 2026-10-07 after run `opencode_go_20261007_frozen_replay_r0_84_01` halted with two HTTP 403 errors and no model answers. The user supplied another OpenCode Go credential and authorized using either credential that supports replay. The original failed run remains intact.

The new run is `opencode_go_20261007_frozen_replay_r0_84_02`. All seven payloads, 14 prompts, 84 transcript/model/condition/repetition positions, randomized order, models, endpoints, weights, sampling configuration and failure rules must match run 01. Only creation timestamps and local infrastructure-recovery metadata differ. No scientific result was observed in run 01, so this recovery is not selected by a model outcome.

Before dispatch, perform bounded credential checks independent of the experimental stimuli: one short JSON request to GLM per distinct supplied credential, followed by Qwen verification for a credential whose GLM check is valid. Prefer the existing environment credential if both support both endpoints. If Qwen fails for that credential, check the other GLM-qualified credential. At most four generation checks; no automatic retry, purchase, overage change or model substitution. Store only sanitized HTTP/parse/model/usage status under the new ignored run, label credentials only as existing/supplied, and never record their values, prefixes, hashes or account URLs.

The supplied credential is read through a terminal prompt with echo disabled and retained only in process memory. Refuse any fallback that would echo the credential. The selected credential is made available to the unchanged runner through the process-local `OPENCODE_GO_API_KEY` environment variable. It is never written to commands, project files or receipts. Interface probes are not replay results.

If neither credential supports both endpoints, stop without dispatching any of the 84 experimental requests. If verification succeeds, dispatch the full frozen queue once. Original run errors are infrastructure attempts outside the new sampling queue; invalid model replies and later transport failures within the new run retain the original no-retry/missing-data rules. Completion means all planned positions were attempted; valid-response completeness is reported separately.

Entry: `python -X utf8 -B scripts/recover_frozen_replay_r0.py`, from the repository root in an interactive terminal. This authorization includes launch and a durable launch receipt. It does not authorize automatic monitoring or GitHub publication.
