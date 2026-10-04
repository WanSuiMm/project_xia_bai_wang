"""Allowlisted fresh Frozen cutoff export (--export), public-only audit otherwise."""
import argparse
import hashlib
import json
from pathlib import Path
from run_boundary_go_case2 import next_turn, parse
from run_boundary_go_v2 import validate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'epistemic_boundary_mimicry'
RUN = BASE / 'runs/opencode_go_20261004_fresh_frozen01'
OUT = BASE / 'published_runs/go_fresh_frozen_cutoff_20261004'
IDENT = 'EB03_D1_symmetric_frozen'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def export():
    if OUT.exists() and list(OUT.glob('*.json')):
        raise SystemExit('Preserve existing snapshot')
    b = read(RUN / 'bundle.json')
    r = read(RUN / 'trajectories' / (IDENT + '.json'))
    assert r['status'] == 'protocol_failure' and r.get('terminal') is None
    freeze = read(RUN / 'freeze.json')
    for key, path in [('bundle_sha256', RUN / 'bundle.json'),
                      ('sources_sha256', RUN / 'sources_frozen.json'),
                      ('seats_sha256', RUN / 'seats_frozen.json')]:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == freeze[key]
    OUT.mkdir(parents=True, exist_ok=True)
    case = b['cases'][0]
    seats = read(RUN / 'seats_frozen.json')
    sources = read(RUN / 'sources_frozen.json')
    write(OUT / 'bundle.json', {
        'public_context': case['public_context'], 'sources': case['sources'],
        'role_initial_prompts': b['role_initial_prompts'], 'configuration': b['configuration'],
        'randomization': {'generation_seeds': sources['generation_seeds'],
            'seat_seed': seats['seat_seed'], 'seat_source_ids': seats['seat_source_ids'],
            'target_draw_seed': b['target_draw_seed'],
            'target_draw_after_source_and_seat_freeze': b['target_draw_after_source_and_seat_freeze'],
            'judge_informed_of_random_label': False},
        'claim_boundary': b['claim_boundary']})
    projected = {k: r[k] for k in ('id', 'case_id', 'condition', 'speaker_model', 'judge_model',
        'target_seat', 'target_source_id', 'other_source_id', 'status', 'asks')}
    projected.update({'terminal': None, 'correct': None, 'failure': r['events'][-1]['detail'], 'messages': []})
    for m in r['messages']:
        receipt = read(RUN / m['receipt'])
        assert receipt.get('text') == m.get('raw')
        projected['messages'].append({
            **{k: m.get(k) for k in ('role', 'question_index', 'prompt', 'model', 'raw', 'parsed', 'setup', 'reply')},
            'returned_model': receipt.get('returned_model'), 'finish_reason': receipt.get('finish_reason'),
            'http_status': receipt.get('http_status'), 'usage': receipt.get('usage')})
    write(OUT / (IDENT + '.json'), projected)
    write(OUT / 'manifest.json', {'files': [{'file': p.name,
        'sha256_lf_utf8': hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()}
        for p in sorted(OUT.glob('*.json'))],
        'projection': 'Exact visible text including invalid final JSON; excludes private reasoning, credentials and account/session/machine metadata.'})


def audit():
    errors = []
    for entry in read(OUT / 'manifest.json')['files']:
        if hashlib.sha256((OUT / entry['file']).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != entry['sha256_lf_utf8']:
            errors.append('hash:' + entry['file'])
    b = read(OUT / 'bundle.json')
    r = read(OUT / (IDENT + '.json'))
    byid = {s['source_id']: s for s in b['sources']}
    for s in b['sources']:
        if hashlib.sha256(s['source_text'].encode()).hexdigest() != s['source_sha256']:
            errors.append('source_hash')
    assignments = b['randomization']['seat_source_ids']
    p = b['role_initial_prompts'][IDENT]
    normalized = []
    for seat in ('A', 'B'):
        own = byid[assignments[seat]]['source_text']
        other = byid[assignments['B' if seat == 'A' else 'A']]['source_text']
        if own not in p[seat] or other in p[seat] or own in p['J']:
            errors.append('source_isolation')
        normalized.append(p[seat].replace(own, '<SOURCE>').replace('speaker ' + seat, 'speaker <SEAT>'))
    if normalized[0] != normalized[1] or assignments[r['target_seat']] != r['target_source_id']:
        errors.append('policy_or_target')
    replay = {**r, 'messages': [], 'asks': 0}
    failed = 0
    for i, m in enumerate(r['messages']):
        if (m['role'], m['question_index'], m['prompt']) != next_turn(replay, b):
            errors.append('routing:' + str(i))
        if m['returned_model'] != m['model'] or m['http_status'] != 200:
            errors.append('provider:' + str(i))
        if not m['reply']:
            failed += 1
            try:
                parse(m['raw'])
                errors.append('failure_not_reproduced')
            except ValueError:
                pass
            if i != len(r['messages']) - 1 or m['role'] != 'J':
                errors.append('unexpected_failure_position')
            continue
        v = parse(m['raw'])
        validate(v, m['role'], m['question_index'], first_judge=m['role'] == 'J' and not replay['asks'])
        if v != m['parsed'] or m['setup']:
            errors.append('reply:' + str(i))
        if m['role'] == 'J' and v['action'] == 'ASK':
            replay['asks'] += 1
        replay['messages'].append(m)
    if failed != 1 or replay['asks'] != r['asks'] or r['terminal'] is not None or r['correct'] is not None:
        errors.append('cutoff')
    print(json.dumps({'audit_errors': errors, 'status': r['status'], 'completed_asks': r['asks'],
        'valid_replies': len(replay['messages']), 'invalid_replies': failed, 'endpoint': False}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    if args.export:
        export()
    audit()
