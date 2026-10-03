"""Summarize the separate serial continuation from its durable receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'naturalistic_study_1'
RUN = ROOT / 'runs/arena_20261003_naturalistic_resume01'

def main():
    b = json.loads((RUN / 'bundle.json').read_text(encoding='utf-8'))
    f = json.loads((RUN / 'freeze.json').read_text(encoding='utf-8'))
    errors = []
    if hashlib.sha256((RUN / 'bundle.json').read_bytes()).hexdigest() != f['bundle_sha256']:
        errors.append('Frozen resume bundle changed')
    rows = []
    sends = []
    for t in b['trajectories']:
        r = json.loads((RUN / 'trajectories' / (t['id'] + '.json')).read_text(encoding='utf-8'))
        c = next(c for c in b['cases'] if c['case_id'] == t['case_id'])
        for m in r['messages']:
            if m.get('sent_utc'):
                sends.append(m['sent_utc'])
            if m['role'] != t['knower'] and c['source_text'] in m['prompt']:
                errors.append(t['id'] + ': private source disclosed')
            if m.get('reply') and not m.get('raw'):
                errors.append(t['id'] + ': missing visible final response')
        rows.append({**t, 'status': r['status'], 'asks': r['asks'], 'sends': sum(bool(m.get('sent_utc')) for m in r['messages']),
                     'replies': sum(bool(m.get('reply')) for m in r['messages']), 'terminal': r.get('terminal'), 'correct': r.get('correct')})
    from datetime import datetime
    times = sorted(datetime.fromisoformat(x.replace('Z', '+00:00')) for x in sends)
    gaps = [(y-x).total_seconds() for x,y in zip(times,times[1:])]
    if gaps and min(gaps) < 30:
        errors.append('Request gap below frozen 30-second pacing')
    summary = {'planned_remaining': len(rows), 'attempted': sum(r['sends'] > 0 for r in rows),
               'completed': sum(r['status'] == 'completed' for r in rows), 'sends': sum(r['sends'] for r in rows),
               'replies': sum(r['replies'] for r in rows), 'minimum_request_gap_seconds': min(gaps) if gaps else None,
               'audit_errors': errors, 'rows': rows}
    (RUN / 'analysis.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# Naturalistic Study 1 — serial continuation', '',
             f"Separate attempt: {summary['attempted']}/{len(rows)} configurations attempted, {summary['completed']} completed; {summary['replies']}/{summary['sends']} responses captured. Minimum submission gap: {summary['minimum_request_gap_seconds']:.1f} seconds. Receipt audit errors: {len(errors)}.", '',
             'N02_D1 original judge request did not recover after security verification and remains a platform-missing receipt. The user explicitly requested its recovery: the separate [N02 recovery](RECOVERY_RESULTS.md) preserves identical openings, a byte-identical initial judge prompt and the original restored speaker sessions. The table below reports the current durable continuation receipts; pending entries are not completed results. No automatic monitor is running.', '',
             'N03_D2 completed: Gemini speakers → GPT judge, true access A. The judge asked BOTH once about firing, recurring marks and limits of fire interpretations, then selected A with reported confidence 0.995. The uninformed account attributed clay hardening to this fire, whereas the informed account cited pre-fire firing and worn edges beneath soot. This is one additional qualitative case, not a stable causal finding.', '',
             'Capture correction: Arena renders unfenced JSON as Markdown, splitting paragraphs and removing escaped punctuation. Full visible response bubbles are now recorded. A single-field speaker wrapper can be decoded deterministically from its complete visible content; judge routing still requires valid JSON. Two initial capture errors in this attempt were corrected from the same pages without any model resend; the earlier captures/events remain in the records. Visible text is not asserted to be byte-identical to the original generation stream. Original-run cutoff files remain unchanged; its format-failure classifications may include display parsing artifacts and need a separate retrospective audit.', '',
             '| Trajectory | Status | Asks | Sends / replies | Terminal |', '|---|---|---:|---:|---|']
    for r in rows:
        if r['sends']:
            lines.append(f"| {r['id']} | {r['status']} | {r['asks']} | {r['sends']} / {r['replies']} | {(r['terminal'] or {}).get('pick','pending')} |")
    lines += ['', 'See [continuation protocol](RESUME_PROTOCOL.md). Original [cutoff](RESULTS.md) is separate; do not pool repeated configurations or select preferable attempts.']
    (ROOT / 'RESUME_RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k != 'rows'}))

if __name__ == '__main__':
    main()
