"""Verify hashes, exact relays and scores using the public Go snapshot only."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / 'epistemic_boundary_mimicry/published_runs/go_two_completed_20261004'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    errors = []
    for entry in read(SNAP / 'manifest.json')['files']:
        if hashlib.sha256((SNAP / entry['file']).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != entry['sha256_lf_utf8']:
            errors.append('hash:' + entry['file'])
    b = read(SNAP / 'bundle.json')
    if hashlib.sha256(b['source']['source_text'].encode()).hexdigest() != b['source']['source_sha256']:
        errors.append('source_hash')
    rows = []
    for path in sorted(SNAP.glob('EB01_*.json')):
        r = read(path)
        seen = []
        asks = 0
        for m in r['messages']:
            if json.loads(m['raw']) != m['parsed'] or m['returned_model'] != m['model']:
                errors.append(r['id'] + ':reply_or_model')
            if not any(x['role'] == m['role'] for x in seen):
                expected = b['role_initial_prompts'][r['id']][m['role']]
                if m['prompt'] != expected:
                    errors.append(r['id'] + ':initial_prompt')
            elif m['role'] in ('A', 'B'):
                j = [x for x in seen if x['role'] == 'J'][-1]
                expected = ('Judge asks speaker ' + m['role'] + ':\n' + j['parsed']['question']
                    + '\n\nAnswer in the same fictional game. Return only {"reply":"your natural-language response"}.')
                if m['prompt'] != expected:
                    errors.append(r['id'] + ':speaker_relay')
            else:
                last = [x for x in seen if x['role'] == 'J'][-1]
                answers = [x for x in seen if x['role'] != 'J' and x['question_index'] == last['question_index']]
                targets = ('A', 'B') if last['parsed']['target'] == 'BOTH' else (last['parsed']['target'],)
                if [x['role'] for x in answers] != list(targets):
                    errors.append(r['id'] + ':targets')
                expected = '\n\n'.join('Speaker ' + x['role'] + ':\n' + x['parsed']['reply'] for x in answers)
                expected += ('\n\nHost relay only; no truth check is available. You have used ' + str(asks)
                    + ' ASK actions. There is no fixed question-count limit. Choose your next ASK, STOP, or ABSTAIN freely. Return the same action JSON format.')
                if m['prompt'] != expected:
                    errors.append(r['id'] + ':judge_relay')
            if m['role'] == 'J':
                if not asks and m['parsed']['action'] != 'ASK':
                    errors.append(r['id'] + ':first_ask')
                asks += m['parsed']['action'] == 'ASK'
            seen.append(m)
        terminal = [m for m in seen if m['role'] == 'J'][-1]['parsed']
        if terminal != r['terminal'] or asks != r['asks'] or r['correct'] != (terminal['pick'] == r['target_seat']):
            errors.append(r['id'] + ':terminal_score')
        rows.append({k: r[k] for k in ('id', 'asks', 'correct', 'terminal')})
    print(json.dumps({'audit_errors': errors, 'completed': len(rows),
        'correct': sum(r['correct'] for r in rows), 'independent_dossiers': 1}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
