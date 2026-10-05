"""Freeze retrospective codebook/cohort and produce role-source annotation inputs, no API."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'epistemic_boundary_mimicry'
OLD=BASE/'analysis/transcript_reuse_20261005'
OUT=BASE/'analysis/offline_coding_20261005'


def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def main():
 if OUT.exists():raise SystemExit('Preserve frozen coding inputs')
 inventory=read(OLD/'inventory.json');replay=read(OLD/'frozen_terminal_blind_dialogues.json')
 complete=[r for r in replay['records'] if r['default_endpoint_replay_eligible']]
 assert len(complete)==7
 OUT.mkdir(parents=True);(OUT/'inputs').mkdir();(OUT/'annotations').mkdir()
 cohort=[{'id':r['id'],'payload_sha256':r['payload_sha256'],'payload':r['payload']} for r in complete]
 write(OUT/'replay_cohort.json',{'rule':'all seven complete canonical Frozen; no outcome filtering',
   'excluded_partial_ids':[r['id'] for r in replay['records'] if not r['default_endpoint_replay_eligible']],
   'records':cohort,'api_calls':0})
 for row in inventory['trajectories']:
  path=ROOT/row['evidence_path'];assert sha(path)==row['evidence_sha256_lf']
  r=read(path);b=read(path.parent/'bundle.json')
  bb=b[r['id']] if path.parent.name=='go_frozen_pair_completed_20261004' else b
  if 'sources' in bb:sources=bb['sources']
  elif 'cases' in bb:sources=next(c['sources'] for c in bb['cases'] if c['case_id']==r['case_id'])
  else:sources=[bb['source']]
  prompts=bb['role_initial_prompts'][r['id']];references={}
  for seat in ['A','B']:
   matches=[s for s in sources if s['source_text'] in prompts[seat]]
   if matches:assert len(matches)==1;references[seat]={'reference_type':'own_source','source_text':matches[0]['source_text']}
   else:
    target=next((s for s in sources if s.get('source_id')==r.get('target_source_id')),sources[0])
    references[seat]={'reference_type':'target_source_proxy_for_bluffer','source_text':target['source_text']}
  messages=[]
  for i,m in enumerate(r['messages']):
   v=m.get('parsed')
   if m.get('reply') is False or not isinstance(v,dict) or m.get('setup'):continue
   if m['role']=='J' and v.get('action')=='ASK':messages.append({'message_index':i,'role':'J','question_index':m['question_index'],**v})
   elif m['role'] in ['A','B'] and 'reply' in v:messages.append({'message_index':i,'role':m['role'],'question_index':m['question_index'],'reply':v['reply']})
  value={'id':r['id'],'case_id':r['case_id'],'condition':r['condition'],'status':r['status'],
   'references':references,'messages':messages,'terminal':r.get('terminal'),
   'evidence_path':row['evidence_path'],'evidence_sha256_lf':row['evidence_sha256_lf']}
  write(OUT/'inputs'/(r['id']+'.json'),value)
 write(OUT/'freeze.json',{'codebook_sha256_lf':sha(BASE/'analysis/CODEBOOK_20261005.md'),
  'inventory_sha256_lf':sha(OLD/'inventory.json'),'cohort_sha256_lf':sha(OUT/'replay_cohort.json'),
  'inputs':{p.name:sha(p) for p in sorted((OUT/'inputs').glob('*.json'))},
  'freeze_before_annotation':not any((OUT/'annotations').iterdir()),'api_calls':0})
 print(json.dumps({'inputs':13,'complete_replay_cohort':7,'partial_excluded':1,'frozen':True,'api_calls':0}))


if __name__=='__main__':main()
