"""One authorized missing-quote repair, then resume fresh Frozen without regeneration."""
import argparse
import hashlib
import json
from pathlib import Path
import run_boundary_go_case2 as case2
from opencode_go_client_v2 import now

base = case2.base
OLD = base.BASE / 'runs/opencode_go_20261004_fresh_frozen01'
RUN = base.BASE / 'runs/opencode_go_20261004_fresh_frozen_resume01'
IDENT = 'EB03_D1_symmetric_frozen'
ORIGINAL_COST = base.cost
ORIGINAL_STATUS = base.status


def decode_missing_quote(raw):
    # Only the observed complete ASK object with an unclosed final question
    # string is eligible. Future replies still use the frozen regular parser.
    assert raw.endswith('}') and raw.startswith('{"action":"ASK","target":"BOTH","question":"')
    try:
        case2.parse(raw)
    except json.JSONDecodeError as exc:
        assert exc.msg == 'Unterminated string starting at'
    else:
        raise ValueError('Not the observed failure')
    corrected = raw[:-1] + '"}'
    value = case2.parse(corrected)
    base.validate(value, 'J', 4)
    assert set(value) == {'action', 'target', 'question'}
    assert value['question'] == raw.partition('"question":"')[2][:-1]
    assert len(corrected) == len(raw) + 1
    return value, corrected


def cost(receipt):
    return 0.0 if receipt.get('inherited_original_receipt') else ORIGINAL_COST(receipt)


def status(records, total_cost, state):
    result = ORIGINAL_STATUS(records, total_cost,
        'FROZEN_RESUME_ATTEMPT_FINISHED' if state == 'ALL_FOUR_ATTEMPTED' else state)
    result['planned'] = 1
    result['usage_scope'] = 'new requests only'
    result['one_off_syntax_amendment'] = True
    base.dump(RUN / 'status.json', result)
    return result


def prepare():
    if RUN.exists():
        raise SystemExit('Preserve existing continuation')
    path = OLD / 'trajectories' / (IDENT + '.json')
    r = base.read(path)
    last = r['messages'][-1]
    assert r['status'] == 'protocol_failure' and not last['reply'] and last['role'] == 'J'
    receipt = base.read(OLD / last['receipt'])
    assert receipt['http_status'] == 200 and receipt['finish_reason'] == 'stop'
    value, corrected = decode_missing_quote(last['raw'])
    (RUN / 'trajectories').mkdir(parents=True)
    (RUN / 'receipts').mkdir()
    for m in r['messages']:
        inherited = base.read(OLD / m['receipt'])
        inherited['inherited_original_receipt'] = True
        base.dump(RUN / m['receipt'], inherited)
    last.update({'reply': True, 'parsed': value, 'setup': False,
        'one_off_syntax_repair': {'inserted': 'one closing double quote before final brace',
            'corrected_json': corrected, 'original_raw_sha256': hashlib.sha256(last['raw'].encode()).hexdigest(),
            'question_text_unchanged': True}})
    r['histories']['J'] += [{'role': 'user', 'content': last['prompt']}, receipt['assistant_message']]
    r['asks'] += 1
    r['status'] = 'reply_captured'
    r['inherited_messages'] = len(r['messages'])
    r['events'].append({'type': 'authorized_one_character_syntax_amendment', 'at': now(),
        'original_raw_unchanged': True, 'no_judge_regeneration': True,
        'future_parser_unchanged': True})
    b = base.read(OLD / 'bundle.json')
    b['continuation'] = {'original_run': OLD.name, 'authorized_utc': now(),
        'syntax_amendment': 'one character, observed final ASK only; no future automatic repair',
        'sampling_and_role_histories_preserved': True}
    base.dump(RUN / 'bundle.json', b)
    base.dump(RUN / 'trajectories' / (IDENT + '.json'), r)
    base.dump(RUN / 'smoke.json', {'passed': True, 'inherited_qualification': OLD.name,
        'reason': 'same models and transport, no redundant generations'})
    paths = {'bundle_sha256': RUN / 'bundle.json', 'runner_sha256': Path(__file__),
        'case2_runner_sha256': Path(case2.__file__), 'base_runner_sha256': Path(base.__file__),
        'transport_sha256': Path(__file__).with_name('opencode_go_client_v2.py'),
        'parser_module_sha256': Path(__file__).with_name('run_boundary_go_recovery.py'),
        'original_record_sha256': path}
    base.dump(RUN / 'freeze.json', {**{k: hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()},
        'created_utc': now(), 'new_calls_at_freeze': 0})
    role, index, prompt = case2.next_turn(r,b)
    assert role == 'A' and index == 4 and value['question'] in prompt
    base.RUN = RUN
    status({IDENT:r},0,'PREPARED')
    print(json.dumps({'prepared':True,'asks':r['asks'],'next_role':role,'new_calls':0,'question_unchanged':True}))


def execute(key_stdin):
    f = base.read(RUN / 'freeze.json')
    for k,p in [('runner_sha256',Path(__file__)),('case2_runner_sha256',Path(case2.__file__)),
        ('base_runner_sha256',Path(base.__file__)),
        ('transport_sha256',Path(__file__).with_name('opencode_go_client_v2.py')),
        ('parser_module_sha256',Path(__file__).with_name('run_boundary_go_recovery.py')),
        ('original_record_sha256',OLD/'trajectories'/(IDENT+'.json'))]:
        assert hashlib.sha256(p.read_bytes()).hexdigest()==f[k]
    base.RUN = RUN
    base.parse = case2.parse
    base.next_turn = case2.next_turn
    base.cost = cost
    base.status = status
    base.execute(key_stdin)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--key-stdin',action='store_true')
    args=parser.parse_args()
    if args.prepare:
        prepare()
    if args.execute:
        execute(args.key_stdin)
