"""Preserve retry cutoff; recover only missing requests using complete openings."""
import hashlib
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'strategic_bluff_pilot'
PREVIOUS = BASE / 'runs/arena_20261003_strategic_retry01'
RUN = BASE / 'runs/arena_20261003_strategic_recovery02'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def main(previous_name='arena_20261003_strategic_retry01', run_name='arena_20261003_strategic_recovery02', expected=4):
    global PREVIOUS, RUN
    for name in [previous_name, run_name]:
        if not name.replace('_', '').replace('-', '').isalnum():
            raise SystemExit('Invalid run name')
    PREVIOUS = BASE / 'runs' / previous_name
    RUN = BASE / 'runs' / run_name
    if RUN.exists():
        raise SystemExit('Recovery exists; refusing overwrite')
    bundle = read(PREVIOUS / 'bundle.json')
    records = {t['id']: read(PREVIOUS / 'trajectories' / (t['id']+'.json')) for t in bundle['trajectories']}
    assert all(r['status'] in ['completed', 'protocol_failure', 'blocked_platform'] for r in records.values())
    cutoff = PREVIOUS / 'cutoff.json'
    if not cutoff.exists():
        files = [PREVIOUS / 'bundle.json', PREVIOUS / 'freeze.json', *sorted((PREVIOUS / 'trajectories').glob('*.json'))]
        manifest = {'collection_state': 'SIX_RETRIES_ATTEMPTED', 'pending': [],
                    'cutoff_utc': datetime.now(timezone.utc).isoformat(),
                    'records': [{'file': p.relative_to(PREVIOUS).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
        cutoff.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    for entry in read(cutoff)['records']:
        assert hashlib.sha256((PREVIOUS / entry['file']).read_bytes()).hexdigest() == entry['sha256']
    failed = [t for t in bundle['trajectories'] if records[t['id']]['status'] != 'completed']
    bundle['trajectories'] = failed
    bundle['retry_provenance'] = {'original_run': PREVIOUS.name,
        'authorization': 'User explicitly requested completing missing outcomes',
        'mode': 'Inherit complete openings and their original sessions; new independent session for a missing opening or initial Judge; unchanged prompts',
        'selection': f'All {expected} residual failures before new recovery calls',
        'analysis': 'Failure-selected recovery, not additional independent observations',
        'created_utc': datetime.now(timezone.utc).isoformat()}
    assert len(failed) == expected
    (RUN / 'trajectories').mkdir(parents=True)
    data = (json.dumps(bundle, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    (RUN / 'bundle.json').write_bytes(data)
    (RUN / 'freeze.json').write_text(json.dumps({'bundle_sha256': hashlib.sha256(data).hexdigest(),
        'protocol_sha256': hashlib.sha256((BASE / 'PROTOCOL.md').read_bytes()).hexdigest(),
        'previous_cutoff_sha256': hashlib.sha256(cutoff.read_bytes()).hexdigest(),
        'invariant_check': 'PASS', 'model_calls_at_freeze': 0}, indent=2)+'\n', encoding='utf-8')
    inherited = 0
    for t in failed:
        prior = records[t['id']]
        messages = [m for m in prior['messages'] if m.get('reply')]
        assert all(m['role'] in ['A', 'B'] and m['question_index'] == 0 for m in messages)
        for m in messages:
            m['inherited_from_run'] = PREVIOUS.name
            inherited += 1
        rec = {**t, 'status': 'not_started', 'messages': messages, 'events': [], 'asks': 0,
               'inherited_source_record_sha256': hashlib.sha256((PREVIOUS / 'trajectories' / (t['id']+'.json')).read_bytes()).hexdigest()}
        (RUN / 'trajectories' / (t['id']+'.json')).write_text(json.dumps(rec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'state': 'RECOVERY_FROZEN', 'planned': len(failed), 'inherited_complete_openings': inherited}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', default='arena_20261003_strategic_retry01')
    parser.add_argument('--run', default='arena_20261003_strategic_recovery02')
    parser.add_argument('--expected', type=int, default=4)
    args = parser.parse_args()
    main(args.previous, args.run, args.expected)
