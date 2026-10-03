"""Create six fresh synthetic fixtures; never replace an existing freeze."""
from pathlib import Path
import datetime,hashlib,itertools,json,random
ROOT=Path(__file__).resolve().parents[1]/'v0_4_active'
RUN=ROOT/'runs/arena_20261003_active01'
SEED=2026100304
SPECS=[('AV01','Rethin latch','PASS iff exactly one of x and y is 1; z has no effect.',lambda x,y,z:x!=y),
 ('AV02','Nuvor gate','PASS iff (x=1 and y=1) or (x=0 and z=1). No other condition applies.',lambda x,y,z:y if x else z),
 ('AV03','Delvek marker','PASS iff exactly two of x,y,z are 1. No other condition applies.',lambda x,y,z:x+y+z==2),
 ('AV04','Sarnel seal','PASS iff x differs from the conjunction of y and z: x XOR (y AND z). No other condition applies.',lambda x,y,z:bool(x)!=bool(y and z)),
 ('AV05','Omrek latch','In standard mode e=0, PASS iff x=1, regardless of y,z. In enhanced mode e=1, PASS iff y differs from z. The enhanced mode is outside the allowed menu.',lambda x,y,z:bool(x)),
 ('AV06','Tavren gate','In standard mode e=0, PASS iff x=1 and z=1, regardless of y. In enhanced mode e=1, PASS iff y=0. The enhanced mode is outside the allowed menu.',lambda x,y,z:bool(x and z))]
def main():
 if (ROOT/'bundle.json').exists():raise RuntimeError('Frozen bundle exists')
 rng=random.Random(SEED);cases=[]
 for cid,term,rule,f in SPECS:
  negative=cid in ['AV05','AV06']
  inputs=list(itertools.product([0,1],repeat=3));rng.shuffle(inputs)
  queries=[dict(id=f'Q{i+1}',x=x,y=y,z=z) for i,(x,y,z) in enumerate(inputs)]
  public=f'{term} is a newly defined fictional bench-fixture acceptance procedure. Three independently set binary inputs x,y,z are recorded; 0 means inactive and 1 active. PASS means the green acceptance lamp is on after one evaluation; FAIL means it is off. The fixture is deterministic, with no noise, memory, history, damage, unstated interaction or external source. Ordinary engineering does not determine this sampled acceptance rule. Tests only ask this lamp result, not wording, manufacturing provenance or unobservable internals. '
  if negative:
   mode='standard mode e=0 (enhanced mode is unavailable)'
   public+='A public standard-mode certificate fully specifies the permitted tests: '+('with e=0, PASS iff x=1, independent of y,z.' if cid=='AV05' else 'with e=0, PASS iff x=1 and z=1, independent of y.')+' The private reference also specifies an enhanced e=1 mode, but changing e or testing enhanced mode is not allowed. Descriptions of enhanced mode cannot be independently verified here.'
  else:
   mode='ordinary mode'
   public+='The private reference supplies the exact complete Boolean rule over x,y,z. Only the eight listed inputs may be tested; no rule is published.'
  c=dict(case_id=cid,term=term,design_class='verification_equivalent_control' if negative else 'identifiable_target',informed_seat=rng.choice(['A','B']),generation_first=rng.choice(['A','B']),public_text=public,private_text=rule,allowed_mode=mode,queries=queries,gold={q['id']:'PASS' if f(q['x'],q['y'],q['z']) else 'FAIL' for q in queries})
  c['case_sha256']=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest();cases.append(c)
 bundle=dict(version='0.4.0-active-qualification01',seed=SEED,frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),speaker_model='glm-5.2 (max)',judge_model='gemini-3.8-flash-high',mode='Direct',cases=cases,judge_replicates=3,verification_cap=8,maximum_speaker_calls=12,maximum_judge_replies=162,scope='Six cases; four identifiable targets, two public-standard-mode verification-equivalent controls. Actual diagnostic labels derive from frozen speaker predictions; collisions/errors retained.')
 ROOT.mkdir(exist_ok=True);(RUN/'logs').mkdir(parents=True,exist_ok=True);(RUN/'trajectories').mkdir(exist_ok=True)
 (ROOT/'bundle.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 for c in cases:
  (RUN/'logs'/(c['case_id']+'.json')).write_text(json.dumps(dict(case_id=c['case_id'],case_sha256=c['case_sha256'],status='not_started',raw={},sent_prompts={},captures={},events=[]),indent=2)+'\n')
  for j in range(1,4):
   (RUN/'trajectories'/f'{c["case_id"]}_J{j}.json').write_text(json.dumps(dict(case_id=c['case_id'],judge_id=f'J{j}',status='not_started',decisions=[],observations=[],events=[]),indent=2)+'\n')
 sha=hashlib.sha256((ROOT/'bundle.json').read_bytes()).hexdigest()
 (RUN/'status.json').write_text(json.dumps(dict(status='prepared',bundle_sha256=sha,planned_cases=6,planned_trajectories=18,automatic_monitor=False),indent=2)+'\n')
 print(json.dumps(dict(bundle_sha256=sha,assignments=[{k:c[k] for k in ['case_id','informed_seat','generation_first']} for c in cases])))
if __name__=='__main__':main()
