# OSI48 credential recovery

Authorized 2026-10-09 when the user supplied a replacement credential and asked to try it. The original run is immutable: one HTTP 403/payment-category failure, zero model answers, 47 unstarted positions. No numerical endpoint is available to select or replace.

Use a new run, opencode_go_20261009_opponent_strategy_inference48_02. Preserve all 48 original request IDs, exact prompt bytes, order, model IDs, inference settings, parser, continuous metrics, and stop policy. The first scheduled new request retries the one delivery-failed position and serves as the credential/interface test; it counts within the new batch's 48 requests. All 47 other positions have never been sent. At most 49 physical requests can occur across the two attempts; never describe them as a clean original 48-call run.

The scientific design is unchanged. The original protocol's no-automatic-retry rule was obeyed. This is a newly human-authorized recovery after an HTTP error, not a correctness-selected retry. Halt again on delivery/model errors and preserve unstarted cells. Do not add a separate paid credential smoke, change models, or enable billing/overage.

Enter the replacement credential through the launcher's hidden getpass input. It is transferred only into the launch process and its child environment; no command argument, file, prompt, stdout/stderr, receipt, or persistent credential setting contains it. The replacement is not written to Git or to memory. The unmodified collector supplies the environment key to the same OpenCode Go endpoint and redacts it from visible response text.

Before the new dispatch, freeze this amendment and the small recovery launcher alongside the unchanged protocol, prompts and collection code. The launcher checks that the parent has exactly one payment-category HTTP 403 receipt and no model answers. It verifies the new schedule/prompt bytes against that parent before launch.

Run from the project root:

    python -X utf8 -B scripts/launch_opponent_strategy_recovery.py --prepare
    python -X utf8 -B scripts/run_opponent_strategy_inference.py --run epistemic_boundary_mimicry/runs/opencode_go_20261009_opponent_strategy_inference48_02 --audit
    python -X utf8 -B scripts/launch_opponent_strategy_recovery.py --launch-hidden

The bounded worker analyzes its own new batch at exit. A one-shot launch verification records its actual dispatch and initial reply or delivery failure. No recurring monitor or publication is added.
