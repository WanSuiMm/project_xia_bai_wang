"""Allowlisted Frozen export (--export), or public-only audit (default)."""
import argparse
import hashlib
import json
from pathlib import Path
from run_boundary_go_v2 import next_turn, validate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'epistemic_boundary_mimicry'
OUT = BASE / 'published_runs/go_frozen_recovery_20261004'
IDENT = 'EB01_D1_symmetric_frozen'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def inherited_hash(message):
    payload = {k: message.get(k) for k in ('role', 'question_index', 'prompt', 'model', 'raw')}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def export():
    if OUT.exists() and list(OUT.glob('*.json')):
        raise SystemExit('Preserve existing snapshot')
    run = BASE / 'runs/opencode_go_20261004_recovery01'
    original = BASE / 'runs/opencode_go_20261004_first_four02'
    r = read(run / 'trajectories' / (IDENT + '.json'))
    old = read(original / 'trajectories' / (IDENT + '.json'))
    b = read(run / 'bundle.json')
    assert r['status'] == 'completed' and r['terminal']['action'] == 'ABSTAIN'
    case = next(c for c in b['cases'] if c['case_id'] == r['case_id'])
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / 'bundle.json', {
        'public_context': case['public_context'],
        'sources': [{k: s[k] for k in ('source_id', 'source_title', 'source_text', 'source_sha256')}
                    for s in case['sources'] if s['source_id'] in (r['target_source_id'], r['other_source_id'])],
        'role_initial_prompts': {IDENT: b['role_initial_prompts'][IDENT]},
        'configuration': {'max_tokens': 32768, 'temperature': 0.5, 'reasoning': 'deployment default',
            'opening': False, 'max_asks': None, 'host_truth': False, 'tools': False},
        'amendment': 'Decode literal JSON string controls with strict=False; no text edits or regeneration.',
        'original_failure': {'status': old['status'], 'asks': old['asks'],
            'role': old['messages'][-1]['role'], 'reason': old['events'][-1]['detail']},
        'inherited_message_hashes': [inherited_hash(m) for m in old['messages']]})
    projected = {k: r[k] for k in ('id', 'case_id', 'condition', 'speaker_model', 'judge_model',
        'target_seat', 'target_source_id', 'other_source_id', 'status', 'asks', 'terminal', 'correct', 'inherited_messages')}
    projected['messages'] = []
    for i, m in enumerate(r['messages']):
        assert m['reply']
        receipt = read(run / m['receipt'])
        assert receipt['text'] == m['raw']
        projected['messages'].append({
            **{k: m[k] for k in ('role', 'question_index', 'prompt', 'model', 'raw', 'parsed', 'setup')},
            'inherited': i < r['inherited_messages'],
            'parser_amended': bool(m.get('recovery_parse')),
            'returned_model': receipt['returned_model'], 'finish_reason': receipt['finish_reason'],
            'usage': receipt['usage']})
    write(OUT / (IDENT + '.json'), projected)
    write(OUT / 'manifest.json', {'files': [{'file': p.name,
        'sha256_lf_utf8': hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()}
        for p in sorted(OUT.glob('*.json'))],
        'projection': 'Exact visible prompts/replies and used sources only; no hidden reasoning or private deployment fields.'})


def audit():
    errors = []
    for entry in read(OUT / 'manifest.json')['files']:
        if hashlib.sha256((OUT / entry['file']).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != entry['sha256_lf_utf8']:
            errors.append('hash:' + entry['file'])
    b = read(OUT / 'bundle.json')
    for s in b['sources']:
        if hashlib.sha256(s['source_text'].encode()).hexdigest() != s['source_sha256']:
            errors.append('source_hash')
    r = read(OUT / (IDENT + '.json'))
    for i, digest in enumerate(b['inherited_message_hashes']):
        if inherited_hash(r['messages'][i]) != digest:
            errors.append('inherited:' + str(i))
    replay = {**r, 'messages': [], 'asks': 0}
    for i, m in enumerate(r['messages']):
        expected = next_turn(replay, b)
        if (m['role'], m['question_index'], m['prompt']) != expected:
            errors.append('routing:' + str(i))
        value = json.loads(m['raw'], strict=False)
        validate(value, m['role'], m['question_index'], first_judge=m['role'] == 'J' and not replay['asks'])
        if value != m['parsed'] or m['returned_model'] != m['model'] or m['finish_reason'] in ('length', 'max_tokens'):
            errors.append('reply:' + str(i))
        if m['role'] == 'J' and value['action'] == 'ASK':
            replay['asks'] += 1
        replay['messages'].append({**m, 'reply': True})
    terminal = [m for m in r['messages'] if m['role'] == 'J'][-1]['parsed']
    if terminal != r['terminal'] or terminal['action'] != 'ABSTAIN' or r['correct'] is not None or replay['asks'] != r['asks']:
        errors.append('terminal')
    print(json.dumps({'audit_errors': errors, 'action': terminal['action'], 'asks': r['asks'],
        'inherited_messages': r['inherited_messages'], 'new_calls': len(r['messages']) - r['inherited_messages']}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    if args.export:
        export()
    audit()
