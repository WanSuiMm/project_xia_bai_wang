"""Audit and report the specifically authorized N02 judge recovery."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'naturalistic_study_1'
RUN = ROOT / 'runs/arena_20261003_naturalistic_judge_recovery01'

def main():
    b = json.loads((RUN / 'bundle.json').read_text(encoding='utf-8'))
    f = json.loads((RUN / 'freeze.json').read_text(encoding='utf-8'))
    r = json.loads((RUN / 'trajectories/N02_D1_Jretry01.json').read_text(encoding='utf-8'))
    old = json.loads((ROOT / 'runs/arena_20261003_naturalistic_resume01/trajectories/N02_D1.json').read_text(encoding='utf-8'))
    errors = []
    if hashlib.sha256((RUN / 'bundle.json').read_bytes()).hexdigest() != f['bundle_sha256']:
        errors.append('Recovery bundle hash mismatch')
    previous_judge_prompt = next(m['prompt'] for m in old['messages'] if m['role'] == 'J')
    first_judge = next(m for m in r['messages'] if m['role'] == 'J')
    if first_judge['prompt'] != previous_judge_prompt:
        errors.append('Judge prompt differs from original request')
    for role in ['A', 'B']:
        earlier = next(m for m in old['messages'] if m['role'] == role and m.get('reply'))
        inherited = next(m for m in r['messages'] if m['role'] == role and m.get('inherited_from'))
        if earlier['parsed']['reply'] != inherited['parsed']['reply']:
            errors.append('Opening changed: ' + role)
        follow = next(m for m in r['messages'] if m['role'] == role and m.get('sent_utc'))
        if follow['url'] != earlier['url']:
            errors.append('Speaker conversation changed: ' + role)
    c = next(c for c in b['cases'] if c['case_id'] == 'N02')
    for m in r['messages']:
        if m['role'] != r['knower'] and c['source_text'] in m['prompt']:
            errors.append('Private source disclosure')
    new = [m for m in r['messages'] if m.get('sent_utc')]
    times = sorted(datetime.fromisoformat(m['sent_utc'].replace('Z', '+00:00')) for m in new)
    gaps = [(y-x).total_seconds() for x,y in zip(times,times[1:])]
    if gaps and min(gaps) < 30:
        errors.append('Submission spacing below 30 seconds')
    summary = {'status': r['status'], 'case_id': 'N02', 'speaker_model': r['speaker_model'],
               'judge_model': r['judge_model'], 'asks': r['asks'], 'new_sends': len(new),
               'new_replies': sum(bool(m.get('reply')) for m in new), 'reused_openings': 2,
               'terminal': r.get('terminal'), 'correct': r.get('correct'),
               'minimum_request_gap_seconds': min(gaps) if gaps else None, 'audit_errors': errors,
               'limits': 'Fresh judge on identical inherited openings; original failed judge retained; one exploratory game, no passive comparison.'}
    (RUN / 'analysis.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    status = json.loads((RUN / 'status.json').read_text(encoding='utf-8'))
    status.update(new_replies=summary['new_replies'], inherited_replies=2, status=r['status'])
    (RUN / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    text = f'''# N02 — recovered judge session

Status: `{r['status']}`. User explicitly requested recovery of the missing original judge request. The same A/B openings and byte-identical original judge prompt were reused. Speaker follow-ups ran in their restored original Claude conversations; no new opening was generated. The judge used a fresh Arena Direct `gemini-3.8-flash-high` session. The prior failed request remains unchanged and is not counted as a model error.

Recovered endpoint: pick **{r.get('terminal', {}).get('pick')}**, true access **{r['knower']}**, correct **{r.get('correct')}**, reported confidence **{r.get('terminal', {}).get('confidence')}**. The judge used {r['asks']} ASK action, containing three subquestions, before stopping. New requests/replies: **{summary['new_sends']}/{summary['new_replies']}**, plus two inherited openings. Minimum submission gap **{summary['minimum_request_gap_seconds']:.1f}s**. Source isolation, exact prompt/opening reuse and original speaker-session checks: **{len(errors)} audit errors**.

The query asked about the narrow strip's material/attachment, financial terms and whether other instruments/guilds appeared. A distinguished unspecified material/attachment and fee amounts from the stated responsibility rules and illustrative dispute. B continued interpreting “instrument makers” as musical instrument makers: it recalled lutes/viols and explicitly treated measuring balances as possibly belonging to a different guild. The final judge reason focused on this mismatch and A's specific procedure details.

Arena inserted an anonymous comparison on the final judge turn. It was skipped; only the subsequently displayed fixed-model response was captured. This response was distinct from the two anonymous candidates. Platform labels are not independent model-identity verification.

This is one exploratory trajectory. A familiar-world interpretation error in B and source-bounded responding in A occurred in this case; neither establishes a stable policy or an interaction advantage. No passive baseline or token-matched control was run. Keep the failed request and this authorized recovery as separate attempts, without selecting a preferred outcome.

Exact local evidence: excluded `runs/arena_20261003_naturalistic_judge_recovery01/`. Audit with `python -X utf8 -B scripts/analyze_naturalistic_judge_recovery.py`. Other planned cases remain incomplete. No GitHub push or background monitoring.
'''
    (ROOT / 'RECOVERY_RESULTS.md').write_text(text, encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == '__main__':
    main()
