"""Summarize first available endpoints without replacing failed attempts."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'strategic_bluff_pilot'
RUNS = ['arena_20261003_strategic01', 'arena_20261003_strategic_retry01', 'arena_20261003_strategic_recovery02', 'arena_20261003_strategic_recovery03', 'arena_20261004_strategic_completion04']

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def main():
    slots = read(BASE / 'runs' / RUNS[0] / 'bundle.json')['trajectories']
    attempts = {t['id']: [] for t in slots}
    submissions = replies = partials = 0
    for name in RUNS:
        run = BASE / 'runs' / name
        if not run.exists():
            continue
        for t in read(run / 'bundle.json')['trajectories']:
            r = read(run / 'trajectories' / (t['id']+'.json'))
            attempts[t['id']].append((name, r))
            for m in r['messages']:
                if m.get('inherited_from_run'):
                    continue
                submissions += bool(m.get('sent_utc')) + len(m.get('retry_sends', []))
                replies += bool(m.get('reply'))
                partials += m.get('capture_format') == 'incomplete_final_visible_wrapper'
    rows = []
    for t in slots:
        endpoints = [(name,r) for name,r in attempts[t['id']] if r['status'] == 'completed']
        name,r = endpoints[0] if endpoints else attempts[t['id']][-1]
        rows.append({**t, 'endpoint_run': name if endpoints else None, 'status': r['status'],
                     'asks': r['asks'], 'terminal': r.get('terminal'), 'correct': r.get('correct'),
                     'own_partial_context_retry':any(e['type']=='authorized_incomplete_followup_retry' for e in r.get('events', [])),
                     'attempt_history': [{'run':n, 'status':x['status']} for n,x in attempts[t['id']]]})
    complete = [r for r in rows if r['endpoint_run']]
    summary = {'configured_slots':8, 'source_dossiers':2, 'completed_slots':len(complete),
               'physical_submissions_across_attempts':submissions, 'distinct_complete_replies':replies,
               'retained_partial_outputs':partials, 'endpoint_selection':'First completed attempt per slot; failed attempts retained',
               'by_condition':{c:{'completed':sum(r['condition']==c for r in complete),
                                  'correct':sum(r['condition']==c and r['correct'] is True for r in complete),
                                  'asks':[r['asks'] for r in complete if r['condition']==c]} for c in ['natural','strong']},
               'rows':rows, 'interpretation':'Descriptive recovery completion; failure-selected retries are not an unbiased fresh sample or a causal instruction/training estimate.'}
    (BASE/'COMPLETION_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# First available endpoints across original and authorized recovery attempts','',
           f"Completed configured slots: **{len(complete)}/8** across **2** source dossiers. Physical submissions: {submissions}; distinct complete replies: {replies}; retained partial outputs: {partials}.",'',
           'Use the first completed attempt per slot, selected independently of its correctness. Retain all original failures and cutoff reports. Completion through failure-selected recovery is descriptive, not an unbiased extra sample. Speaker openings may be inherited; they are not counted twice.','',
           '| Slot | Endpoint run | ASK | Pick | Confidence | Correct |','|---|---|---:|---|---:|---|']
    for r in rows:
        term=r['terminal'] or {}
        lines.append(f"| {r['id']} | {r['endpoint_run'] or 'pending'} | {r['asks']} | {term.get('pick','unavailable')} | {term.get('confidence','—')} | {r['correct']} |")
    lines += ['', 'Read [original cutoff](RESULTS.md), [six-attempt retry](RETRY_RESULTS.md), [remaining-request recovery](RECOVERY_RESULTS.md), and [scope amendments](RETRY_PROTOCOL.md). Correct picks do not validate Judge rationales. Only two independent dossiers are represented; no robust ToM, model ranking, causal instruction effect or post-training explanation follows. No automatic publication or background monitoring.']
    if any(r['own_partial_context_retry'] for r in rows):
        lines += ['', 'Recovery03 includes a repeated identical follow-up after a truncated reply. The Speaker could see its own failed partial response in its conversation; the Judge did not receive that partial. This context difference limits comparison with a clean uninterrupted trajectory. See [latest recovery receipts](RECOVERY03_RESULTS.md).']
    if any(r['endpoint_run']=='arena_20261004_strategic_completion04' for r in rows):
        lines += ['', 'Completion04 removes the ten-ASK cap after six ASK actions for strong and from the initial Judge prompt for natural. This is mixed-protocol completion, not eight uniform fixed-protocol replications. See [amendment](COMPLETION04_PROTOCOL.md).']
    (BASE/'COMPLETION_SUMMARY.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},ensure_ascii=False))

if __name__=='__main__':
    main()
