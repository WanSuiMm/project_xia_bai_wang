"""Offline frozen-case provenance, initialization isolation and live routing audit."""
import hashlib
import json
from pathlib import Path
import run_boundary_go_case2 as case2


def main():
    read = case2.base.read
    root = case2.RUN
    b = read(root / 'bundle.json')
    original = read(case2.SOURCE / 'bundle.json')
    freeze = read(root / 'freeze.json')
    errors = []
    paths = {'bundle_sha256': root / 'bundle.json', 'source_bundle_sha256': case2.SOURCE / 'bundle.json',
        'runner_sha256': Path(case2.__file__), 'base_runner_sha256': Path(case2.base.__file__),
        'parser_module_sha256': Path(case2.__file__).with_name('run_boundary_go_recovery.py'),
        'transport_sha256': Path(case2.__file__).with_name('opencode_go_client_v2.py')}
    for key, path in paths.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != freeze[key]:
            errors.append('hash:' + key)
    if b['cases'] != [c for c in original['cases'] if c['case_id'] == 'EB02']:
        errors.append('source_changed')
    rows = []
    for t in b['trajectories']:
        ident = t['id']
        if b['role_initial_prompts'][ident] != original['role_initial_prompts'][ident]:
            errors.append(ident + ':initial_instructions_changed')
        fixture = {**t, 'messages': [], 'asks': 0}
        if case2.next_turn(fixture, b) != ('J', 1, b['role_initial_prompts'][ident]['J']):
            errors.append(ident + ':judge_first')
        fixture['messages'] = [{'role': 'J', 'question_index': 1, 'reply': True,
            'parsed': {'action': 'ASK', 'target': 'BOTH', 'question': 'Describe the recorded arrangement.'}}]
        fixture['asks'] = 1
        _, _, initial = case2.next_turn(fixture, b)
        if not initial.startswith(b['role_initial_prompts'][ident]['A'].split('There is no opening account.')[0].rstrip()):
            errors.append(ident + ':private_initialization')
        r = read(root / 'trajectories' / (ident + '.json'))
        replay = {**r, 'messages': [], 'asks': 0}
        histories = {x: [] for x in ('A', 'B', 'J')}
        for i, m in enumerate(r['messages']):
            if (m['role'], m['question_index'], m['prompt']) != case2.next_turn(replay, b):
                errors.append(ident + ':routing:' + str(i))
            if not m.get('receipt'):
                continue
            receipt = read(root / m['receipt'])
            if receipt.get('text') != m.get('raw') or receipt.get('max_tokens') != 32768 or receipt.get('temperature') != .5:
                errors.append(ident + ':receipt')
            if m.get('reply'):
                value = case2.parse(m['raw'])
                case2.base.validate(value, m['role'], m['question_index'], first_judge=m['role'] == 'J' and not replay['asks'])
                if value != m['parsed'] or receipt['returned_model'] != m['model'] or m['setup']:
                    errors.append(ident + ':reply')
                histories[m['role']] += [{'role': 'user', 'content': m['prompt']}, receipt['assistant_message']]
                replay['messages'].append(m)
                if m['role'] == 'J' and value['action'] == 'ASK':
                    replay['asks'] += 1
        if histories != r['histories'] or replay['asks'] != r['asks']:
            errors.append(ident + ':history_or_ask_count')
        if r['status'] == 'completed':
            v = [m for m in replay['messages'] if m['role'] == 'J'][-1]['parsed']
            if v != r['terminal'] or r['correct'] != (v['pick'] == r['target_seat'] if v['action'] == 'STOP' else None):
                errors.append(ident + ':terminal')
        rows.append({'id': ident, 'status': r['status'], 'asks': r['asks']})
    case2.base.dump(root / 'audit.json', {'errors': errors, 'trajectories': rows, 'independent_case_count_this_run': 1})
    print(json.dumps({'audit_errors': errors, 'planned': len(rows), 'completed': sum(r['status'] == 'completed' for r in rows)}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
