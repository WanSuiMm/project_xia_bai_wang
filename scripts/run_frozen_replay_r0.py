"""Prepare/audit/execute 84 one-shot Frozen disclosure replays, no Speaker calls."""
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'epistemic_boundary_mimicry'
DEFAULT_RUN=BASE/'runs/opencode_go_20261007_frozen_replay_r0_84_01'
COHORT=BASE/'analysis/offline_coding_20261005/replay_cohort.json'
DRAFT=ROOT/'XiaBaiWang_Statistical_ToM_Formalization_20261007.md'
PROTOCOL=BASE/'replay_r0/PROTOCOL_20261007.md'
ENDPOINTS={'glm-5.3':'chat/completions','qwen3.8-max':'messages'}
SEED=2026100701
MAX_TOKENS=32768
LOCK=threading.Lock()

def now():return datetime.now(timezone.utc).isoformat()
def sha_bytes(v):return hashlib.sha256(v).hexdigest()
def sha_file(p):return sha_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
def read(p):return json.loads(p.read_text(encoding='utf8'))
def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    temp.replace(p)

def modules():
    text=DRAFT.read_text(encoding='utf8')
    section=text.split('### 13.2 ',1)[1].split('### 13.3 ',1)[0]
    fences=re.findall(r'```text\n(.*?)\n```',section,re.S)
    assert len(fences)==5
    common,blind,informed,template,output=fences
    assert '[exact terminal-blind chronological questions and answers]' in template
    return {'common':common,'blind':blind,'informed':informed,'output':output}

def render(payload):
    lines=[]
    for q in payload['dialogue']:
        lines.append(f"Interviewer (to {q['target']}): {q['question']}")
        for a in q['answers']:
            lines.append(f"Speaker {a['speaker']}: {a['reply']}")
    return '<public_context>\n'+payload['public_context']+'\n</public_context>\n\n<conversation>\n'+'\n\n'.join(lines)+'\n</conversation>'

def prepare(run):
    assert not run.exists(),'Preserve existing run; audit/resume does not regenerate frozen inputs.'
    cohort=read(COHORT);assert len(cohort['records'])==7
    old=read(COHORT.parent/'freeze.json')
    assert sha_file(COHORT)==old['cohort_sha256_lf']
    blocks=modules();run.mkdir(parents=True)
    dump(run/'prompt_modules.json',blocks)
    frozen={'rule':cohort['rule'],'records':cohort['records']}
    dump(run/'cohort.json',frozen)
    weights={r['id']:(1/12 if r['id'].startswith('EB05_') else 1/6) for r in frozen['records']}
    assert math.isclose(sum(weights.values()),1)
    prompts={}
    for r in frozen['records']:
        for condition in ('blind','informed'):
            prompt='\n\n'.join([blocks['common'],blocks[condition],render(r['payload']),blocks['output']])
            key=r['id']+'_'+condition
            file=run/'prompts'/(key+'.txt');file.parent.mkdir(exist_ok=True)
            file.write_text(prompt+'\n',encoding='utf8')
            prompts[key]={'path':file.relative_to(run).as_posix(),'sha256':sha_file(file)}
    rng=random.Random(SEED)
    waves=[(r['id'],rep) for rep in (1,2,3) for r in frozen['records']];rng.shuffle(waves)
    schedule=[]
    for model_index,model in enumerate(ENDPOINTS):
        first=['blind']*10+['informed']*11 if model_index==0 else ['blind']*11+['informed']*10
        rng.shuffle(first)
        for wave,(ident,rep) in enumerate(waves,1):
            pair=ident+'_'+model+'_r'+str(rep)
            order=[first[wave-1], 'informed' if first[wave-1]=='blind' else 'blind']
            for slot,condition in enumerate(order,1):
                key=ident+'_'+condition
                schedule.append({'request_id':pair+'_'+condition,'transcript_id':ident,
                    'model':model,'condition':condition,'replicate':rep,'pair_id':pair,
                    'wave':wave,'slot_order':slot,'prompt_path':prompts[key]['path'],
                    'prompt_sha256':prompts[key]['sha256'],'max_tokens':MAX_TOKENS})
    manifest={'schema_version':1,'study':'R0 fixed transcript Blind/Informed replay',
        'created_utc':now(),'planned':84,'repetitions':3,'models':list(ENDPOINTS),
        'endpoint_base':'https://opencode.ai/zen/go/v1','endpoint_formats':ENDPOINTS,
        'randomization_seed':SEED,'family_weights':weights,'prompts':prompts,'requests':schedule,
        'target_semantics':'Original independent target designation, not original sole source access.',
        'configuration':{'temperature':0.5,'max_tokens':MAX_TOKENS,'reasoning':'deployment default; omitted',
            'stream':False,'tools':False,'timeout_seconds':600,'concurrency':2,'one_worker_per_model':True,
            'session':'fresh independent session for every request','response_reason_max_words':120},
        'failure_policy':{'semantic_retry':False,'transport_retry':False,'model_fallback':False,
            'no_probability_repair':True,'stop_remaining_on':[401,403,429],
            'quota_stop_is_missing_not_abstain':True,'unknown_inflight_no_resubmit':True,
            'fixed_count_no_result_dependent_extension':True},
        'score':{'oracle_p_A':0.5,'primary':'family weighted expected excess Brier per model',
            'correct_loss':0,'wrong_loss':1,'abstain_loss':0.25,
            'inference':'fixed six-family convenience cohort; no population effect or model ranking'},
        'allowance':'Existing Go account only; no overage switch, purchase, model substitution or auto refill.'}
    dump(run/'manifest.json',manifest)
    dump(run/'freeze.json',{'created_utc':now(),'experimental_requests_at_freeze':0,
        'hashes':{'manifest.json':sha_file(run/'manifest.json'),'cohort.json':sha_file(run/'cohort.json'),
                  'prompt_modules.json':sha_file(run/'prompt_modules.json')},
        'reference_hashes':{'original_cohort':sha_file(COHORT),'draft':sha_file(DRAFT),
                            'protocol':sha_file(PROTOCOL),'runner':sha_file(Path(__file__))}})
    (run/'responses').mkdir();(run/'dispatches').mkdir()
    dump(run/'status.json',{'state':'PREPARED','planned':84,'response_count':0,'valid':0,'provider_requests':0})
    audit(run)

def audit(run):
    f=read(run/'freeze.json')
    for filename,h in f['hashes'].items():assert sha_file(run/filename)==h,filename
    for name,p in [('original_cohort',COHORT),('draft',DRAFT),('protocol',PROTOCOL),('runner',Path(__file__))]:
        assert sha_file(p)==f['reference_hashes'][name],name
    m=read(run/'manifest.json');c=read(run/'cohort.json')
    assert len(m['requests'])==84 and len({r['request_id'] for r in m['requests']})==84
    ids={r['id'] for r in c['records']}
    assert len(ids)==7 and math.isclose(sum(m['family_weights'].values()),1)
    for row in c['records']:
        compact=json.dumps(row['payload'],ensure_ascii=False,separators=(',',':')).encode()
        # Prior payload hash convention is independently checked below.
        assert set(row['payload'])=={'public_context','dialogue'}
        for q in row['payload']['dialogue']:
            assert set(q)=={'question_index','target','question','answers'}
            for a in q['answers']:assert set(a)=={'speaker','reply'}
    old=read(COHORT)
    assert c['records']==old['records'],'Canonical model-facing payloads unchanged'
    for r in m['requests']:
        assert r['transcript_id'] in ids and r['replicate'] in (1,2,3)
        assert r['model'] in ENDPOINTS and r['condition'] in ('blind','informed')
        assert sha_file(run/r['prompt_path'])==r['prompt_sha256']
    from collections import Counter
    cells=Counter((r['transcript_id'],r['model'],r['condition']) for r in m['requests'])
    assert len(cells)==28 and set(cells.values())=={3}
    for p in {r['pair_id'] for r in m['requests']}:
        pair=[r for r in m['requests'] if r['pair_id']==p]
        assert len(pair)==2 and {r['slot_order'] for r in pair}=={1,2}
        assert {r['condition'] for r in pair}=={'blind','informed'}
    print(json.dumps({'offline_audit':'PASS','planned':84,'prompts':14,'families':6,'payloads':7}),flush=True)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def parse(text,finish):
    if finish in ('length','max_tokens'):return None,'truncated'
    if not text.strip():return None,'empty_visible'
    text=text.strip()
    if text.startswith('```json\n') and text.endswith('```'):text=text[8:-3].strip()
    try:
        value=json.loads(text)
        assert isinstance(value,dict) and set(value)=={'p_A','decision','reason'}
        p=value['p_A']
        assert isinstance(p,(int,float)) and not isinstance(p,bool) and math.isfinite(p) and 0<=p<=1
        assert value['decision'] in ('A','B','ABSTAIN')
        assert isinstance(value['reason'],str) and value['reason'].strip() and len(value['reason'].split())<=120
        return value,'valid'
    except (ValueError,TypeError,AssertionError):return None,'invalid_json_or_schema'

def call(row,prompt,key):
    model=row['model'];fmt=ENDPOINTS[model]
    headers={'Content-Type':'application/json','User-Agent':'XiaBaiWangResearch/1.0',
        'x-opencode-session':'xia-r0-'+str(uuid4())}
    if fmt=='messages':headers.update({'x-api-key':key,'anthropic-version':'2023-06-01'})
    else:headers['Authorization']='Bearer '+key
    body={'model':model,'messages':[{'role':'user','content':prompt}],
        'max_tokens':MAX_TOKENS,'temperature':0.5,'stream':False}
    receipt={k:row[k] for k in ['request_id','transcript_id','model','condition','replicate','pair_id','slot_order','prompt_sha256']}
    receipt.update({'status':'inflight','sent_utc':now(),'visible_text':'','parsed':None,
        'parse_status':'not_received','finish_reason':None,'usage':{},'returned_model':None,
        'session_id_private':headers['x-opencode-session'],'raw_response_path':None})
    start=time.monotonic()
    try:
        req=urllib.request.Request('https://opencode.ai/zen/go/v1/'+fmt,
            data=json.dumps(body,ensure_ascii=False).encode(),headers=headers)
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=600) as response:
            data=json.loads(response.read().decode('utf8'));receipt['http_status']=response.status
        receipt['returned_model']=data.get('model');receipt['usage']=data.get('usage',{})
        if fmt=='messages':
            receipt['visible_text']=''.join(b.get('text','') for b in data.get('content',[]) if b.get('type')=='text')
            receipt['finish_reason']=data.get('stop_reason')
        else:
            c=data['choices'][0];receipt['visible_text']=c['message'].get('content') or ''
            receipt['finish_reason']=c.get('finish_reason')
        receipt['status']='response_received'
        receipt['parsed'],receipt['parse_status']=parse(receipt['visible_text'],receipt['finish_reason'])
        if receipt['returned_model']!=model:
            receipt['parsed']=None;receipt['parse_status']='unexpected_model'
        # Persist visible fields and usage only. Hidden reasoning/provider headers are discarded.
    except urllib.error.HTTPError as e:
        receipt.update(status='http_error',http_status=e.code)
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        receipt.update(status='transport_unknown',error_type=type(e).__name__)
    except (ValueError,KeyError,IndexError,TypeError) as e:
        receipt.update(status='invalid_provider_response',error_type=type(e).__name__)
    receipt['elapsed_seconds']=round(time.monotonic()-start,3);receipt['captured_utc']=now()
    # A key echo is not expected, but never allow it to enter a receipt.
    receipt['visible_text']=receipt['visible_text'].replace(key,'[REDACTED]')
    if receipt['parsed'] and key in json.dumps(receipt['parsed']):
        receipt['parsed']=None;receipt['parse_status']='credential_echo_redacted'
    return receipt

def execute(run):
    audit(run);key=os.environ.get('OPENCODE_GO_API_KEY')
    assert key,'OPENCODE_GO_API_KEY unavailable; no request sent'
    lock=run/'execution.lock'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:raise SystemExit('Existing execution lock; do not duplicate dispatch')
    os.close(fd)
    m=read(run/'manifest.json');halt=threading.Event();state={'halt_reason':None}
    launch={'pid':os.getpid(),'host':os.environ.get('COMPUTERNAME'),'launch_utc':now(),
        'command':'python -X utf8 -B scripts/run_frozen_replay_r0.py --execute',
        'run_path':str(run.resolve()),'manifest_sha256':sha_file(run/'manifest.json'),
        'planned_provider_requests':84,'max_concurrency':2}
    dump(run/'launch_receipt.private.json',launch)
    def update():
        receipts=[read(p) for p in (run/'responses').glob('*.json')]
        counts={model:{'responses':0,'valid':0} for model in m['models']}
        for r in receipts:
            counts[r['model']]['responses']+=1;counts[r['model']]['valid']+=r['parse_status']=='valid'
        value={'state':'HALTED' if halt.is_set() else 'RUNNING','planned':84,
            'provider_requests':len(list((run/'dispatches').glob('*.json'))),
            'response_count':len(receipts),'valid':sum(r['parse_status']=='valid' for r in receipts),
            'by_model':counts,'halt_reason':state['halt_reason'],'updated_utc':now()}
        dump(run/'status.json',value);return value
    def worker(model):
        for row in [r for r in m['requests'] if r['model']==model]:
            if halt.is_set():break
            out=run/'responses'/(row['request_id']+'.json')
            if out.exists():continue
            dispatch=run/'dispatches'/(row['request_id']+'.json')
            if dispatch.exists():
                with LOCK:state['halt_reason']='unknown prior in-flight request';halt.set();update()
                break
            with LOCK:
                dump(dispatch,{'request_id':row['request_id'],'dispatched_utc':now(),'prompt_sha256':row['prompt_sha256']})
                update()
            receipt=call(row,(run/row['prompt_path']).read_text(encoding='utf8'),key)
            with LOCK:
                dump(out,receipt)
                if receipt.get('http_status') in (401,403,429):
                    state['halt_reason']='HTTP '+str(receipt['http_status'])+'; preserve remaining as not dispatched';halt.set()
                value=update()
                print(json.dumps({'progress':value['response_count'],'planned':84,'valid':value['valid'],
                    'last_model':model,'last_condition':row['condition'],'last_status':receipt['status'],
                    'parse_status':receipt['parse_status'],'finish_reason':receipt['finish_reason']}),flush=True)
    try:
        with LOCK:update()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(worker,model) for model in m['models']]
            for future in futures:future.result()
        with LOCK:
            final=update();final['state']='HALTED' if halt.is_set() else 'ALL_84_ATTEMPTED'
            final['completed_utc']=now();dump(run/'status.json',final)
        print(json.dumps(final),flush=True)
    finally:lock.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,default=DEFAULT_RUN)
    p.add_argument('--prepare',action='store_true');p.add_argument('--audit',action='store_true')
    p.add_argument('--execute',action='store_true')
    args=p.parse_args();run=args.run.resolve()
    assert run.is_relative_to(BASE/'runs'),'New outputs must stay in owning project runs'
    if args.prepare:prepare(run)
    if args.audit:audit(run)
    if args.execute:execute(run)
if __name__=='__main__':main()
