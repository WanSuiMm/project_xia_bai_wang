"""User-authorized recovery of the missing N02 judge on unchanged openings."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'naturalistic_study_1'
OLD = ROOT / 'runs/arena_20261003_naturalistic_resume01'
NEW = ROOT / 'runs/arena_20261003_naturalistic_judge_recovery01'

def main():
    if NEW.exists():
        raise SystemExit('Refusing to overwrite judge recovery')
    b = json.loads((OLD / 'bundle.json').read_text(encoding='utf-8'))
    r = json.loads((OLD / 'trajectories/N02_D1.json').read_text(encoding='utf-8'))
    j = next(m for m in r['messages'] if m['role'] == 'J')
    openings = [copy.deepcopy(m) for m in r['messages'] if m['role'] in ['A', 'B'] and m.get('reply')]
    assert len(openings) == 2
    for m in openings:
        m['inherited_from'] = 'arena_20261003_naturalistic_resume01/N02_D1'
        m['original_sent_utc'] = m.pop('sent_utc')
        m['sent'] = False
    t = {k: r[k] for k in ['case_id', 'speaker_model', 'judge_model', 'knower']}
    t['id'] = 'N02_D1_Jretry01'
    b['trajectories'] = [t]
    b['recovery'] = {'parent_run': OLD.name, 'parent_trajectory': 'N02_D1',
                     'user_authorization': 'User specifically requested recovery of the missing judge conversation.',
                     'expected_judge_prompt_sha256': hashlib.sha256(j['prompt'].encode()).hexdigest(),
                     'fixed_openings_reused': True, 'fresh_judge_session': True,
                     'automatic_monitor': False, 'minimum_send_gap_seconds': 30}
    (NEW / 'trajectories').mkdir(parents=True)
    (NEW / 'bundle.json').write_text(json.dumps(b, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (NEW / 'original_judge_prompt.txt').write_bytes(j['prompt'].encode('utf-8'))
    (NEW / 'freeze.json').write_text(json.dumps({'bundle_sha256': hashlib.sha256((NEW / 'bundle.json').read_bytes()).hexdigest(), 'model_calls_at_freeze': 0}, indent=2) + '\n', encoding='utf-8')
    (NEW / 'trajectories' / (t['id'] + '.json')).write_text(json.dumps({**t, 'messages': openings, 'status': 'openings_reused', 'asks': 0, 'events': []}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Recovery prepared: unchanged A/B openings; fresh Gemini judge; exact original prompt hash frozen')

if __name__ == '__main__':
    main()
