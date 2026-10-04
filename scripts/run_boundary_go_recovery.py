"""Two explicitly amended recoveries; preserve all original replies and failures."""
import argparse
import hashlib
import json
from pathlib import Path
import run_boundary_go_v2 as base
from opencode_go_client_v2 import now, session_id

OLD = base.RUN
RUN = base.BASE / 'runs/opencode_go_20261004_recovery01'
FROZEN = 'EB01_D1_symmetric_frozen'
REVERSE = 'EB01_D2_boundary_aware'
ORIGINAL_NEXT = base.next_turn
ORIGINAL_COST = base.cost
ORIGINAL_STATUS = base.status


def parse(text):
    # Accept literal JSON string control characters deterministically. No prose
    # extraction, inference from reasoning, missing-field synthesis or LLM repair.
    text = text.strip()
    if text.startswith('```json\n') and text.endswith('```'):
        text = text[8:-3].strip()
    return json.loads(text, strict=False)


def next_turn(record, bundle):
    if record['id'] != REVERSE:
        return ORIGINAL_NEXT(record, bundle)
    valid = [m for m in record['messages'] if m.get('reply')]
    if not valid:
        return 'J', 1, bundle['role_initial_prompts'][REVERSE]['J']
    role, index, prompt = ORIGINAL_NEXT(record, bundle)
    if role != 'J' and not any(m['role'] == role for m in valid):
        initialization = bundle['role_initial_prompts'][REVERSE][role]
        prefix = initialization.split('There is no opening account.')[0].rstrip()
        prompt = (prefix + '\n\nThere is no opening account or separate READY turn. '
                  'Answer the following first question now. Put the response JSON in your '
                  'visible final answer, not only in a reasoning field.\n\n' + prompt)
    return role, index, prompt


def cost(receipt):
    return 0.0 if receipt.get('inherited_original_receipt') else ORIGINAL_COST(receipt)


def status(records, total_cost, state):
    value = ORIGINAL_STATUS(records, total_cost,
        'BOTH_RECOVERIES_ATTEMPTED' if state == 'ALL_FOUR_ATTEMPTED' else state)
    value['planned'] = 2
    value['amended_recovery'] = True
    value['usage_scope'] = 'new requests only; inherited usage excluded'
    base.dump(RUN / 'status.json', value)
    return value


def prepare():
    if RUN.exists():
        raise SystemExit('Preserve recovery directory')
    b = base.read(OLD / 'bundle.json')
    b['trajectories'] = [t for t in b['trajectories'] if t['id'] in (FROZEN, REVERSE)]
    b['role_initial_prompts'] = {i: b['role_initial_prompts'][i] for i in (FROZEN, REVERSE)}
    b['recovery_amendment'] = {
        'previous_run': OLD.name, 'authorized_utc': now(),
        'parser': 'json.loads(strict=False), whitespace/single JSON fence only',
        'frozen': 'inherit complete original messages; accept literal controls in B reply; continue without regeneration',
        'reverse': 'fresh sessions; Judge first; fold private speaker initialization into first question; no READY requests',
        'same_sampling': True, 'no_reasoning_promoted': True,
        'claim_boundary': 'failure-selected amended recovery; separate from original and published two endpoints'}
    (RUN / 'trajectories').mkdir(parents=True)
    (RUN / 'receipts').mkdir()
    base.dump(RUN / 'bundle.json', b)
    records = {}
    for t in b['trajectories']:
        if t['id'] == FROZEN:
            r = base.read(OLD / 'trajectories' / (FROZEN + '.json'))
            for m in r['messages']:
                receipt = base.read(OLD / m['receipt'])
                receipt['inherited_original_receipt'] = True
                base.dump(RUN / m['receipt'], receipt)
            last = r['messages'][-1]
            assert not last['reply'] and last['role'] == 'B'
            receipt = base.read(OLD / last['receipt'])
            assert receipt['finish_reason'] not in ('length', 'max_tokens')
            value = parse(receipt['text'])
            base.validate(value, 'B', last['question_index'])
            last.update({'reply': True, 'parsed': value, 'setup': False,
                         'recovery_parse': 'literal controls accepted; raw text unchanged'})
            r['histories']['B'] += [{'role': 'user', 'content': last['prompt']}, receipt['assistant_message']]
            r['status'] = 'reply_captured'
            r['events'].append({'type': 'authorized_parser_amendment', 'at': now(),
                'original_failure_preserved': True, 'no_provider_regeneration': True})
            r['inherited_messages'] = len(r['messages'])
        else:
            r = {**t, 'status': 'not_started', 'asks': 0, 'messages': [], 'events': [],
                 'histories': {x: [] for x in ('A', 'B', 'J')},
                 'session_ids': {x: session_id() for x in ('A', 'B', 'J')},
                 'inherited_messages': 0}
        base.dump(RUN / 'trajectories' / (t['id'] + '.json'), r)
        records[t['id']] = r
    base.dump(RUN / 'smoke.json', {'passed': True, 'inherited_qualification': OLD.name,
        'reason': 'same exact models, transport, sampling; no redundant qualification calls'})
    base.dump(RUN / 'freeze.json', {
        'bundle_sha256': hashlib.sha256((RUN / 'bundle.json').read_bytes()).hexdigest(),
        'recovery_runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'base_runner_sha256': hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest(),
        'transport_sha256': hashlib.sha256(Path(base.__file__).with_name('opencode_go_client_v2.py').read_bytes()).hexdigest(),
        'created_utc': now(), 'new_model_calls_at_freeze': 0})
    status(records, 0, 'PREPARED')
    print(json.dumps({'state': 'PREPARED', 'planned': 2, 'new_model_calls': 0}))


def execute(key_stdin):
    freeze = base.read(RUN / 'freeze.json')
    for key, path in [('recovery_runner_sha256', Path(__file__)),
                      ('base_runner_sha256', Path(base.__file__)),
                      ('transport_sha256', Path(base.__file__).with_name('opencode_go_client_v2.py'))]:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == freeze[key]
    base.RUN = RUN
    base.parse = parse
    base.next_turn = next_turn
    base.cost = cost
    base.status = status
    base.execute(key_stdin)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--key-stdin', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    if args.execute:
        execute(args.key_stdin)
