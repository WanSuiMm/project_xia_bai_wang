"""Local-only prompt and durable capture server. No Arena network/API calls."""
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import json, subprocess, shutil, html, datetime

ROOT = Path(__file__).resolve().parents[1] / 'v0_2_math'
RUN = ROOT/'runs/arena_20261002_selvar_pair01'
DATA = json.loads((ROOT/'bundle.json').read_text(encoding='utf-8'))
CASES = {c['case_id']:c for c in DATA['cases']}
NODE = shutil.which('node')
JS = "const fs=require('fs'),root=process.argv[1],C=require(root+'/console.js'),D=JSON.parse(fs.readFileSync(root+'/bundle.json','utf8')),r=JSON.parse(fs.readFileSync(0,'utf8')),c=D.cases.find(c=>c.case_id===r.case_id),steps=C.stepsFor(c),next=steps.find(k=>!r.raw[k]);console.log(JSON.stringify({steps,next,prompt:next?C.buildPrompt(D,c,r,next):'',prompts:Object.fromEntries(Object.keys(r.sent_prompts).map(k=>[k,C.buildPrompt(D,c,r,k)]))}));"
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(cid):
    p=RUN/'logs'/f'{cid}.json'
    if p.exists(): return json.loads(p.read_text(encoding='utf-8'))
    return dict(schema_version='xbw.pilot.record/0.1',protocol_version=DATA['version'],case_id=cid,case_sha256=CASES[cid]['case_sha256'],status='in_progress',demo=False,run_id=RUN.name+'-'+cid,
                metadata=dict(speaker_model='claude-sonnet-5-5-high',judge_model='gemini-3.8-flash-high',platform='Arena',mode='Direct',temperature='unknown',tools_status='not_verified',started_utc=now()),raw={},sent_prompts={},captures={},manual_questions={},issue_flags=[],events=[])
def core(r):
    p=subprocess.run([NODE,'-e',JS,str(ROOT)],input=json.dumps(r),text=True,encoding='utf-8',capture_output=True,check=True)
    return json.loads(p.stdout)
def prior():
    return 'This is a separate prior-only probe, not a game player or judge. Do not browse or use tools.\n'+CASES['M01V1']['public_text']+'\nNo private definition or check answers have been provided. For each of Q1, Q2, Q3, report your subjective probability that the operation is defined. Do not assume a particular familiar definition. Return one JSON object: {"p_pass":{"Q1":0.5,"Q2":0.5,"Q3":0.5},"insufficient_evidence":true,"reason":"At most 50 English words"}.'
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,s,code=200):
        self.send_response(code);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(s.encode())
    def page(self,cid,msg=''):
        if cid=='prior': key='prior';prompt=prior();done=(RUN/'prior.json').exists()
        else:
            r=read(cid);v=core(r);key=v.get('next') or 'completed';prompt=v['prompt'];done=key=='completed'
        return '<meta charset="utf-8"><title>Selvar capture</title><h1>'+cid+'</h1><p>'+html.escape(msg)+'</p><p id="step">'+key+'</p><textarea id="prompt" rows="12" cols="100">'+html.escape(prompt)+'</textarea><form method="post"><input name="cid" value="'+cid+'"><input name="step" value="'+key+'"><label>Exact capture JSON<textarea name="capture" id="capture" rows="8" cols="100"></textarea></label><button '+('disabled' if done else '')+'>Save capture</button></form>'
    def do_GET(self):
        cid=self.path.strip('/')
        if cid not in CASES and cid!='prior': return self.send('Unknown case',404)
        self.send(self.page(cid))
    def do_POST(self):
        try:
            x=parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode());cid=x['cid'][0];key=x['step'][0];cap=json.loads(x['capture'][0])
            if cid=='prior':
                path=RUN/'prior.json'
                if path.exists(): raise ValueError('Prior already saved')
                if cap['prompt']!=prior(): raise ValueError('Prior prompt mismatch')
                path.write_text(json.dumps(dict(prompt=prior(),capture=cap,saved_utc=now()),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            else:
                r=read(cid);v=core(r)
                if key!=v.get('next'): raise ValueError('Unexpected step')
                if cap['prompt']!=v['prompt']: raise ValueError('Prompt mismatch')
                if not cap.get('raw','').strip(): raise ValueError('Empty raw response')
                r['raw'][key]=cap['raw'];r['sent_prompts'][key]=cap['prompt'];r['captures'][key]=cap
                r['events'].append(dict(at=now(),step=key,type='ui_capture_saved'))
                v=core(r)
                if any(r['sent_prompts'][k]!=v['prompts'][k] for k in r['sent_prompts']): raise ValueError('Frozen receipt mismatch')
                r['status']='completed' if not v.get('next') else 'in_progress'
                if r['status']=='completed': r['metadata']['ended_utc']=now()
                (RUN/'logs'/f'{cid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                status=json.loads((RUN/'status.json').read_text());status['completed_replies']=sum(len(read(c)['raw']) for c in CASES);status['status']='completed' if status['completed_replies']==28 else 'in_progress';status['updated_utc']=now();(RUN/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
            self.send(self.page(cid,'Saved exact capture'))
        except Exception as e:self.send(html.escape(str(e)),400)
if __name__=='__main__':
    print('Selvar local capture on http://127.0.0.1:8772/M01V1',flush=True)
    HTTPServer(('127.0.0.1',8772),Handler).serve_forever()
