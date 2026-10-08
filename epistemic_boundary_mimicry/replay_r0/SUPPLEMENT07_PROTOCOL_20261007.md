# R0: seven-position failure-selected supplement

The user explicitly authorized only supplementary reruns on 2026-10-07 and then confirmed execution. GitHub publication is paused. The original 84-request run is complete with 77 valid replies, all Qwen positions valid, and seven GLM Blind positions invalid. This amendment permits exactly one new request for each of those seven positions; no valid position or other experimental module may be rerun.

Parent: `opencode_go_20261007_frozen_replay_r0_84_02`. New run: `opencode_go_20261007_frozen_replay_r0_supplement07_01`, in the ignored project run tree. Five positions were token-truncated, one strict JSON reply exceeded the reason-word limit by one word, and one timed out. The timeout's server-side completion and charged usage remain unknown. A user-authorized fresh attempt does not erase or reclassify that unknown original dispatch.

Freeze the seven positions in their original manifest order before any supplementary request. Copy each exact parent prompt and preserve model `glm-5.3`, temperature .5, max_tokens 32768, nonstreaming, default reasoning, no tools, reason limit 120 words, probability/action schema and 600-second timeout. Use a fresh session for each new call and one sequential GLM worker, as in the original per-model stream. The selected new credential remains process-only, supplied through a non-echoing input prompt; do not store it in commands, scripts, receipts or project files. No extra generation smoke or model substitution is required.

Each supplement position maps explicitly to its original request ID and error record. Preserve all 84 original receipts, prompt/manifest/freeze files and primary analysis byte-for-byte. The original registered analysis remains 77 valid / 84 planned with its original missing-weight bounds. A later completion view must be labeled failure-selected supplementary analysis and retain both attempts; it is not 84 originally successful calls, seven new independent families, or a clean replacement preregistered dataset.

No automatic retry of a supplementary failure, relaxed parser, changed token cap, probability repair or repeated generation until success. HTTP 401/403/429 stops the remaining supplement; other invalid replies stay invalid. Completion of this launch requires a verified dispatch and durable receipt, not automatic monitoring. No publication or broader new study is authorized by this supplement instruction.

From the repository root:

```text
python -X utf8 -B scripts/rerun_frozen_replay_r0_missing.py --prepare
python -X utf8 -B scripts/rerun_frozen_replay_r0_missing.py --audit
python -X utf8 -B scripts/rerun_frozen_replay_r0_missing.py --execute
```

The final command requires an interactive terminal for hidden credential input. It refuses an existing dispatch or non-prepared state to prevent duplicating any supplementary request.
