"""Loopback-only raw-record capture; never contacts or controls Arena."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json, html, subprocess, datetime, sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
CASES = {c['case_id']: c for c in json.loads((ROOT/'data/HOST_ONLY/cases.json').read_text(encoding='utf-8'))}
import shutil
NODE = shutil.which('node')
if not NODE: raise RuntimeError('Node.js must be available on PATH')
JS = """const fs=require('fs'),root=process.argv[1],C=require(root+'/tools/console.js'),D=JSON.parse(fs.readFileSync(root+'/data/HOST_ONLY/console_bundle.json','utf8')),x=JSON.parse(fs.readFileSync(0,'utf8')),c=D.cases.find(c=>c.case_id===x.case_id); const steps=C.stepsFor(c); let prompts={};for(const k of Object.keys(x.sent_prompts||{}))prompts[k]=C.buildPrompt(D,c,x,k);let next=steps.find(k=>!x.raw[k]);let prompt=null;try{if(next)prompt=C.buildPrompt(D,c,x,next);}catch(e){};console.log(JSON.stringify({steps,prompts,next,prompt}));"""

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def record(cid):
    path=RUN/'logs'/f'{cid}.json'
    if path.exists(): return json.loads(path.read_text(encoding='utf-8-sig'))
    c=CASES[cid]; m1='claude-sonnet-5-5-high';m2='gemini-3.8-flash-high'
    return dict(schema_version='xbw.pilot.record/0.1', protocol_version='0.1.0',case_id=cid,
        case_sha256=c['case_sha256'],run_id=RUN.name+'-'+cid,status='in_progress',demo=False,
        metadata=dict(speaker_model=m1 if c['config']=='R1' else m2,judge_model=m2 if c['config']=='R1' else m1,
        platform='Arena',mode='Direct',effort='high (displayed model label); internal configuration unverified',
        temperature='unknown',tools_status='not_verified',started_utc=now(),ended_utc=''),
        raw={},sent_prompts={},manual_questions={},issue_flags=[],notes='',events=[],session_urls={})
def canonical(r):
    cp=subprocess.run([NODE,'-e',JS,str(ROOT)],input=json.dumps(r,ensure_ascii=False),text=True,encoding='utf-8',capture_output=True,check=True)
    return json.loads(cp.stdout)
def page(cid,msg=''):
    r=record(cid); v=canonical(r); v.setdefault('next', None); c=CASES[cid]
    payload=json.dumps(dict(case_id=cid,raw=r['raw'],sent_prompts=r['sent_prompts'],session_urls=r.get('session_urls',{}),rendered_sessions=r.get('rendered_sessions',{})),ensure_ascii=False)
    return '<!doctype html><meta charset="utf-8"><title>Local pilot capture</title><h1>Local pilot capture: '+cid+'</h1><p>'+html.escape(msg)+'</p><p>Next: '+str(v['next'])+'</p><p>Speaker: '+r['metadata']['speaker_model']+'; Judge: '+r['metadata']['judge_model']+'</p><p>Steps: '+html.escape(json.dumps(v['steps']))+'</p><form method="post" action="/save"><label>Snapshot<textarea name="snapshot" rows="8" cols="100">'+html.escape(payload)+'</textarea></label><button>Save exact snapshot</button></form><label>Prompt<textarea rows="10" cols="100">'+html.escape(v['prompt'] or '')+'</textarea></label><label>Case metadata<textarea rows="3" cols="100">'+html.escape(json.dumps(dict(case_id=cid,case_sha256=c['case_sha256'],config=c['config'],steps=v['steps']),ensure_ascii=False))+'</textarea></label>'
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,body,status=200):
        self.send_response(status);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(body.encode())
    def do_GET(self):
        cid=self.path.strip('/') or 'D01'
        if cid not in {'D01','P01','P02','P03','P04'}: return self.send('Unknown case',404)
        self.send(page(cid))
    def do_POST(self):
        from urllib.parse import parse_qs
        try:
            if self.path!='/save':raise ValueError('Unknown path')
            size=int(self.headers.get('Content-Length',0))
            if size>3000000:raise ValueError('Payload too large')
            x=json.loads(parse_qs(self.rfile.read(size).decode())['snapshot'][0]);cid=x['case_id']
            if cid not in {'D01','P01','P02','P03','P04'}:raise ValueError('Unknown case')
            r=record(cid)
            for field in ('raw','sent_prompts'):
                for k,val in x.get(field,{}).items():
                    if not isinstance(val,str):raise ValueError('Raw fields must be strings')
                    if r[field].get(k) and r[field][k]!=val:raise ValueError('Refusing replacement of saved '+k)
                r[field].update(x.get(field,{}))
            r.setdefault('session_urls',{}).update(x.get('session_urls',{}))
            if 'rendered_sessions' in x:
                r['rendered_sessions']=x['rendered_sessions']
            if 'platform_observations' in x:
                r['platform_observations']=x['platform_observations']
            v=canonical(r)
            for k,val in r['sent_prompts'].items():
                if v['prompts'][k]!=val:raise ValueError('Frozen prompt mismatch: '+k)
            if any(k not in v['steps'] for k in r['raw']):raise ValueError('Unknown step')
            complete=all(r['raw'].get(k,'').strip() for k in v['steps'])
            r['status']='completed' if complete else 'in_progress'
            if complete:r['metadata']['ended_utc']=now()
            r['events'].append(dict(at=now(),type='exact_browser_capture_saved',response_count=len(r['raw'])))
            path=RUN/'logs'/f'{cid}.json';path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            self.send(page(cid,'Saved exact raw snapshot; frozen prompts verified. Responses: '+str(len(r['raw']))))
        except Exception as e:self.send(html.escape(str(e)),400)

if __name__=='__main__':
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8766
    print(f'Loopback capture http://127.0.0.1:{port}/D01',flush=True)
    HTTPServer(('127.0.0.1',port),Handler).serve_forever()
