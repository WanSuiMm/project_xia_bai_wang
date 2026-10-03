"""Analyze preserved naturalistic receipts without model calls."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'naturalistic_study_1'
RUN = ROOT / 'runs' / 'arena_20261003_naturalistic01'

def main():
    bundle = json.loads((RUN / 'bundle.json').read_text(encoding='utf-8'))
    freeze = json.loads((RUN / 'freeze.json').read_text(encoding='utf-8'))
    errors = []
    if hashlib.sha256((RUN / 'bundle.json').read_bytes()).hexdigest() != freeze['bundle_sha256']:
        errors.append('Frozen bundle hash differs')
    rows = []
    for plan in bundle['trajectories']:
        r = json.loads((RUN / 'trajectories' / (plan['id'] + '.json')).read_text(encoding='utf-8'))
        c = next(c for c in bundle['cases'] if c['case_id'] == plan['case_id'])
        if r['asks'] > 10:
            errors.append(plan['id'] + ': exceeded cap')
        for m in r['messages']:
            if m['role'] != r['knower'] and c['source_text'] in m['prompt']:
                errors.append(plan['id'] + ': source disclosure')
            if m.get('reply') and not m.get('raw'):
                errors.append(plan['id'] + ': reply lacks raw capture')
        rows.append({**plan, 'status': r['status'], 'asks': r['asks'],
                     'sends': sum('sent_utc' in m for m in r['messages']),
                     'replies': sum(bool(m.get('reply')) for m in r['messages']),
                     'terminal': r.get('terminal'), 'correct': r.get('correct')})
    completed = [r for r in rows if r['status'] == 'completed']
    picks = [r for r in completed if r['terminal']['action'] == 'STOP']
    summary = {'planned': 24, 'completed': len(completed), 'picks': len(picks),
               'attempted': sum(r['sends'] > 0 for r in rows),
               'status_counts': {state: sum(r['status'] == state for r in rows) for state in sorted({r['status'] for r in rows})},
               'correct_picks': sum(bool(r['correct']) for r in picks),
               'abstentions': len(completed) - len(picks),
               'sends': sum(r['sends'] for r in rows), 'replies': sum(r['replies'] for r in rows),
               'audit_errors': errors, 'rows': rows,
               'interpretation': 'Exploratory cross-family dialogues. No passive/self-model/control baseline; missing is not incorrect.'}
    (RUN / 'analysis.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    md = ['# Naturalistic Study 1 — collection status', '',
          f"Attempted {summary['attempted']}/24; completed {len(completed)}/24; captured {summary['replies']}/{summary['sends']} sent messages. Correct terminal picks {summary['correct_picks']}/{len(picks)}; abstentions {summary['abstentions']}. Receipt-integrity audit errors: {len(errors)}.", '',
          'Collection stopped after multiple sessions explicitly reported the Arena rate limit. Thirteen planned trajectories were not sent. Six attempted trajectories ended at rate limits, two at other platform errors, one at malformed speaker JSON, and one was invalidated after a host state bug caused a duplicate opening send. No retry or replacement was used to rescue an outcome.', '',
          'A stale host instance used during cutoff bookkeeping omitted 19 already sent messages from six records. They were recovered from preserved visible browser pages using the frozen prompt templates. Their nine final replies remain exact; original send/capture times are unavailable and explicitly null. The recovery manifest is local. These deviations constrain the pilot; the integrity audit is not evidence that execution had no errors.', '',
          'These are exploratory trajectories, not a family ranking or an interaction benefit estimate. Missing outputs are not wrong judgments. No passive, human, self-model or matched actor–observer condition was collected.', '',
          '| Trajectory | Speaker → Judge | State | Asks | Pick | Correct |',
          '|---|---|---|---:|---|---|']
    for r in rows:
        terminal = r['terminal'] or {}
        md.append(f"| {r['id']} | {r['speaker_model']} → {r['judge_model']} | {r['status']} | {r['asks']} | {terminal.get('pick', terminal.get('action', '—'))} | {r['correct']} |")
    md += ['', 'The local excluded run preserves exact prompts and replies. See [protocol](PROTOCOL.md); qualitative observations require quotes from actual trajectories. No new evidence has been published to GitHub.']
    (ROOT / 'RESULTS.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
