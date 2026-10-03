# Naturalistic Study 1 — serial continuation

Separate attempt: 11/23 configurations attempted, 7 completed; 88/92 responses captured. Minimum submission gap: 38.7 seconds. Receipt audit errors: 0.

N02_D1 original judge request did not recover after security verification and remains a platform-missing receipt. The user explicitly requested its recovery: the separate [N02 recovery](RECOVERY_RESULTS.md) preserves identical openings, a byte-identical initial judge prompt and the original restored speaker sessions. The table below reports the current durable continuation receipts; pending entries are not completed results. No automatic monitor is running.

N03_D2 completed: Gemini speakers → GPT judge, true access A. The judge asked BOTH once about firing, recurring marks and limits of fire interpretations, then selected A with reported confidence 0.995. The uninformed account attributed clay hardening to this fire, whereas the informed account cited pre-fire firing and worn edges beneath soot. This is one additional qualitative case, not a stable causal finding.

Capture correction: Arena renders unfenced JSON as Markdown, splitting paragraphs and removing escaped punctuation. Full visible response bubbles are now recorded. A single-field speaker wrapper can be decoded deterministically from its complete visible content; judge routing still requires valid JSON. Two initial capture errors in this attempt were corrected from the same pages without any model resend; the earlier captures/events remain in the records. Visible text is not asserted to be byte-identical to the original generation stream. Original-run cutoff files remain unchanged; its format-failure classifications may include display parsing artifacts and need a separate retrospective audit.

| Trajectory | Status | Asks | Sends / replies | Terminal |
|---|---|---:|---:|---|
| N01_D2 | completed | 6 | 21 / 21 | A |
| N02_D1 | blocked_platform | 0 | 3 / 2 | pending |
| N02_D2 | completed | 5 | 18 / 18 | B |
| N03_D1 | completed | 1 | 5 / 5 | B |
| N03_D2 | completed | 1 | 6 / 6 | A |
| N04_D1 | blocked_platform | 0 | 3 / 2 | pending |
| N04_D2 | completed | 5 | 13 / 13 | A |
| N05_D1 | completed | 1 | 6 / 6 | A |
| N05_D2 | completed | 2 | 9 / 9 | B |
| N06_D1 | blocked_platform | 1 | 6 / 5 | pending |
| N06_D2 | generating | 0 | 2 / 1 | pending |

See [continuation protocol](RESUME_PROTOCOL.md). Original [cutoff](RESULTS.md) is separate; do not pool repeated configurations or select preferable attempts.
