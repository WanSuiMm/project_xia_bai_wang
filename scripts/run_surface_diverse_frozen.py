"""Two new surface-diverse Frozen families, two reciprocal directions; fixed bounded batch."""
import argparse
import hashlib
import json
import random
from pathlib import Path
import run_boundary_go_case2 as case2
from opencode_go_client_v2 import now, session_id
from prepare_boundary_mimicry import SPEAKER, READER, JUDGE
from prepare_surface_diverse_frozen import CASES

base = case2.base
RUN = base.BASE / 'runs/opencode_go_20261004_surface_diverse_frozen02'
SEED = 2026100431
ORIGINAL_STATUS = base.status


def paths():
    return {'bundle': RUN/'bundle.json', 'sources': RUN/'sources_frozen.json',
        'seats': RUN/'seats_frozen.json', 'runner': Path(__file__),
        'materials': Path(__file__).with_name('prepare_surface_diverse_frozen.py'),
        'case2': Path(case2.__file__), 'base': Path(base.__file__),
        'templates': Path(__file__).with_name('prepare_boundary_mimicry.py'),
        'parser': Path(__file__).with_name('run_boundary_go_recovery.py'),
        'transport': Path(__file__).with_name('opencode_go_client_v2.py'),
        'protocol': base.BASE/'SURFACE_DIVERSE_FROZEN_PROTOCOL.md'}


def status(records, total_cost, state):
    v = ORIGINAL_STATUS(records,total_cost,
        'SURFACE_DIVERSE_ATTEMPT_FINISHED' if state=='ALL_FOUR_ATTEMPTED' else state)
    v['score_semantics'] = 'arbitrary independent target match, not authenticity accuracy'
    for t in v['trajectories'].values():
        t['arbitrary_target_match'] = t.pop('correct')
    base.dump(RUN/'status.json',v)
    return v


def prepare():
    if RUN.exists(): raise SystemExit('Preserve existing run')
    assert base.read(base.RUN/'smoke.json')['passed']
    cases = []
    for c in CASES:
        sources = [{'source_id':c['case_id']+'_source_'+str(i),
            'source_text':text, 'source_sha256':hashlib.sha256(text.encode()).hexdigest()}
            for i,text in enumerate(c['sources'])]
        cases.append({'case_id':c['case_id'],'public_context':c['public_context'],'sources':sources})
    (RUN/'trajectories').mkdir(parents=True)
    (RUN/'receipts').mkdir()
    base.dump(RUN/'sources_frozen.json',{'cases':cases,'created_utc':now(),
        'authorship':'fixed investigator-composed prose; shared latent fact slots, not IID source generation'})
    seats = {}; slots = []
    for c in cases:
        for d,(speaker,judge) in enumerate([('qwen3.8-max','glm-5.3'),('glm-5.3','qwen3.8-max')],1):
            i = len(slots)
            ident = c['case_id']+'_D'+str(d)+'_symmetric_frozen'
            order = c['sources'][:]
            random.Random(SEED+1000+i).shuffle(order)
            seats[ident] = {'seat_seed':SEED+1000+i,
                'seat_source_ids':dict(zip(['A','B'],[s['source_id'] for s in order]))}
            slots.append((ident,c,speaker,judge,order))
    base.dump(RUN/'seats_frozen.json',{'assignments':seats,'created_utc':now()})
    trajectories = []; prompts = {}; records = {}
    # All sources and seat assignments are on disk before any target draw.
    for i,(ident,c,speaker,judge,order) in enumerate(slots):
        target_index = random.Random(SEED+2000+i).randrange(2)
        target = ['A','B'][target_index]
        t = {'id':ident,'case_id':c['case_id'],'condition':'symmetric_frozen',
            'speaker_model':speaker,'judge_model':judge,'target_seat':target,
            'target_source_id':order[target_index]['source_id'],
            'other_source_id':order[1-target_index]['source_id'],'knower':target,
            'target_seed':SEED+2000+i}
        trajectories.append(t)
        prompts[ident] = {seat:SPEAKER.format(seat=seat,public_context=c['public_context'],
            access=READER.format(source_text=s['source_text'])) for seat,s in zip(['A','B'],order)}
        prompts[ident]['J'] = JUDGE.format(public_context=c['public_context'])
        records[ident] = {**t,'status':'not_started','asks':0,'messages':[],'events':[],
            'histories':{r:[] for r in ['A','B','J']},'session_ids':{r:session_id() for r in ['A','B','J']}}
    b = {'study':'surface-diverse Frozen pilot','cases':cases,'trajectories':trajectories,
        'role_initial_prompts':prompts,'target_draw_after_all_sources_and_seats_frozen':True,
        'judge_informed_of_random_label':False,
        'configuration':{'temperature':.5,'max_tokens':32768,'reasoning':'deployment default',
            'stream':False,'tools':False,'max_asks':None,'opening':False,'no_READY':True,
            'Judge_first':True,'parser':'strict=False; no syntax repair',
            'operational_batch_new_usage_stop_before_next_request_usd':1.9},
        'claim_boundary':'two material families, four trajectories; arbitrary target matching is not knowledge-access accuracy'}
    base.dump(RUN/'bundle.json',b)
    for ident,r in records.items(): base.dump(RUN/'trajectories'/(ident+'.json'),r)
    base.dump(RUN/'smoke.json',{'passed':True,'inherited_qualification':base.RUN.name,
        'reason':'already qualified identical endpoints/sampling, both role directions previously exercised'})
    base.dump(RUN/'freeze.json',{'bundle_sha256':hashlib.sha256((RUN/'bundle.json').read_bytes()).hexdigest(),
        'hashes':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths().items()},
        'created_utc':now(),'model_calls_at_freeze':0})
    base.RUN = RUN
    status(records,0,'PREPARED')
    audit()


def audit():
    f = base.read(RUN/'freeze.json')
    for k,p in paths().items(): assert hashlib.sha256(p.read_bytes()).hexdigest()==f['hashes'][k],k
    b = base.read(RUN/'bundle.json'); assignments = base.read(RUN/'seats_frozen.json')['assignments']
    material_stats = []
    for c in b['cases']:
        sources = c['sources']; words = [s['source_text'].split() for s in sources]
        assert all(250<=len(w)<=400 for w in words),[len(w) for w in words]
        assert max(map(len,words))/min(map(len,words)) <= 1.2
        spans = [set(' '.join(w[i:i+12]).lower() for i in range(len(w)-11)) for w in words]
        assert not spans[0].intersection(spans[1]),'shared 12-word prose span'
        for s in sources: assert hashlib.sha256(s['source_text'].encode()).hexdigest()==s['source_sha256']
        material_stats.append({'case':c['case_id'],'source_words':list(map(len,words)),'shared_12_word_spans':0})
    for t in b['trajectories']:
        c = next(c for c in b['cases'] if c['case_id']==t['case_id'])
        byid = {s['source_id']:s for s in c['sources']}; p=b['role_initial_prompts'][t['id']]
        assigned=assignments[t['id']]['seat_source_ids']; normalized=[]
        for seat,other in [('A','B'),('B','A')]:
            own=byid[assigned[seat]]['source_text']; opposite=byid[assigned[other]]['source_text']
            assert own in p[seat] and opposite not in p[seat] and own not in p['J']
            normalized.append(p[seat].replace(own,'<SOURCE>').replace('speaker '+seat,'speaker <SEAT>'))
        assert normalized[0]==normalized[1]
        assert assigned[t['target_seat']]==t['target_source_id']
        # Flipping only the Host target leaves the first model input identical.
        r={**t,'messages':[],'asks':0}
        assert case2.next_turn(r,b)==('J',1,p['J'])
        r['target_seat']='B' if t['target_seat']=='A' else 'A'
        assert case2.next_turn(r,b)==('J',1,p['J'])
    print(json.dumps({'offline_audit':'PASS','planned':4,'families':2,'material_stats':material_stats,
        'source_isolation':True,'equal_role_policy':True,'no_target_in_prompts':True,'provider_calls':0}),flush=True)


def execute(key_stdin):
    audit()
    base.RUN=RUN; base.next_turn=case2.next_turn; base.parse=case2.parse; base.status=status
    base.execute(key_stdin)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepare',action='store_true');p.add_argument('--audit',action='store_true')
    p.add_argument('--execute',action='store_true');p.add_argument('--key-stdin',action='store_true')
    a=p.parse_args()
    if a.prepare:prepare()
    if a.audit:audit()
    if a.execute:execute(a.key_stdin)
