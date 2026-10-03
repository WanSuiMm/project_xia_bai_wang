# Naturalistic Study 1 — collection status

Attempted 11/24; completed 1/24; captured 33/48 sent messages. Correct terminal picks 1/1; abstentions 0. Receipt-integrity audit errors: 0.

Collection stopped after multiple sessions explicitly reported the Arena rate limit. Thirteen planned trajectories were not sent. Six attempted trajectories ended at rate limits, two at other platform errors, one at malformed speaker JSON, and one was invalidated after a host state bug caused a duplicate opening send. No retry or replacement was used to rescue an outcome.

A stale host instance used during cutoff bookkeeping omitted 19 already sent messages from six records. They were recovered from preserved visible browser pages using the frozen prompt templates. Their nine final replies remain exact; original send/capture times are unavailable and explicitly null. The recovery manifest is local. These deviations constrain the pilot; the integrity audit is not evidence that execution had no errors.

These are exploratory trajectories, not a family ranking or an interaction benefit estimate. Missing outputs are not wrong judgments. No passive, human, self-model or matched actor–observer condition was collected.

| Trajectory | Speaker → Judge | State | Asks | Pick | Correct |
|---|---|---|---:|---|---|
| N01_D1 | claude-sonnet-5-high → gpt-5.5-instant | completed | 2 | B | True |
| N01_D2 | gpt-5.5-instant → claude-sonnet-5-high | blocked_platform | 3 | — | None |
| N02_D1 | claude-sonnet-5-high → gemini-3.8-flash-high | blocked_rate_limit | 0 | — | None |
| N02_D2 | gemini-3.8-flash-high → claude-sonnet-5-high | not_started | 0 | — | None |
| N03_D1 | gpt-5.5-instant → gemini-3.8-flash-high | blocked_rate_limit | 0 | — | None |
| N03_D2 | gemini-3.8-flash-high → gpt-5.5-instant | not_started | 0 | — | None |
| N04_D1 | claude-sonnet-5-high → gpt-5.5-instant | blocked_platform | 2 | — | None |
| N04_D2 | gpt-5.5-instant → claude-sonnet-5-high | blocked_rate_limit | 1 | — | None |
| N05_D1 | claude-sonnet-5-high → gemini-3.8-flash-high | blocked_rate_limit | 0 | — | None |
| N05_D2 | gemini-3.8-flash-high → claude-sonnet-5-high | not_started | 0 | — | None |
| N06_D1 | gpt-5.5-instant → gemini-3.8-flash-high | not_started | 0 | — | None |
| N06_D2 | gemini-3.8-flash-high → gpt-5.5-instant | not_started | 0 | — | None |
| N07_D1 | claude-sonnet-5-high → gpt-5.5-instant | invalid_host_resend | 0 | — | None |
| N07_D2 | gpt-5.5-instant → claude-sonnet-5-high | blocked_rate_limit | 1 | — | None |
| N08_D1 | claude-sonnet-5-high → gemini-3.8-flash-high | not_started | 0 | — | None |
| N08_D2 | gemini-3.8-flash-high → claude-sonnet-5-high | not_started | 0 | — | None |
| N09_D1 | gpt-5.5-instant → gemini-3.8-flash-high | not_started | 0 | — | None |
| N09_D2 | gemini-3.8-flash-high → gpt-5.5-instant | not_started | 0 | — | None |
| N10_D1 | claude-sonnet-5-high → gpt-5.5-instant | protocol_failure | 0 | — | None |
| N10_D2 | gpt-5.5-instant → claude-sonnet-5-high | blocked_rate_limit | 1 | — | None |
| N11_D1 | claude-sonnet-5-high → gemini-3.8-flash-high | not_started | 0 | — | None |
| N11_D2 | gemini-3.8-flash-high → claude-sonnet-5-high | not_started | 0 | — | None |
| N12_D1 | gpt-5.5-instant → gemini-3.8-flash-high | not_started | 0 | — | None |
| N12_D2 | gemini-3.8-flash-high → gpt-5.5-instant | not_started | 0 | — | None |

The local excluded run preserves exact prompts and replies. See [protocol](PROTOCOL.md); qualitative observations require quotes from actual trajectories. No new evidence has been published to GitHub.
