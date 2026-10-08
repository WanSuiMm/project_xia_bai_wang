"""Continue six missing R0 positions once; classify service errors without leaks."""
from __future__ import annotations

import argparse
import getpass
import io
import os
from pathlib import Path
import urllib.error
import urllib.request
import warnings

import run_frozen_replay_r0 as original


PARENT = original.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_84_02'
PREVIOUS = original.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_supplement07_01'
RUN = original.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_supplement06_01'
PROTOCOL = original.BASE / 'replay_r0/SUPPLEMENT06_PROTOCOL_20261007.md'
TOTAL = 6


def selected_positions():
    parent_status = original.read(PARENT / 'status.json')
    previous_status = original.read(PREVIOUS / 'status.json')
    assert parent_status['state'] == 'ALL_84_ATTEMPTED' and parent_status['valid'] == 77
    assert previous_status['state'] == 'HALTED'
    assert previous_status['provider_requests'] == 2 and previous_status['valid'] == 1
    assert not (PREVIOUS / 'execution.lock').exists()
    manifest = original.read(PARENT / 'manifest.json')
    hashes = {'parent': {}, 'previous': {}}
    for label, directory in (('parent', PARENT), ('previous', PREVIOUS)):
        for name in ('manifest.json', 'freeze.json', 'status.json'):
            hashes[label][name] = original.sha_file(directory / name)
        for file in (directory / 'responses').glob('*.json'):
            relative = file.relative_to(directory).as_posix()
            hashes[label][relative] = original.sha_file(file)
    parent_receipts = {
        row['request_id']: original.read(PARENT / 'responses' / (row['request_id'] + '.json'))
        for row in manifest['requests']
    }
    assert len(parent_receipts) == 84
    valid_ids = {ident for ident, receipt in parent_receipts.items() if receipt['parse_status'] == 'valid'}
    for file in (PREVIOUS / 'responses').glob('*.json'):
        receipt = original.read(file)
        assert receipt['source_request_id'] in parent_receipts
        if receipt['parse_status'] == 'valid':
            valid_ids.add(receipt['source_request_id'])
    assert len(valid_ids) == 78
    selected = [row for row in manifest['requests'] if row['request_id'] not in valid_ids]
    assert len(selected) == TOTAL
    assert all(row['model'] == 'glm-5.3' and row['condition'] == 'blind' for row in selected)
    return manifest, selected, hashes


def prepare():
    assert not RUN.exists(), 'Preserve existing continuation; refuse regeneration'
    original.audit(PARENT)
    parent_manifest, selected, hashes = selected_positions()
    RUN.mkdir(parents=True)
    requests = []
    for source in selected:
        row = dict(source)
        row['source_request_id'] = source['request_id']
        row['request_id'] = 'supplement02_' + source['request_id']
        prompt = RUN / row['prompt_path']
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_bytes((PARENT / source['prompt_path']).read_bytes())
        requests.append(row)
    original.dump(RUN / 'manifest.json', {
        'schema_version': 1, 'created_utc': original.now(),
        'study': 'R0 failure-selected continuation after preserved HTTP 429 cutoff',
        'planned': TOTAL, 'parent_run': PARENT.name, 'previous_supplement': PREVIOUS.name,
        'previous_distinct_valid_positions': 78, 'requests': requests,
        'configuration': parent_manifest['configuration'],
        'failure_policy': parent_manifest['failure_policy'], 'effective_model_workers': 1,
        'primary_analysis_unchanged': True,
    })
    own_hashes = {'manifest.json': original.sha_file(RUN / 'manifest.json')}
    for row in requests:
        own_hashes[row['prompt_path']] = original.sha_file(RUN / row['prompt_path'])
    original.dump(RUN / 'freeze.json', {
        'created_utc': original.now(), 'experimental_requests_at_freeze': 0,
        'hashes': own_hashes, 'prior_run_hashes': hashes,
        'protocol_sha256': original.sha_file(PROTOCOL),
        'continuation_runner_sha256': original.sha_file(Path(__file__)),
        'original_runner_sha256': original.sha_file(Path(original.__file__)),
    })
    (RUN / 'dispatches').mkdir()
    (RUN / 'responses').mkdir()
    original.dump(RUN / 'status.json', {
        'state': 'PREPARED', 'planned': TOTAL, 'provider_requests': 0,
        'response_count': 0, 'valid': 0, 'previous_distinct_valid_positions': 78,
    })
    audit()


def audit():
    freeze = original.read(RUN / 'freeze.json')
    for name, digest in freeze['hashes'].items():
        assert original.sha_file(RUN / name) == digest, name
    for label, directory in (('parent', PARENT), ('previous', PREVIOUS)):
        for name, digest in freeze['prior_run_hashes'][label].items():
            assert original.sha_file(directory / name) == digest, 'Prior evidence changed'
    assert original.sha_file(PROTOCOL) == freeze['protocol_sha256']
    assert original.sha_file(Path(__file__)) == freeze['continuation_runner_sha256']
    assert original.sha_file(Path(original.__file__)) == freeze['original_runner_sha256']
    parent, selected, _ = selected_positions()
    manifest = original.read(RUN / 'manifest.json')
    assert manifest['planned'] == len(manifest['requests']) == TOTAL
    assert manifest['configuration'] == parent['configuration']
    assert manifest['failure_policy'] == parent['failure_policy']
    assert [r['source_request_id'] for r in manifest['requests']] == [r['request_id'] for r in selected]
    assert len({r['request_id'] for r in manifest['requests']}) == TOTAL
    for row, source in zip(manifest['requests'], selected):
        for name, value in source.items():
            if name != 'request_id':
                assert row[name] == value
        assert (RUN / row['prompt_path']).read_bytes() == (PARENT / source['prompt_path']).read_bytes()
        assert original.sha_file(RUN / row['prompt_path']) == row['prompt_sha256']
    print('PASS: only six missing positions; 78 valid positions excluded; all prior evidence preserved', flush=True)


def classify_error(raw):
    text = raw.decode('utf-8', errors='replace').lower()
    if 'subscription ended' in text or 'payment method needs authorization' in text:
        return 'subscription_ended_payment_authorization_required'
    if any(word in text for word in ('5-hour', '5 hour', 'five hour', '5h limit')):
        return 'five_hour_allowance_limit'
    if 'weekly' in text:
        return 'weekly_allowance_limit'
    if 'monthly' in text:
        return 'monthly_allowance_limit'
    if any(word in text for word in ('insufficient balance', 'not enough balance', 'no balance')):
        return 'insufficient_account_balance'
    if any(word in text for word in ('quota', 'usage limit', 'allowance')):
        return 'account_allowance_limit'
    if 'rate limit' in text or 'too many requests' in text:
        return 'rate_limit'
    return 'provider_http_error_unspecified'


def call_with_diagnosis(row, key):
    # Single-threaded metadata instrumentation: successful requests are unchanged.
    # Error bytes are read only in memory and never returned or persisted.
    diagnostics = {}
    factory = urllib.request.build_opener
    class SafeHTTPErrorCapture(urllib.request.HTTPErrorProcessor):
        def http_response(self, request, response):
            if response.code >= 400:
                body = response.read()
                diagnostics['provider_error_category'] = classify_error(body)
                retry = response.headers.get('Retry-After', '')
                if retry.isdigit():
                    diagnostics['retry_after_seconds'] = int(retry)
                raise urllib.error.HTTPError(request.full_url, response.code, response.msg,
                                             response.headers, io.BytesIO(body))
            return super().http_response(request, response)
        https_response = http_response
    def instrumented_factory(*handlers):
        return factory(*handlers, SafeHTTPErrorCapture())
    urllib.request.build_opener = instrumented_factory
    try:
        receipt = original.call(row, (RUN / row['prompt_path']).read_text(encoding='utf-8'), key)
    finally:
        urllib.request.build_opener = factory
    receipt.update(diagnostics)
    receipt.update(source_request_id=row['source_request_id'], failure_selected_supplement=True,
                   continuation_after_preserved_429=True)
    return receipt


def execute():
    audit()
    assert original.read(RUN / 'status.json')['state'] == 'PREPARED', 'Existing execution; do not retry'
    assert not list((RUN / 'dispatches').glob('*.json')), 'Existing dispatch; do not duplicate'
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        key = getpass.getpass('New credential (input hidden): ').strip()
    assert key, 'No credential supplied; no request sent'
    lock = RUN / 'execution.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
    state = {'state': 'RUNNING', 'halt_reason': None}
    manifest = original.read(RUN / 'manifest.json')
    original.dump(RUN / 'launch_receipt.private.json', {
        'pid': os.getpid(), 'host': os.environ.get('COMPUTERNAME'), 'launch_utc': original.now(),
        'command': 'python -X utf8 -B scripts/continue_frozen_replay_r0_missing.py --execute',
        'run_path': str(RUN.resolve()), 'manifest_sha256': original.sha_file(RUN / 'manifest.json'),
        'planned_provider_requests': TOTAL, 'effective_concurrency': 1,
    })
    def update():
        receipts = [original.read(file) for file in (RUN / 'responses').glob('*.json')]
        value = {
            **state, 'planned': TOTAL,
            'provider_requests': len(list((RUN / 'dispatches').glob('*.json'))),
            'response_count': len(receipts), 'valid': sum(r['parse_status'] == 'valid' for r in receipts),
            'parent_primary_valid': 77, 'previous_distinct_valid_positions': 78,
            'updated_utc': original.now(),
        }
        original.dump(RUN / 'status.json', value)
        return value
    try:
        update()
        for row in manifest['requests']:
            dispatch = RUN / 'dispatches' / (row['request_id'] + '.json')
            output = RUN / 'responses' / (row['request_id'] + '.json')
            assert not dispatch.exists() and not output.exists(), 'Existing attempt; refuse duplicate'
            original.dump(dispatch, {
                'request_id': row['request_id'], 'source_request_id': row['source_request_id'],
                'dispatched_utc': original.now(), 'prompt_sha256': row['prompt_sha256'],
            })
            update()
            receipt = call_with_diagnosis(row, key)
            original.dump(output, receipt)
            if receipt.get('http_status') in (401, 403, 429):
                state.update(state='HALTED', halt_reason='HTTP ' + str(receipt['http_status']),
                             provider_error_category=receipt.get('provider_error_category'))
            value = update()
            print('Continuation: {}/6 received, {} valid'.format(value['response_count'], value['valid']), flush=True)
            if state['state'] == 'HALTED':
                break
        if state['state'] != 'HALTED':
            state['state'] = 'ALL_6_ATTEMPTED'
        final = update()
        final['completed_utc'] = original.now()
        original.dump(RUN / 'status.json', final)
    except BaseException as exc:
        state.update(state='INTERRUPTED', halt_reason=type(exc).__name__)
        update()
        raise
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--audit', action='store_true')
    group.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.audit:
        audit()
    else:
        execute()


if __name__ == '__main__':
    main()
