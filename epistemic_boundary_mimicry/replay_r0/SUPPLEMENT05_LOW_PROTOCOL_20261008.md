# R0: five-position engineering completion with low reasoning

The user explicitly requested fixing and completing the remaining supplementary requests on 2026-10-08. The original 84-position batch has 77 valid replies. Supplement07 and supplement06 each added one distinct valid position. Supplement06's process exited with three unstarted positions, one repeated length truncation, and one dispatched request without a response receipt. Its stale RUNNING status, lock, and all previous artifacts remain unchanged. The cause of its process exit is unknown.

This amendment permits one new attempt at each of the five positions lacking a valid response across these runs. An earlier dispatched-without-response position remains an unknown earlier attempt; the new attempt is not its recovered response. Exclude all 79 already valid positions. Freeze exact original prompt bytes, original-position mapping, prior attempt classification, and prior artifact hashes before dispatch.

The repeated truncation returned `finish_reason=length`, 32,768 completion tokens and zero visible answer characters. Repeating the same settings did not resolve output exhaustion. For these five engineering attempts, request GLM-5.3 with `thinking.type=enabled` and `reasoning_effort=low`, retaining original temperature .5, max_tokens 32768, nonstreaming, no tools, independent fresh sessions, strict original JSON parser and 120-word reason limit. Official GLM-5.3 documentation supports low/high/max reasoning and states that reasoning cannot be disabled: [model parameters](https://docs.z.ai/guides/llm/glm-5.3). Whether the OpenCode proxy actually honors the requested setting is not independently verified; a successful request alone does not prove effective reasoning effort.

This is a changed-configuration, failure-selected engineering supplement. It never replaces the original registered 77/84 analysis or becomes five additional independent samples. Any completion view must retain the requested parameter difference and first-valid-per-original-position selection rule. Do not interpret differences from the original run as a controlled reasoning-effort effect.

Use one sequential worker with a 600-second request timeout. The first actual missing-position request doubles as the interface check; no extra generation smoke. At most five model requests, one per selected position. No semantic repair, parser relaxation, automatic retry, model substitution, allowance changes, purchase or overage. Stop on HTTP errors or unknown transport outcome and retain remaining positions unstarted. Unsupported parameters are recorded as interface failures rather than silently removed or retried.

Launch a separate detached worker with standard output/error in the ignored run directory, not a long-lived interactive terminal. The new credential enters via a hidden terminal prompt and is passed only in child process memory; do not store it in commands, files, prompts, receipts or logs. Persist each dispatch before sending and each response immediately after receipt. A later restart must refuse an existing execution or dispatch; stale earlier locks are never deleted to enable a retry. Launch completion requires a verified live worker and a durable dispatch receipt; result completion requires actual response receipts.

```text
python -X utf8 -B scripts/complete_frozen_replay_r0_low.py --prepare
python -X utf8 -B scripts/complete_frozen_replay_r0_low.py --audit
python -X utf8 -B scripts/complete_frozen_replay_r0_low.py --launch
```

The audit is offline. Launch is an explicit paid-request action, not an audit or default command. No recurring monitor is created.
