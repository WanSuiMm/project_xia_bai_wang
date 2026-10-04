"""Second frozen dossier, same four slots, uniform Judge-first protocol."""
import argparse
import hashlib
import json
from pathlib import Path
import run_boundary_go_v2 as base
from opencode_go_client_v2 import now, session_id
from run_boundary_go_recovery import parse

RUN = base.BASE / 'runs/opencode_go_20261004_case02_four01'
SOURCE = base.BASE / 'runs/arena_20261004_boundary01'
QUALIFIED = base.RUN
ORIGINAL_NEXT = base.next_turn
IDS = ('EB02_D1_boundary_aware', 'EB02_D1_symmetric_frozen',
       'EB02_D1_strong', 'EB02_D2_boundary_aware')


def next_turn(record, bundle):
    valid = [m for m in record['messages'] if m.get('reply')]
    if not valid:
        return 'J', 1, bundle['role_initial_prompts'][record['id']]['J']
    role, index, prompt = ORIGINAL_NEXT(record, bundle)
    if role != 'J' and not any(m['role'] == role for m in valid):
        initialization = bundle['role_initial_prompts'][record['id']][role]
        prefix = initialization.split('There is no opening account.')[0].rstrip()
        prompt = (prefix + '\n\nThere is no opening account or separate READY turn. '
                  'Answer the following first question now. Put the response JSON in your '
                  'visible final answer, not only in a reasoning field.\n\n' + prompt)
    return role, index, prompt


def prepare():
    if RUN.exists():
        raise SystemExit('Preserve existing run')
    original = base.read(SOURCE / 'bundle.json')
    assert hashlib.sha256((SOURCE / 'bundle.json').read_bytes()).hexdigest() == base.read(SOURCE / 'freeze.json')['bundle_sha256']
    assert base.read(QUALIFIED / 'smoke.json')['passed']
    bundle = json.loads(json.dumps(original))
    bundle['trajectories'] = [t for t in bundle['trajectories'] if t['id'] in IDS]
    assert tuple(t['id'] for t in bundle['trajectories']) == IDS
    mapping = {'claude-sonnet-5-high': 'qwen3.8-max', 'gemini-3.1-pro-preview': 'glm-5.3'}
    for t in bundle['trajectories']:
        t['speaker_model'] = mapping[t['speaker_model']]
        t['judge_model'] = mapping[t['judge_model']]
    bundle['cases'] = [c for c in bundle['cases'] if c['case_id'] == 'EB02']
    bundle['role_initial_prompts'] = {i: bundle['role_initial_prompts'][i] for i in IDS}
    bundle['migration'] = {
        'scope': 'second existing dossier; same four condition/direction slots, no extra first-case slots',
        'claim_boundary': 'second-case follow-up, not the proposed 36-trajectory confirmatory study',
        'max_tokens': 32768, 'temperature': 0.5, 'reasoning': 'deployment default',
        'tools': False, 'stream': False, 'max_asks': None, 'opening': False,
        'initialization': 'Judge first; private speaker initialization combined with first requested answer',
        'parser': 'strict=False JSON controls; no prose extraction or inferred fields',
        'no_semantic_retry': True, 'no_model_fallback': True,
        'operational_new_usage_stop_before_next_request_usd': 1.9,
        'execution_order': 'original frozen bundle order filtered to the four authorized slots',
        'fresh_sessions': True, 'authorized_utc': now()}
    (RUN / 'trajectories').mkdir(parents=True)
    (RUN / 'receipts').mkdir()
    base.dump(RUN / 'bundle.json', bundle)
    for t in bundle['trajectories']:
        base.dump(RUN / 'trajectories' / (t['id'] + '.json'), {
            **t, 'status': 'not_started', 'asks': 0, 'messages': [], 'events': [],
            'histories': {r: [] for r in ('A', 'B', 'J')},
            'session_ids': {r: session_id() for r in ('A', 'B', 'J')}})
    base.dump(RUN / 'smoke.json', {'passed': True, 'inherited_qualification': QUALIFIED.name,
        'reason': 'exact same transport/models/sampling; no redundant provider qualification'})
    paths = {'bundle_sha256': RUN / 'bundle.json', 'source_bundle_sha256': SOURCE / 'bundle.json',
        'runner_sha256': Path(__file__), 'base_runner_sha256': Path(base.__file__),
        'parser_module_sha256': Path(__file__).with_name('run_boundary_go_recovery.py'),
        'transport_sha256': Path(__file__).with_name('opencode_go_client_v2.py')}
    base.dump(RUN / 'freeze.json', {**{k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
        'created_utc': now(), 'new_model_calls_at_freeze': 0})
    base.RUN = RUN
    records = {t['id']: base.read(RUN / 'trajectories' / (t['id'] + '.json')) for t in bundle['trajectories']}
    base.status(records, 0, 'PREPARED')
    print(json.dumps({'state': 'PREPARED', 'case': 'EB02', 'planned': 4, 'new_model_calls': 0}))


def execute(key_stdin):
    freeze = base.read(RUN / 'freeze.json')
    for key, path in [('source_bundle_sha256', SOURCE / 'bundle.json'), ('runner_sha256', Path(__file__)),
                      ('base_runner_sha256', Path(base.__file__)),
                      ('parser_module_sha256', Path(__file__).with_name('run_boundary_go_recovery.py')),
                      ('transport_sha256', Path(__file__).with_name('opencode_go_client_v2.py'))]:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == freeze[key]
    base.RUN = RUN
    base.next_turn = next_turn
    base.parse = parse
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
