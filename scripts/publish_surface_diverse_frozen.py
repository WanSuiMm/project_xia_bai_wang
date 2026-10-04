"""Fixed four-slot public snapshot: three endpoints plus operational usage cutoff."""
import argparse
import hashlib
import json
import random
from pathlib import Path
from run_boundary_go_case2 import next_turn, parse
from run_boundary_go_v2 import validate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'epistemic_boundary_mimicry'
RUN = BASE/'runs/opencode_go_20261004_surface_diverse_frozen02'
OUT = BASE/'published_runs/go_surface_diverse_cutoff_20261005'


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def export():
    if OUT.exists() and list(OUT.glob('*.json')): raise SystemExit('Preserve existing snapshot')
    b=read(RUN/'bundle.json');f=read(RUN/'freeze.json')
    for key,name in [('bundle','bundle.json'),('sources','sources_frozen.json'),('seats','seats_frozen.json')]:
        assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==f['hashes'][key]
    old=BASE/'runs/opencode_go_20261004_surface_diverse_frozen01'
    assert read(old/'bundle.json')==b and not list((old/'receipts').glob('*.json'))
    s=read(RUN/'status.json')
    assert s['state']=='STOP_USAGE_CEILING' and s['completed']==3
    OUT.mkdir(parents=True,exist_ok=True)
    write(OUT/'bundle.json',{k:b[k] for k in ['study','cases','trajectories','role_initial_prompts',
        'target_draw_after_all_sources_and_seats_frozen','judge_informed_of_random_label','configuration','claim_boundary']})
    write(OUT/'randomization.json',read(RUN/'seats_frozen.json')['assignments'])
    for t in b['trajectories']:
        r=read(RUN/'trajectories'/(t['id']+'.json'))
        v={k:r[k] for k in ['id','case_id','condition','speaker_model','judge_model','target_seat',
            'target_source_id','other_source_id','target_seed','status','asks']}
        v['terminal']=r.get('terminal');v['arbitrary_target_match']=r.get('correct');v['messages']=[]
        for m in r['messages']:
            receipt=read(RUN/m['receipt']);assert receipt['text']==m['raw']
            v['messages'].append({**{k:m.get(k) for k in ['role','question_index','prompt','model','raw','parsed','setup','reply']},
                **{k:receipt.get(k) for k in ['returned_model','finish_reason','http_status','usage']}})
        if not v['terminal']:
            role,index,_=next_turn(r,b)
            v['missing_next_request']={'role':role,'question_index':index}
            v['missing_reason']='batch operational estimated usage ceiling; no request dispatched'
        write(OUT/(t['id']+'.json'),v)
    write(OUT/'summary.json',{'state':s['state'],'planned':4,'completed':3,
        'estimated_usage_usd':s['estimated_usage_usd'],'families':2,
        'pre_dispatch_suffix01_failure':{'provider_calls':0,'same_bundle':True,
            'error':'missing compatibility bundle_sha256 field; corrected before dispatch'},
        'score_semantics':s['score_semantics'],'annotation_pending':True})
    write(OUT/'manifest.json',{'files':[{'file':p.name,'sha256_lf_utf8':digest(p)} for p in sorted(OUT.glob('*.json'))],
        'projection':'Exact visible prompts/replies and fixed material provenance; excludes reasoning, sessions, credentials and machine/account identifiers.'})


def audit():
    for e in read(OUT/'manifest.json')['files']: assert digest(OUT/e['file'])==e['sha256_lf_utf8']
    b=read(OUT/'bundle.json');seats=read(OUT/'randomization.json');s=read(OUT/'summary.json')
    assert b['target_draw_after_all_sources_and_seats_frozen'] and not b['judge_informed_of_random_label']
    for c in b['cases']:
        words=[x['source_text'].split() for x in c['sources']]
        spans=[set(' '.join(w[i:i+12]).lower() for i in range(len(w)-11)) for w in words]
        assert not spans[0].intersection(spans[1])
        assert all(250<=len(w)<=400 for w in words) and max(map(len,words))/min(map(len,words))<=1.2
        for x in c['sources']:assert hashlib.sha256(x['source_text'].encode()).hexdigest()==x['source_sha256']
    summary=[];completed=0
    for t in b['trajectories']:
        ident=t['id'];r=read(OUT/(ident+'.json'));c=next(c for c in b['cases'] if c['case_id']==t['case_id'])
        byid={x['source_id']:x for x in c['sources']};assignment=seats[ident]['seat_source_ids']
        order=c['sources'][:];random.Random(seats[ident]['seat_seed']).shuffle(order)
        assert assignment==dict(zip(['A','B'],[x['source_id'] for x in order]))
        assert t['target_seat']==['A','B'][random.Random(t['target_seed']).randrange(2)]
        assert assignment[t['target_seat']]==t['target_source_id']
        p=b['role_initial_prompts'][ident];normalized=[]
        for seat,other in [('A','B'),('B','A')]:
            own=byid[assignment[seat]]['source_text'];opposite=byid[assignment[other]]['source_text']
            assert own in p[seat] and opposite not in p[seat] and own not in p['J']
            normalized.append(p[seat].replace(own,'<SOURCE>').replace('speaker '+seat,'speaker <SEAT>'))
        assert normalized[0]==normalized[1]
        replay={**r,'messages':[],'asks':0}
        for i,m in enumerate(r['messages']):
            assert (m['role'],m['question_index'],m['prompt'])==next_turn(replay,b),(ident,i)
            assert m['http_status']==200 and m['returned_model']==m['model']
            assert m['finish_reason'] in ('stop','end_turn') and m['reply'] and not m['setup']
            v=parse(m['raw']);assert v==m['parsed']
            validate(v,m['role'],m['question_index'],first_judge=m['role']=='J' and not replay['asks'])
            if m['role']=='J' and v['action']=='ASK':replay['asks']+=1
            replay['messages'].append(m)
        assert replay['asks']==r['asks']
        if r['terminal']:
            completed+=1;assert r['status']=='completed' and r['terminal']==r['messages'][-1]['parsed']
            match=(r['terminal']['pick']==t['target_seat']) if r['terminal']['action']=='STOP' else None
            assert match==r['arbitrary_target_match']
        else:
            assert ident=='EB06_D2_symmetric_frozen' and r['status']=='reply_captured'
            role,index,_=next_turn(replay,b)
            assert r['missing_next_request']=={'role':role,'question_index':index}
            assert r['arbitrary_target_match'] is None
        summary.append({'id':ident,'asks':r['asks'],'terminal':r['terminal']['action'] if r['terminal'] else None,
            'pending':r.get('missing_next_request')})
    assert completed==s['completed']==3 and s['state']=='STOP_USAGE_CEILING'
    assert s['estimated_usage_usd']>=b['configuration']['operational_batch_new_usage_stop_before_next_request_usd']
    print(json.dumps({'audit_errors':[],'slots':summary,'completed':completed,'missing':1}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--export',action='store_true')
    if p.parse_args().export:export()
    audit()
