"""Export two fixed completed Frozen endpoints; audit from public files without API calls."""
import argparse
import hashlib
import json
from pathlib import Path
from run_boundary_go_case2 import next_turn, parse
from run_boundary_go_v2 import validate
from run_boundary_go_fresh_frozen_resume import decode_missing_quote

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'epistemic_boundary_mimicry'
OUT = BASE / 'published_runs/go_frozen_pair_completed_20261004'
SLOTS = [('EB03_D1_symmetric_frozen', 'opencode_go_20261004_fresh_frozen_resume01',
          'opencode_go_20261004_fresh_frozen01'),
         ('EB04_D1_symmetric_frozen', 'opencode_go_20261004_archaeology_frozen01',
          'opencode_go_20261004_archaeology_frozen01')]


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def write(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def export():
    if OUT.exists() and list(OUT.glob('*.json')):
        raise SystemExit('Preserve existing snapshot')
    OUT.mkdir(parents=True, exist_ok=True)
    bundles = {}
    for ident, run_name, original_name in SLOTS:
        run = BASE / 'runs' / run_name
        original = BASE / 'runs' / original_name
        b = read(run / 'bundle.json')
        f = read(original / 'freeze.json')
        for key, name in [('bundle_sha256','bundle.json'), ('sources_sha256','sources_frozen.json'), ('seats_sha256','seats_frozen.json')]:
            assert hashlib.sha256((original / name).read_bytes()).hexdigest() == f[key]
        original_bundle = read(original / 'bundle.json')
        for key in ['cases','role_initial_prompts','configuration','trajectories']:
            assert b[key] == original_bundle[key]
        r = read(run / 'trajectories' / (ident + '.json'))
        assert r['status'] == 'completed'
        sources = read(original / 'sources_frozen.json')
        seats = read(original / 'seats_frozen.json')
        bundles[ident] = {'public_context': b['cases'][0]['public_context'],
            'sources': b['cases'][0]['sources'], 'configuration': b['configuration'],
            'role_initial_prompts': b['role_initial_prompts'],
            'randomization': {'generation_seeds': sources['generation_seeds'],
                'seat_seed': seats['seat_seed'], 'seat_source_ids': seats['seat_source_ids'],
                'target_draw_seed': b['target_draw_seed'],
                'target_draw_after_source_and_seat_freeze': b['target_draw_after_source_and_seat_freeze'],
                'judge_informed_of_random_label': False}, 'claim_boundary': b['claim_boundary']}
        projected = {k:r[k] for k in ['id','case_id','condition','speaker_model','judge_model',
            'target_seat','target_source_id','other_source_id','status','asks','terminal','correct']}
        projected['messages'] = []
        for m in r['messages']:
            receipt = read(run / m['receipt'])
            assert receipt['text'] == m['raw']
            v = {k:m.get(k) for k in ['role','question_index','prompt','model','raw','parsed','setup','reply']}
            v.update({k:receipt.get(k) for k in ['returned_model','finish_reason','http_status','usage']})
            if 'one_off_syntax_repair' in m:
                v['one_off_syntax_repair'] = m['one_off_syntax_repair']
            projected['messages'].append(v)
        projected['inherited_messages'] = r.get('inherited_messages',0)
        projected['estimated_new_usage_usd'] = read(run / 'status.json')['estimated_usage_usd']
        if original != run:
            old = read(original / 'trajectories' / (ident + '.json'))
            assert len(old['messages']) == projected['inherited_messages']
            assert all(old['messages'][i]['raw'] == projected['messages'][i]['raw'] and
                old['messages'][i]['prompt'] == projected['messages'][i]['prompt'] for i in range(len(old['messages'])))
            projected['original_failure'] = old['events'][-1]['detail']
            projected['estimated_original_usage_usd'] = read(original / 'status.json')['estimated_usage_usd']
        write(OUT / (ident + '.json'), projected)
    write(OUT / 'bundle.json', bundles)
    write(OUT / 'manifest.json', {'files':[{'file':p.name,'sha256_lf_utf8':digest(p)} for p in sorted(OUT.glob('*.json'))],
        'projection':'Exact visible prompts and replies; omits reasoning, sessions, accounts, machine data and credentials.'})


def audit():
    for entry in read(OUT / 'manifest.json')['files']:
        assert digest(OUT / entry['file']) == entry['sha256_lf_utf8']
    bundles = read(OUT / 'bundle.json')
    summary = []
    for ident, _, _ in SLOTS:
        b = bundles[ident]
        r = read(OUT / (ident + '.json'))
        assignments = b['randomization']['seat_source_ids']
        byid = {s['source_id']:s for s in b['sources']}
        p = b['role_initial_prompts'][ident]
        normalized = []
        for seat in ['A','B']:
            own = byid[assignments[seat]]['source_text']
            other = byid[assignments['B' if seat == 'A' else 'A']]['source_text']
            assert own in p[seat] and other not in p[seat] and own not in p['J']
            assert hashlib.sha256(own.encode()).hexdigest() == byid[assignments[seat]]['source_sha256']
            normalized.append(p[seat].replace(own,'<SOURCE>').replace('speaker '+seat,'speaker <SEAT>'))
        assert normalized[0] == normalized[1]
        assert assignments[r['target_seat']] == r['target_source_id']
        assert b['randomization']['target_draw_after_source_and_seat_freeze']
        replay = {**r,'messages':[],'asks':0}
        repairs = 0
        for i,m in enumerate(r['messages']):
            assert (m['role'],m['question_index'],m['prompt']) == next_turn(replay,b), ('routing',ident,i)
            assert m['http_status'] == 200 and m['returned_model'] == m['model']
            assert m['finish_reason'] in ('stop','end_turn') and m['reply'] and not m['setup']
            if 'one_off_syntax_repair' in m:
                v, corrected = decode_missing_quote(m['raw'])
                assert corrected == m['one_off_syntax_repair']['corrected_json']
                assert hashlib.sha256(m['raw'].encode()).hexdigest() == m['one_off_syntax_repair']['original_raw_sha256']
                assert ident.startswith('EB03') and i == 9
                repairs += 1
            else:
                v = parse(m['raw'])
            validate(v,m['role'],m['question_index'],first_judge=m['role']=='J' and not replay['asks'])
            assert v == m['parsed']
            if m['role']=='J' and v['action']=='ASK': replay['asks'] += 1
            replay['messages'].append(m)
        assert repairs == (1 if ident.startswith('EB03') else 0)
        assert replay['asks'] == r['asks'] and r['terminal'] == r['messages'][-1]['parsed']
        assert r['status']=='completed' and r['terminal']['action']=='ABSTAIN' and r['correct'] is None
        if repairs:
            old = read(BASE / 'published_runs/go_fresh_frozen_cutoff_20261004' / (ident+'.json'))
            assert len(old['messages']) == r['inherited_messages']
            assert all(m['raw']==r['messages'][i]['raw'] and m['prompt']==r['messages'][i]['prompt'] for i,m in enumerate(old['messages']))
        summary.append({'id':ident,'asks':r['asks'],'terminal':r['terminal']['action'],'repairs':repairs})
    print(json.dumps({'audit_errors':[],'endpoints':summary}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',action='store_true')
    if parser.parse_args().export: export()
    audit()
