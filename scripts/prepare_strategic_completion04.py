"""Freeze the two remaining slots; no provider calls or evidence overwrite."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]/'strategic_bluff_pilot'
PREVIOUS = BASE/'runs/arena_20261003_strategic_recovery03'
RUN = BASE/'runs/arena_20261004_strategic_completion04'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def main():
    if RUN.exists():
        raise SystemExit('Preserve existing completion attempt.')
    bundle = read(PREVIOUS/'bundle.json')
    ids = ['S02_D2_strong','S02_D1_natural']
    previous = {key:read(PREVIOUS/'trajectories'/f'{key}.json') for key in ids}
    assert all(r['status']!='completed' for r in previous.values())
    files = [PREVIOUS/'bundle.json',PREVIOUS/'freeze.json',*sorted((PREVIOUS/'trajectories').glob('*.json'))]
    cutoff = PREVIOUS/'cutoff.json'
    if not cutoff.exists():
        cutoff.write_text(json.dumps({'cutoff_utc':datetime.now(timezone.utc).isoformat(),
            'collection_state':'SIX_TOTAL_ENDPOINTS_BEFORE_TWO_SLOT_COMPLETION',
            'records':[{'file':p.relative_to(PREVIOUS).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]},indent=2)+'\n',encoding='utf-8')
    for e in read(cutoff)['records']:
        assert hashlib.sha256((PREVIOUS/e['file']).read_bytes()).hexdigest()==e['sha256']
    configs = {t['id']:t for t in bundle['trajectories']}
    bundle['trajectories'] = [configs[key] for key in ids]
    bundle['retry_provenance'] = {'original_run':PREVIOUS.name,
        'authorization':'User requested completing the remaining two slots',
        'selection':'Both slots lacking terminal decisions, independent of correctness',
        'mode':'Strong inherits complete openings in original sessions, fresh Judge; natural fresh A/B/J to avoid own-partial context',
        'created_utc':datetime.now(timezone.utc).isoformat()}
    (RUN/'trajectories').mkdir(parents=True)
    data = (json.dumps(bundle,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    (RUN/'bundle.json').write_bytes(data)
    (RUN/'freeze.json').write_text(json.dumps({'bundle_sha256':hashlib.sha256(data).hexdigest(),
        'protocol_sha256':hashlib.sha256((BASE/'PROTOCOL.md').read_bytes()).hexdigest(),
        'previous_cutoff_sha256':hashlib.sha256(cutoff.read_bytes()).hexdigest(),
        'invariant_check':'PASS','model_calls_at_freeze':0},indent=2)+'\n',encoding='utf-8')
    for key in ids:
        messages = [] if key.endswith('natural') else [m.copy() for m in previous[key]['messages'] if m.get('reply') and m['question_index']==0 and m['role'] in ['A','B']]
        if key.endswith('strong'):
            assert len(messages)==2
        for m in messages:
            m['inherited_from_run']=PREVIOUS.name
        r = {**configs[key],'status':'not_started','messages':messages,'events':[],'asks':0,
            'inherited_source_record_sha256':hashlib.sha256((PREVIOUS/'trajectories'/f'{key}.json').read_bytes()).hexdigest()}
        (RUN/'trajectories'/f'{key}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'state':'FROZEN','slots':ids,'inherited_openings':2,'model_calls':0}))

if __name__=='__main__':
    main()
