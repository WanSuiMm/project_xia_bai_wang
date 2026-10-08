"""One authorized fresh attempt for each of seven invalid R0 positions only."""
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import warnings

import run_frozen_replay_r0 as original


PARENT = original.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_84_02'
RUN = original.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_supplement07_01'
PROTOCOL = original.BASE / 'replay_r0/SUPPLEMENT07_PROTOCOL_20261007.md'


def parent_selection():
    status = original.read(PARENT / 'status.json')
    assert status['state'] == 'ALL_84_ATTEMPTED'
    assert status['provider_requests'] == 84 and status['response_count'] == 84
    assert status['valid'] == 77
    manifest = original.read(PARENT / 'manifest.json')
    selected = []
    parent_hashes = {'manifest.json': original.sha_file(PARENT / 'manifest.json')}
    for row in manifest['requests']:
        relative = 'responses/' + row['request_id'] + '.json'
        receipt = original.read(PARENT / relative)
        parent_hashes[relative] = original.sha_file(PARENT / relative)
        if receipt['parse_status'] != 'valid':
            assert row['model'] == 'glm-5.3' and row['condition'] == 'blind'
            selected.append((row, receipt))
    assert len(selected) == 7
    return manifest, selected, parent_hashes


def prepare():
    assert not RUN.exists(), 'Preserve existing supplement; refuse regeneration'
    original.audit(PARENT)
    parent_manifest, selected, parent_hashes = parent_selection()
    RUN.mkdir(parents=True)
    requests = []
    for source, failed in selected:
        row = dict(source)
        row['source_request_id'] = source['request_id']
        row['request_id'] = 'supplement01_' + source['request_id']
        row['original_failure'] = {
            k: failed.get(k) for k in ('status', 'parse_status', 'finish_reason', 'error_type')
        }
        prompt_file = RUN / row['prompt_path']
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_bytes((PARENT / source['prompt_path']).read_bytes())
        requests.append(row)
    manifest = {
        'schema_version': 1, 'created_utc': original.now(),
        'study': 'R0 failure-selected supplement, one new attempt per invalid position',
        'planned': 7, 'parent_run': PARENT.name, 'parent_valid': 77,
        'requests': requests, 'configuration': parent_manifest['configuration'],
        'effective_model_workers': 1, 'models': ['glm-5.3'],
        'failure_policy': parent_manifest['failure_policy'],
        'primary_analysis_unchanged': True,
        'interpretation': 'Supplementary completion is failure-selected, never an original clean 84-call dataset.',
    }
    original.dump(RUN / 'manifest.json', manifest)
    hashes = {'manifest.json': original.sha_file(RUN / 'manifest.json')}
    for row in requests:
        hashes[row['prompt_path']] = original.sha_file(RUN / row['prompt_path'])
    original.dump(RUN / 'freeze.json', {
        'created_utc': original.now(), 'experimental_requests_at_freeze': 0,
        'hashes': hashes, 'parent_hashes': parent_hashes,
        'reference_hashes': {
            'protocol': original.sha_file(PROTOCOL),
            'supplement_runner': original.sha_file(Path(__file__)),
            'original_runner': original.sha_file(Path(original.__file__)),
        },
    })
    (RUN / 'dispatches').mkdir()
    (RUN / 'responses').mkdir()
    original.dump(RUN / 'status.json', {
        'state': 'PREPARED', 'planned': 7, 'provider_requests': 0,
        'response_count': 0, 'valid': 0, 'parent_primary_valid': 77,
    })
    audit()


def audit():
    freeze = original.read(RUN / 'freeze.json')
    for name, digest in freeze['hashes'].items():
        assert original.sha_file(RUN / name) == digest, name
    for name, digest in freeze['parent_hashes'].items():
        assert original.sha_file(PARENT / name) == digest, 'Original changed: ' + name
    for name, path in (
        ('protocol', PROTOCOL), ('supplement_runner', Path(__file__)),
        ('original_runner', Path(original.__file__)),
    ):
        assert original.sha_file(path) == freeze['reference_hashes'][name], name
    parent_manifest, selected, _ = parent_selection()
    m = original.read(RUN / 'manifest.json')
    assert m['planned'] == len(m['requests']) == 7
    assert m['configuration'] == parent_manifest['configuration']
    assert m['failure_policy'] == parent_manifest['failure_policy']
    assert [r['source_request_id'] for r in m['requests']] == [r['request_id'] for r, _ in selected]
    assert len({r['request_id'] for r in m['requests']}) == 7
    for row, (source, _) in zip(m['requests'], selected):
        for name, value in source.items():
            if name != 'request_id':
                assert row[name] == value, name
        assert (RUN / row['prompt_path']).read_bytes() == (PARENT / source['prompt_path']).read_bytes()
        assert original.sha_file(RUN / row['prompt_path']) == row['prompt_sha256']
    print('PASS: seven invalid positions only; original prompts, parameters and receipts preserved', flush=True)


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
    m = original.read(RUN / 'manifest.json')
    state = {'state': 'RUNNING', 'halt_reason': None}
    original.dump(RUN / 'launch_receipt.private.json', {
        'pid': os.getpid(), 'host': os.environ.get('COMPUTERNAME'),
        'launch_utc': original.now(), 'run_path': str(RUN.resolve()),
        'command': 'python -X utf8 -B scripts/rerun_frozen_replay_r0_missing.py --execute',
        'manifest_sha256': original.sha_file(RUN / 'manifest.json'),
        'planned_provider_requests': 7, 'effective_concurrency': 1,
    })
    def update():
        receipts = [original.read(p) for p in (RUN / 'responses').glob('*.json')]
        value = {
            **state, 'planned': 7,
            'provider_requests': len(list((RUN / 'dispatches').glob('*.json'))),
            'response_count': len(receipts),
            'valid': sum(r['parse_status'] == 'valid' for r in receipts),
            'parent_primary_valid': 77, 'updated_utc': original.now(),
        }
        original.dump(RUN / 'status.json', value)
        return value
    try:
        update()
        for row in m['requests']:
            dispatch = RUN / 'dispatches' / (row['request_id'] + '.json')
            output = RUN / 'responses' / (row['request_id'] + '.json')
            assert not dispatch.exists() and not output.exists(), 'Existing attempt; refuse duplicate'
            original.dump(dispatch, {
                'request_id': row['request_id'], 'source_request_id': row['source_request_id'],
                'dispatched_utc': original.now(), 'prompt_sha256': row['prompt_sha256'],
            })
            update()
            receipt = original.call(row, (RUN / row['prompt_path']).read_text(encoding='utf-8'), key)
            receipt.update(source_request_id=row['source_request_id'], failure_selected_supplement=True)
            original.dump(output, receipt)
            if receipt.get('http_status') in (401, 403, 429):
                state['state'] = 'HALTED'
                state['halt_reason'] = 'HTTP ' + str(receipt['http_status']) + '; remaining not dispatched'
            value = update()
            print('Supplement progress: {}/7 received, {} valid'.format(value['response_count'], value['valid']), flush=True)
            if state['state'] == 'HALTED':
                break
        if state['state'] != 'HALTED':
            state['state'] = 'ALL_7_ATTEMPTED'
        final = update()
        final['completed_utc'] = original.now()
        original.dump(RUN / 'status.json', final)
    except BaseException as exc:
        state['state'] = 'INTERRUPTED'
        state['halt_reason'] = 'Interrupted execution: ' + type(exc).__name__
        update()
        raise
    finally:
        lock.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--audit', action='store_true')
    group.add_argument('--execute', action='store_true')
    args = p.parse_args()
    if args.prepare:
        prepare()
    elif args.audit:
        audit()
    else:
        execute()


if __name__ == '__main__':
    main()
