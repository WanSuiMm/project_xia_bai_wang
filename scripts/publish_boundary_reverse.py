"""Allowlisted reverse endpoint export (--export), or public-only audit."""
import argparse
import hashlib
import json
from pathlib import Path
from run_boundary_go_recovery import next_turn, parse
from run_boundary_go_v2 import validate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'epistemic_boundary_mimicry'
OUT = BASE / 'published_runs/go_reverse_recovery_20261004'
IDENT = 'EB01_D2_boundary_aware'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def export():
    if OUT.exists() and list(OUT.glob('*.json')):
        raise SystemExit('Preserve existing snapshot')
    run = BASE / 'runs/opencode_go_20261004_recovery01'
    original = BASE / 'runs/opencode_go_20261004_first_four02'
    r = read(run / 'trajectories' / (IDENT + '.json'))
    old = read(original / 'trajectories' / (IDENT + '.json'))
    b = read(run / 'bundle.json')
    assert r['status'] == 'completed' and r['terminal']['action'] == 'STOP'
    case = next(c for c in b['cases'] if c['case_id'] == r['case_id'])
    source = next(s for s in case['sources'] if s['source_id'] == r['target_source_id'])
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / 'bundle.json', {
        'public_context': case['public_context'],
        'source': {k: source[k] for k in ('source_id', 'source_title', 'source_text', 'source_sha256')},
        'role_initial_prompts': {IDENT: b['role_initial_prompts'][IDENT]},
        'configuration': {'max_tokens': 32768, 'temperature': 0.5, 'reasoning': 'deployment default',
            'opening': False, 'max_asks': None, 'host_truth': False, 'tools': False},
        'amendment': 'Fresh histories; Judge first; private initialization combined with first requested Speaker answer. No READY calls. strict=False JSON control decoding.',
        'original_failure': {'status': old['status'], 'asks': old['asks'],
            'role': old['messages'][-1]['role'], 'visible_raw': old['messages'][-1]['raw'],
            'reason': old['events'][-1]['detail'], 'no_reasoning_promoted': True}})
    projected = {k: r[k] for k in ('id', 'case_id', 'condition', 'speaker_model', 'judge_model',
        'target_seat', 'target_source_id', 'knower', 'status', 'asks', 'terminal', 'correct', 'inherited_messages')}
    projected['messages'] = []
    for m in r['messages']:
        assert m['reply']
        receipt = read(run / m['receipt'])
        assert receipt['text'] == m['raw']
        projected['messages'].append({
            **{k: m[k] for k in ('role', 'question_index', 'prompt', 'model', 'raw', 'parsed', 'setup')},
            'returned_model': receipt['returned_model'], 'finish_reason': receipt['finish_reason'],
            'usage': receipt['usage']})
    write(OUT / (IDENT + '.json'), projected)
    write(OUT / 'manifest.json', {'files': [{'file': p.name,
        'sha256_lf_utf8': hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()}
        for p in sorted(OUT.glob('*.json'))],
        'projection': 'Exact visible prompts/replies and used source only; no hidden reasoning or private deployment fields.'})


def audit():
    errors = []
    for entry in read(OUT / 'manifest.json')['files']:
        if hashlib.sha256((OUT / entry['file']).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != entry['sha256_lf_utf8']:
            errors.append('hash:' + entry['file'])
    b = read(OUT / 'bundle.json')
    if hashlib.sha256(b['source']['source_text'].encode()).hexdigest() != b['source']['source_sha256']:
        errors.append('source_hash')
    r = read(OUT / (IDENT + '.json'))
    replay = {**r, 'messages': [], 'asks': 0}
    for i, m in enumerate(r['messages']):
        if (m['role'], m['question_index'], m['prompt']) != next_turn(replay, b):
            errors.append('routing:' + str(i))
        value = parse(m['raw'])
        validate(value, m['role'], m['question_index'], first_judge=m['role'] == 'J' and not replay['asks'])
        if value != m['parsed'] or m['returned_model'] != m['model'] or m['finish_reason'] in ('length', 'max_tokens'):
            errors.append('reply:' + str(i))
        if m['setup']:
            errors.append('unexpected_ready')
        if m['role'] == 'J' and value['action'] == 'ASK':
            replay['asks'] += 1
        replay['messages'].append({**m, 'reply': True})
    terminal = [m for m in r['messages'] if m['role'] == 'J'][-1]['parsed']
    if (terminal != r['terminal'] or terminal['action'] != 'STOP'
            or r['correct'] != (terminal['pick'] == r['target_seat']) or replay['asks'] != r['asks']
            or r['inherited_messages'] != 0):
        errors.append('terminal')
    print(json.dumps({'audit_errors': errors, 'asks': r['asks'], 'pick': terminal['pick'],
        'target': r['target_seat'], 'confidence': terminal['confidence'], 'correct': r['correct']}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    if args.export:
        export()
    audit()
