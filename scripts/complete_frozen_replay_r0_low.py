"""Bounded five-position completion; preserve all earlier replay attempts."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request
import warnings
from uuid import uuid4

import run_frozen_replay_r0 as original
from continue_frozen_replay_r0_missing import classify_error

PARENT = original.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_84_02'
PRIORS = (PARENT,
    original.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_supplement07_01',
    original.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_supplement06_01')
RUN = original.BASE / 'runs/opencode_go_20261008_frozen_replay_r0_supplement05_low_01'
PROTOCOL = original.BASE / 'replay_r0/SUPPLEMENT05_LOW_PROTOCOL_20261008.md'
TOTAL = 5


def inventory():
    manifest = original.read(PARENT / 'manifest.json')
    valid, history, hashes = set(), {}, {}
    for directory in PRIORS:
        hashes[directory.name] = {}
        for path in sorted(directory.rglob('*')):
            if path.is_file() and (path.name in ('manifest.json', 'freeze.json', 'status.json', 'execution.lock')
                                  or path.parent.name in ('responses', 'dispatches')):
                hashes[directory.name][path.relative_to(directory).as_posix()] = original.sha_file(path)
        receipts = {p.stem: original.read(p) for p in (directory / 'responses').glob('*.json')}
        rows = original.read(directory / 'manifest.json')['requests']
        for row in rows:
            source = row.get('source_request_id', row['request_id'])
            receipt = receipts.get(row['request_id'])
            dispatched = (directory / 'dispatches' / (row['request_id'] + '.json')).exists()
            state = receipt['parse_status'] if receipt else ('dispatched_no_response' if dispatched else 'unstarted')
            history.setdefault(source, []).append({'run': directory.name, 'request_id': row['request_id'],
                                                 'attempt_state': state})
            if receipt and receipt['parse_status'] == 'valid':
                valid.add(source)
    assert len(valid) == 79, 'Eligibility changed; refuse a new or duplicate request'
    selected = [r for r in manifest['requests'] if r['request_id'] not in valid]
    assert len(selected) == TOTAL
    assert all(r['model'] == 'glm-5.3' and r['condition'] == 'blind' for r in selected)
    return manifest, selected, history, hashes


def prepare():
    assert not RUN.exists(), 'Existing run preserved; refuse regeneration'
    original.audit(PARENT)
    manifest, selected, history, hashes = inventory()
    RUN.mkdir(parents=True)
    rows = []
    for source in selected:
        row = dict(source)
        row.update(source_request_id=source['request_id'], request_id='supplement03_' + source['request_id'],
                   prior_attempts=history[source['request_id']], reasoning_effort_requested='low')
        path = RUN / row['prompt_path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((PARENT / source['prompt_path']).read_bytes())
        rows.append(row)
    configuration = dict(manifest['configuration'])
    configuration.update(reasoning='thinking enabled; reasoning_effort low requested', concurrency=1)
    original.dump(RUN / 'manifest.json', {
        'schema_version': 1, 'created_utc': original.now(), 'planned': TOTAL,
        'study': 'Failure-selected changed-configuration engineering completion',
        'parent_run': PARENT.name, 'previous_distinct_valid_positions': 79,
        'primary_analysis_unchanged': True, 'requests': rows, 'configuration': configuration,
        'request_overrides': {'thinking': {'type': 'enabled'}, 'reasoning_effort': 'low'},
        'proxy_honors_reasoning_setting_verified': False,
        'failure_policy': {'automatic_retry': False, 'semantic_repair': False,
                           'stop_on_http_error_or_transport_unknown': True}})
    own = {'manifest.json': original.sha_file(RUN / 'manifest.json')}
    own.update({r['prompt_path']: original.sha_file(RUN / r['prompt_path']) for r in rows})
    original.dump(RUN / 'freeze.json', {'created_utc': original.now(), 'hashes': own,
        'prior_artifact_hashes': hashes, 'protocol_sha256': original.sha_file(PROTOCOL),
        'runner_sha256': original.sha_file(Path(__file__)), 'experimental_requests_at_freeze': 0})
    (RUN / 'responses').mkdir()
    (RUN / 'dispatches').mkdir()
    original.dump(RUN / 'status.json', {'state': 'PREPARED', 'planned': TOTAL,
                  'provider_requests': 0, 'response_count': 0, 'valid': 0})
    audit()


def audit():
    freeze = original.read(RUN / 'freeze.json')
    for name, digest in freeze['hashes'].items():
        assert original.sha_file(RUN / name) == digest, name
    for directory in PRIORS:
        for name, digest in freeze['prior_artifact_hashes'][directory.name].items():
            assert original.sha_file(directory / name) == digest, 'Prior artifact changed'
    assert original.sha_file(PROTOCOL) == freeze['protocol_sha256']
    assert original.sha_file(Path(__file__)) == freeze['runner_sha256']
    parent, selected, history, _ = inventory()
    manifest = original.read(RUN / 'manifest.json')
    assert len(manifest['requests']) == TOTAL
    for row, source in zip(manifest['requests'], selected):
        assert row['source_request_id'] == source['request_id']
        assert row['prior_attempts'] == history[source['request_id']]
        assert (RUN / row['prompt_path']).read_bytes() == (PARENT / source['prompt_path']).read_bytes()
        assert row['prompt_sha256'] == original.sha_file(RUN / row['prompt_path'])
        for field in ('model', 'condition', 'replicate', 'temperature', 'max_tokens'):
            if field in source:
                assert row[field] == source[field]
    assert manifest['request_overrides'] == {'thinking': {'type': 'enabled'}, 'reasoning_effort': 'low'}
    print('PASS: 5 missing positions only; 79 excluded; prior artifacts preserved; low-setting amendment', flush=True)


def call(row, key):
    prompt = (RUN / row['prompt_path']).read_text(encoding='utf-8')
    session = 'xia-r0-completion-' + str(uuid4())
    payload = {'model': row['model'], 'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': row['max_tokens'], 'temperature': .5, 'stream': False,
        'thinking': {'type': 'enabled'}, 'reasoning_effort': 'low'}
    receipt = {k: row[k] for k in ('request_id', 'source_request_id', 'transcript_id', 'model',
               'condition', 'replicate', 'pair_id', 'slot_order', 'prompt_sha256')}
    receipt.update(status='inflight', sent_utc=original.now(), visible_text='', parsed=None,
        parse_status='not_received', finish_reason=None, usage={}, returned_model=None,
        session_id_private=session, reasoning_effort_requested='low',
        changed_configuration_supplement=True, failure_selected_supplement=True)
    started = time.monotonic()
    try:
        request = urllib.request.Request('https://opencode.ai/zen/go/v1/chat/completions',
            data=json.dumps(payload, ensure_ascii=False).encode(), headers={
                'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key,
                'User-Agent': 'XiaBaiWangResearch/1.0', 'x-opencode-session': session})
        with urllib.request.build_opener(original.NoRedirect()).open(request, timeout=600) as response:
            data = json.loads(response.read().decode('utf-8'))
            receipt['http_status'] = response.status
        choice = data['choices'][0]
        receipt.update(status='response_received', returned_model=data.get('model'),
            usage=data.get('usage', {}), finish_reason=choice.get('finish_reason'),
            visible_text=choice['message'].get('content') or '')
        receipt['visible_text'] = receipt['visible_text'].replace(key, '[REDACTED]')
        receipt['parsed'], receipt['parse_status'] = original.parse(receipt['visible_text'], receipt['finish_reason'])
        if receipt['returned_model'] != row['model']:
            receipt.update(parsed=None, parse_status='unexpected_model')
    except urllib.error.HTTPError as exc:
        receipt.update(status='http_error', http_status=exc.code,
                       provider_error_category=classify_error(exc.read()))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        receipt.update(status='transport_unknown', error_type=type(exc).__name__)
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        receipt.update(status='invalid_provider_response', error_type=type(exc).__name__)
    receipt.update(elapsed_seconds=round(time.monotonic() - started, 3), captured_utc=original.now())
    return receipt


def execute():
    audit()
    assert original.read(RUN / 'status.json')['state'] == 'PREPARED'
    assert not list((RUN / 'dispatches').glob('*.json')), 'Existing dispatch; refuse restart'
    key = os.environ.get('OPENCODE_GO_API_KEY', '').strip()
    assert key, 'Credential unavailable; no request sent'
    fd = os.open(RUN / 'execution.lock', os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
    state = {'state': 'RUNNING', 'halt_reason': None}
    original.dump(RUN / 'launch_receipt.private.json', {'pid': os.getpid(),
        'launch_utc': original.now(), 'host': os.environ.get('COMPUTERNAME'),
        'command': 'python -X utf8 -B scripts/complete_frozen_replay_r0_low.py --execute',
        'run_path': str(RUN.resolve()), 'planned_provider_requests': TOTAL})
    def update():
        receipts = [original.read(p) for p in (RUN / 'responses').glob('*.json')]
        value = {**state, 'planned': TOTAL, 'updated_utc': original.now(),
            'provider_requests': len(list((RUN / 'dispatches').glob('*.json'))),
            'response_count': len(receipts), 'valid': sum(r['parse_status'] == 'valid' for r in receipts)}
        original.dump(RUN / 'status.json', value)
        return value
    try:
        update()
        for row in original.read(RUN / 'manifest.json')['requests']:
            output = RUN / 'responses' / (row['request_id'] + '.json')
            dispatch = RUN / 'dispatches' / (row['request_id'] + '.json')
            assert not output.exists() and not dispatch.exists()
            original.dump(dispatch, {'request_id': row['request_id'], 'source_request_id': row['source_request_id'],
                'dispatched_utc': original.now(), 'prompt_sha256': row['prompt_sha256'],
                'reasoning_effort_requested': 'low'})
            update()
            receipt = call(row, key)
            original.dump(output, receipt)
            if receipt['status'] in ('http_error', 'transport_unknown', 'invalid_provider_response'):
                state.update(state='HALTED', halt_reason=receipt['status'],
                    provider_error_category=receipt.get('provider_error_category'))
            value = update()
            print(json.dumps({'received': value['response_count'], 'valid': value['valid'],
                'planned': TOTAL, 'parse_status': receipt['parse_status'], 'status': receipt['status']}), flush=True)
            if state['state'] == 'HALTED':
                break
        if state['state'] != 'HALTED':
            state['state'] = 'ALL_5_ATTEMPTED'
        update()
    except BaseException as exc:
        state.update(state='INTERRUPTED', halt_reason=type(exc).__name__)
        update()
        raise
    finally:
        (RUN / 'execution.lock').unlink(missing_ok=True)


def launch():
    audit()
    assert original.read(RUN / 'status.json')['state'] == 'PREPARED'
    assert not (RUN / 'launcher_receipt.private.json').exists(), 'Already launched; refuse duplication'
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        key = getpass.getpass('New credential (hidden, memory only): ').strip()
    assert key, 'No credential; no request sent'
    environment = dict(os.environ)
    environment['OPENCODE_GO_API_KEY'] = key
    with (RUN / 'worker.stdout.private.log').open('ab', buffering=0) as out, \
         (RUN / 'worker.stderr.private.log').open('ab', buffering=0) as err:
        flags = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == 'nt' else 0
        process = subprocess.Popen([sys.executable, '-X', 'utf8', '-B', str(Path(__file__).resolve()), '--execute'],
            cwd=original.ROOT, env=environment, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            creationflags=flags, start_new_session=os.name != 'nt')
    original.dump(RUN / 'launcher_receipt.private.json', {'worker_pid': process.pid,
        'launched_utc': original.now(), 'detached_worker': True, 'planned_provider_requests': TOTAL})
    print('Detached five-position worker launched; private receipt saved. No credential saved.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare', 'audit', 'launch', 'execute'):
        group.add_argument('--' + name, action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.audit:
        audit()
    elif args.launch:
        launch()
    else:
        execute()


if __name__ == '__main__':
    main()
