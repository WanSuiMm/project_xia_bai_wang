"""Audit exact receipts and report small-pair descriptive outcomes only."""
from pathlib import Path
import json, subprocess, shutil, hashlib
ROOT=Path(__file__).resolve().parents[1]/'v0_2_math'
RUN=ROOT/'runs/arena_20261002_selvar_pair01'
if not RUN.exists():
    RUN=ROOT/'published_runs/arena_20261002_selvar_pair01'
JS="const fs=require('fs'),root=process.argv[1],C=require(root+'/console.js'),D=JSON.parse(fs.readFileSync(root+'/bundle.json','utf8')),r=JSON.parse(fs.readFileSync(0,'utf8')),c=D.cases.find(c=>c.case_id===r.case_id);console.log(JSON.stringify({steps:C.stepsFor(c),prompts:Object.fromEntries(Object.keys(r.sent_prompts).map(k=>[k,C.buildPrompt(D,c,r,k)])),diagnostic:C.diagnostic(c,r),parsed:Object.fromEntries(Object.entries(r.raw).map(([k,v])=>[k,C.parseObject(v)]))}));"
def main():
    d=json.loads((ROOT/'bundle.json').read_text(encoding='utf-8'))
    rows=[];deviations=[];hashes=[]
    for c in d['cases']:
        p=RUN/'logs'/f"{c['case_id']}.json"
        if not p.exists():continue
        r=json.loads(p.read_text(encoding='utf-8'))
        out=json.loads(subprocess.run([shutil.which('node'),'-e',JS,str(ROOT)],input=json.dumps(r),text=True,encoding='utf-8',capture_output=True,check=True).stdout)
        assert r['case_sha256']==c['case_sha256']
        assert all(out['prompts'][k]==v for k,v in r['sent_prompts'].items())
        for k,v in r['raw'].items():
            assert r['captures'][k]['raw']==v
            assert r['captures'][k]['prompt']==r['sent_prompts'][k]
            obj=out['parsed'][k];field='explanation' if k.startswith('opening_') else 'reason' if k.startswith('judge_') else 'answer'
            n=len(obj.get(field,'').split());lo,hi=(100,140) if field=='explanation' else (0,50) if field=='reason' else (60,100)
            if not lo<=n<=hi:deviations.append(dict(case=c['case_id'],step=k,kind='word_budget',field=field,words=n,allowed=[lo,hi]))
            hashes.append(dict(case=c['case_id'],step=k,prompt_sha256=hashlib.sha256(r['sent_prompts'][k].encode()).hexdigest(),raw_sha256=hashlib.sha256(v.encode()).hexdigest()))
        stages={}
        for s in ['P0','P1','P2','P3','N','E']:
            obj=out['parsed'].get('judge_'+s)
            if obj:
                target=int(c['informed_seat']=='A');stages[s]=dict(p_informed_A=obj['p_informed_A'],pick=obj['pick'],correct=obj['pick']==c['informed_seat'],brier=(obj['p_informed_A']-target)**2,insufficient_evidence=obj['insufficient_evidence'])
        rows.append(dict(case=c['case_id'],informed_seat=c['informed_seat'],status=r['status'],replies=len(r['raw']),missing=[k for k in out['steps'] if k not in r['raw']],diagnostic=out['diagnostic'],stages=stages,platform_interventions=len(r.get('platform_observations',[])),issue_flags=r.get('issue_flags',[])))
    result=dict(status='complete' if len(rows)==2 and all(not r['missing'] for r in rows) else 'partial',independent_pairs=1,receipt_audit='passed',cases=rows,deviations=deviations,claim_boundary='One background pair, descriptive only; no grounding or active-questioning causal claim.')
    (ROOT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (RUN/'receipt_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
