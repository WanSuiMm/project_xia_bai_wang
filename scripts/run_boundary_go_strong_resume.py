"""Resume only EB02 Strong after a documented HTTP 429; preserve the cutoff."""
import argparse
import hashlib
import json
from pathlib import Path
import run_boundary_go_case2 as case2
from opencode_go_client_v2 import now

base = case2.base
OLD = case2.RUN
RUN = base.BASE / 'runs/opencode_go_20261004_case02_strong_resume01'
IDENT = 'EB02_D1_strong'
ORIGINAL_COST = base.cost
ORIGINAL_STATUS = base.status


def cost(receipt):
    return 0.0 if receipt.get('inherited_original_receipt') else ORIGINAL_COST(receipt)


def status(records, total_cost, state):
    result = ORIGINAL_STATUS(records, total_cost,
        'STRONG_ATTEMPT_FINISHED' if state == 'ALL_FOUR_ATTEMPTED' else state)
    result['planned'] = 1
    result['usage_scope'] = 'new requests only'
    result['resumed_after_429'] = True
    base.dump(RUN / 'status.json', result)
    return result


def prepare():
    if RUN.exists():
        raise SystemExit('Preserve existing recovery')
    rpath = OLD / 'trajectories' / (IDENT + '.json')
    record = base.read(rpath)
    last = record['messages'][-1]
    receipt = base.read(OLD / last['receipt'])
    assert record['status'] == 'platform_failure' and receipt['http_status'] == 429
    assert not last['reply']
    bundle = base.read(OLD / 'bundle.json')
    bundle['trajectories'] = [t for t in bundle['trajectories'] if t['id'] == IDENT]
    bundle['role_initial_prompts'] = {IDENT: bundle['role_initial_prompts'][IDENT]}
    bundle['resume'] = {'previous_run': OLD.name, 'reason': 'user-authorized completion after GoUsageLimitError',
        'same_role_histories': True, 'same_session_ids': True, 'no_answer_regeneration': True,
        'other_slots_not_dispatched': True, 'authorized_utc': now()}
    assert case2.next_turn(record, bundle) == (last['role'], last['question_index'], last['prompt'])
    (RUN / 'trajectories').mkdir(parents=True)
    (RUN / 'receipts').mkdir()
    for m in record['messages']:
        inherited = base.read(OLD / m['receipt'])
        inherited['inherited_original_receipt'] = True
        base.dump(RUN / m['receipt'], inherited)
    record['status'] = 'reply_captured'
    record['inherited_messages'] = len(record['messages'])
    record['events'].append({'type': 'authorized_429_resume', 'at': now(),
        'original_failed_request_retained': True, 'prior_visible_answers_unchanged': True})
    base.dump(RUN / 'trajectories' / (IDENT + '.json'), record)
    base.dump(RUN / 'bundle.json', bundle)
    base.dump(RUN / 'smoke.json', {'passed': True, 'inherited_qualification': OLD.name,
        'reason': 'same transport, models, protocol and native histories; retry actual missing request only'})
    paths = {'bundle_sha256': RUN / 'bundle.json', 'runner_sha256': Path(__file__),
        'case2_runner_sha256': Path(case2.__file__), 'base_runner_sha256': Path(base.__file__),
        'transport_sha256': Path(__file__).with_name('opencode_go_client_v2.py'),
        'parser_module_sha256': Path(__file__).with_name('run_boundary_go_recovery.py'),
        'original_record_sha256': rpath}
    base.dump(RUN / 'freeze.json', {**{k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
        'created_utc': now(), 'new_model_calls_at_freeze': 0})
    base.RUN = RUN
    status({IDENT: record}, 0, 'PREPARED')
    print(json.dumps({'state': 'PREPARED', 'prior_asks': record['asks'], 'next_role': last['role'], 'new_calls': 0}))


def execute(key_stdin):
    freeze = base.read(RUN / 'freeze.json')
    for key, path in [('runner_sha256', Path(__file__)), ('case2_runner_sha256', Path(case2.__file__)),
                      ('base_runner_sha256', Path(base.__file__)),
                      ('transport_sha256', Path(__file__).with_name('opencode_go_client_v2.py')),
                      ('parser_module_sha256', Path(__file__).with_name('run_boundary_go_recovery.py')),
                      ('original_record_sha256', OLD / 'trajectories' / (IDENT + '.json'))]:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == freeze[key]
    base.RUN = RUN
    base.parse = case2.parse
    base.next_turn = case2.next_turn
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
