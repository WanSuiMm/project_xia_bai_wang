"""Freeze the user-authorized six failed configurations as fresh attempts."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'strategic_bluff_pilot'
ORIGINAL = BASE / 'runs/arena_20261003_strategic01'
RUN = BASE / 'runs/arena_20261003_strategic_retry01'

def main():
    if RUN.exists():
        raise SystemExit('Retry already exists; refusing overwrite')
    bundle = json.loads((ORIGINAL / 'bundle.json').read_text(encoding='utf-8'))
    cutoff = json.loads((ORIGINAL / 'cutoff.json').read_text(encoding='utf-8'))
    for entry in cutoff['records']:
        assert hashlib.sha256((ORIGINAL / entry['file']).read_bytes()).hexdigest() == entry['sha256']
    failed = []
    for t in bundle['trajectories']:
        r = json.loads((ORIGINAL / 'trajectories' / (t['id'] + '.json')).read_text(encoding='utf-8'))
        if r['status'] != 'completed':
            failed.append(t)
    assert len(failed) == 6
    bundle['trajectories'] = failed
    bundle['retry_provenance'] = {
        'original_run': ORIGINAL.name,
        'authorization': 'User explicitly requested continuing the six truncated/platform-missing games',
        'mode': 'Fresh independent A/B/J conversations; same source, assignments and prompt templates',
        'selection': 'All six failed configurations, fixed before new calls; no retries of correct or incorrect endpoints',
        'analysis': 'Separate attempts, not replacement evidence or six new independent dossiers',
        'created_utc': datetime.now(timezone.utc).isoformat(),
    }
    (RUN / 'trajectories').mkdir(parents=True)
    data = (json.dumps(bundle, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    (RUN / 'bundle.json').write_bytes(data)
    freeze = {'bundle_sha256': hashlib.sha256(data).hexdigest(),
              'protocol_sha256': hashlib.sha256((BASE / 'PROTOCOL.md').read_bytes()).hexdigest(),
              'invariant_check': 'PASS', 'model_calls_at_freeze': 0,
              'original_cutoff_sha256': hashlib.sha256((ORIGINAL / 'cutoff.json').read_bytes()).hexdigest()}
    (RUN / 'freeze.json').write_text(json.dumps(freeze, indent=2) + '\n', encoding='utf-8')
    for t in failed:
        record = {**t, 'status': 'not_started', 'messages': [], 'events': [], 'asks': 0}
        (RUN / 'trajectories' / (t['id'] + '.json')).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'state': 'FROZEN_RETRY', 'planned': len(failed), 'order': [t['id'] for t in failed]}))

if __name__ == '__main__':
    main()
