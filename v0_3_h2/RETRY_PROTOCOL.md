# Neutral retry01: user-authorized amendment

After qualification01 ended with a neutral no-output timeout and one salient response, the user explicitly requested one neutral rerun. This overrides the earlier no-resend stopping rule for this single rerun. It is an operational amendment, not a revision of the frozen prompts or original cutoff evidence.

Send the exact frozen `neutral_prompt.txt` once in a fresh isolated Arena Direct conversation with `gemini-3.8-flash-high`. Do not edit dialogue, public facts, wording, instructions, model or scoring thresholds. Do not resend salient, inspect the original neutral for response selection, or run extra variants. The original neutral receipt and salient reply remain unchanged. Save new receipts under ignored `runs/h2_neutral_retry01/`.

Allow up to approximately five minutes, then one reload/status check and a short hydration check if necessary. If still no output, preserve partial and stop. Skip anonymous comparisons without quality choice; capture only a restored fixed-model reply. Stop for unresolved model identity, verification or malformed actual reply; no quality-based regeneration.

Compare the rerun to the already captured salient reply in a separate report, retaining the original qualification's incomplete status. This is an amended, temporally separated comparison, with no additional independent background/transcript. Sampling variability and deployment drift remain confounded with presentation. No automatic monitor or GitHub push is requested here.
