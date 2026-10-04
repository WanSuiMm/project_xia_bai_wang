"""Allowlisted second-case three-endpoint export (--export), public audit otherwise."""
import argparse
import hashlib
import json
from pathlib import Path
from run_boundary_go_case2 import next_turn, parse
from run_boundary_go_v2 import validate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'epistemic_boundary_mimicry'
OUT = BASE / 'published_runs/go_case02_three_20261004'
IDS = ('EB02_D1_boundary_aware', 'EB02_D1_symmetric_frozen', 'EB02_D1_strong')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def message_hash(message):
    obj = {k: message.get(k) for k in ('role', 'question_index', 'prompt', 'model', 'raw')}
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def export():
    if OUT.exists() and list(OUT.glob('*.json')):
        raise SystemExit('Preserve existing snapshot')
    original = BASE / 'runs/opencode_go_20261004_case02_four01'
    resumed = BASE / 'runs/opencode_go_20261004_case02_strong_resume01'
    b = read(original / 'bundle.json')
    case = b['cases'][0]
    OUT.mkdir(parents=True, exist_ok=True)
    old_strong = read(original / 'trajectories/EB02_D1_strong.json')
    write(OUT / 'bundle.json', {
        'case_id': case['case_id'], 'public_context': case['public_context'],
        'sources': [{k: s[k] for k in ('source_id', 'source_title', 'source_text', 'source_sha256')}
                    for s in case['sources']],
        'role_initial_prompts': {i: b['role_initial_prompts'][i] for i in IDS},
        'configuration': {k: b['migration'][k] for k in ('max_tokens', 'temperature', 'reasoning',
            'tools', 'stream', 'max_asks', 'opening', 'initialization', 'parser', 'no_semantic_retry', 'no_model_fallback')},
        'strong_original_cutoff': {'status': old_strong['status'], 'asks': old_strong['asks'],
            'failed_role': 'J', 'http_status': 429, 'error_code': 'GoUsageLimitError',
            'message_hashes': [message_hash(m) for m in old_strong['messages']]},
        'excluded': [{'id': 'EB02_D2_boundary_aware', 'status': 'not_started'}],
        'scope': 'three completed slots on one second dossier; no reverse endpoint, no new calls for publication'})
    for ident in IDS:
        run = resumed if ident.endswith('_strong') else original
        r = read(run / 'trajectories' / (ident + '.json'))
        assert r['status'] == 'completed'
        projected = {k: r[k] for k in ('id', 'case_id', 'condition', 'speaker_model', 'judge_model',
            'target_seat', 'target_source_id', 'other_source_id', 'status', 'asks', 'terminal', 'correct')}
        projected['inherited_messages'] = r.get('inherited_messages', 0)
        projected['messages'] = []
        for i, m in enumerate(r['messages']):
            receipt = read(run / m['receipt'])
            assert receipt.get('text') == m.get('raw')
            projected['messages'].append({
                **{k: m.get(k) for k in ('role', 'question_index', 'prompt', 'model', 'raw', 'parsed', 'setup', 'reply')},
                'inherited': i < projected['inherited_messages'],
                'returned_model': receipt.get('returned_model'), 'finish_reason': receipt.get('finish_reason'),
                'http_status': receipt.get('http_status'), 'error_code': receipt.get('error_code'),
                'usage': receipt.get('usage')})
        write(OUT / (ident + '.json'), projected)
    write(OUT / 'manifest.json', {'files': [{'file': p.name,
        'sha256_lf_utf8': hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()}
        for p in sorted(OUT.glob('*.json'))],
        'projection': 'Exact visible prompts/replies and used sources; no hidden reasoning, account/session IDs, auth or machine paths.'})


def audit():
    errors = []
    for entry in read(OUT / 'manifest.json')['files']:
        if hashlib.sha256((OUT / entry['file']).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != entry['sha256_lf_utf8']:
            errors.append('hash:' + entry['file'])
    b = read(OUT / 'bundle.json')
    for s in b['sources']:
        if hashlib.sha256(s['source_text'].encode()).hexdigest() != s['source_sha256']:
            errors.append('source_hash')
    rows = []
    for ident in IDS:
        r = read(OUT / (ident + '.json'))
        replay = {**r, 'messages': [], 'asks': 0}
        for i, m in enumerate(r['messages']):
            if (m['role'], m['question_index'], m['prompt']) != next_turn(replay, b):
                errors.append(ident + ':routing:' + str(i))
            if not m['reply']:
                if ident != 'EB02_D1_strong' or m['http_status'] != 429 or m['error_code'] != 'GoUsageLimitError':
                    errors.append(ident + ':unexpected_failed_request')
                continue
            value = parse(m['raw'])
            validate(value, m['role'], m['question_index'], first_judge=m['role'] == 'J' and not replay['asks'])
            if value != m['parsed'] or m['returned_model'] != m['model'] or m['finish_reason'] in ('length', 'max_tokens') or m['setup']:
                errors.append(ident + ':reply:' + str(i))
            if m['role'] == 'J' and value['action'] == 'ASK':
                replay['asks'] += 1
            replay['messages'].append(m)
        if ident.endswith('_strong'):
            digests = b['strong_original_cutoff']['message_hashes']
            if r['inherited_messages'] != len(digests):
                errors.append('strong:inheritance_count')
            for i, digest in enumerate(digests):
                if message_hash(r['messages'][i]) != digest:
                    errors.append('strong:inherited:' + str(i))
        terminal = [m for m in replay['messages'] if m['role'] == 'J'][-1]['parsed']
        correct = terminal['pick'] == r['target_seat'] if terminal['action'] == 'STOP' else None
        if terminal != r['terminal'] or correct != r['correct'] or replay['asks'] != r['asks']:
            errors.append(ident + ':terminal')
        rows.append({'id': ident, 'asks': r['asks'], 'action': terminal['action'],
                     'target_match': correct, 'confidence': terminal.get('confidence')})
    print(json.dumps({'audit_errors': errors, 'endpoints': rows, 'independent_dossiers_this_snapshot': 1}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    if args.export:
        export()
    audit()
