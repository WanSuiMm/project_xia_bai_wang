"""Prepare a separately authorized serial retry; preserve original cutoff."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'naturalistic_study_1'
OLD = ROOT / 'runs/arena_20261003_naturalistic01'
NEW = ROOT / 'runs/arena_20261003_naturalistic_resume01'

def main():
    if NEW.exists():
        raise SystemExit('Refusing to overwrite resume run')
    b = json.loads((OLD / 'bundle.json').read_text(encoding='utf-8'))
    original = b['trajectories']
    completed = {t['id'] for t in original if json.loads((OLD / 'trajectories' / (t['id'] + '.json')).read_text(encoding='utf-8'))['status'] == 'completed'}
    b['trajectories'] = [t for t in original if t['id'] not in completed]
    b['resume'] = {'authorized_utc': datetime.now(timezone.utc).isoformat(),
                   'parent_run': OLD.name, 'excluded_completed': sorted(completed),
                   'mode': 'Fresh isolated sessions; same sources, prompts, assignments and model labels',
                   'request_spacing_seconds': 30, 'concurrent_trajectories': 1,
                   'stop_on_first_rate_limit': True, 'quality_retries': False}
    (NEW / 'trajectories').mkdir(parents=True)
    (NEW / 'bundle.json').write_text(json.dumps(b, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (NEW / 'freeze.json').write_text(json.dumps({'bundle_sha256': hashlib.sha256((NEW / 'bundle.json').read_bytes()).hexdigest(), 'original_bundle_sha256': hashlib.sha256((OLD / 'bundle.json').read_bytes()).hexdigest(), 'model_calls_at_freeze': 0}, indent=2) + '\n', encoding='utf-8')
    for t in b['trajectories']:
        (NEW / 'trajectories' / (t['id'] + '.json')).write_text(json.dumps({**t, 'status': 'not_started', 'messages': [], 'events': [], 'asks': 0}, indent=2) + '\n', encoding='utf-8')
    print('Separate resume frozen:', len(b['trajectories']), 'remaining trajectories; serial, 30-second minimum request spacing')

if __name__ == '__main__':
    main()
