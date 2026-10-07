"""Make deterministic exhaustive sentence/clause coverage inputs; no provider dependencies."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'epistemic_boundary_mimicry/analysis/offline_coding_20261005'
OUT=ROOT/'epistemic_boundary_mimicry/analysis/claim_audit_20261007'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def units(text):
    # A reproducible coverage grid, not a semantic atomizer. Preserve exact offsets.
    start=0;result=[]
    for end in [m.end() for m in re.finditer(r';|[.!?](?=\s+(?:[A-Z0-9(\"\u201c])|\s*$)|\n\n',text)]+[len(text)]:
        a=start;b=end
        while a<b and text[a].isspace():a+=1
        while b>a and text[b-1].isspace():b-=1
        if a<b:result.append({'start':a,'end':b,'text':text[a:b]})
        start=end
    return result
def main():
    destination=OUT/'inputs'
    if destination.exists():raise SystemExit('Preserve prior prepared inputs')
    destination.mkdir(parents=True);(OUT/'labels').mkdir()
    hashes={};counts={'trajectories':0,'answers':0,'units':0,'asks':0}
    for p in sorted((OLD/'inputs').glob('*.json')):
        x=read(p);x['public_context']=read(OLD/'public_contexts.json')[x['id']]
        for seat,ref in x['references'].items():
            ref['source_units']=[{'id':i,**u} for i,u in enumerate(units(ref['source_text']))]
        for m in x['messages']:
            if m['role'] in ['A','B']:
                m['units']=[{'id':f"{m['message_index']}.{i}",**u} for i,u in enumerate(units(m['reply']))]
                counts['answers']+=1;counts['units']+=len(m['units'])
            else:counts['asks']+=1
        q=destination/p.name;q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        hashes[p.name]=sha(q);counts['trajectories']+=1
    manifest={'scope':'all canonical API EB01-EB06; retrospective sentence/clause grid',
        'protocol_sha256_lf':sha(OUT/'PROTOCOL.md'),'original_freeze_sha256_lf':sha(OLD/'freeze.json'),
        'inputs':hashes,'counts':counts,'experimental_api_calls':0}
    (OUT/'freeze.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(json.dumps(counts))
if __name__=='__main__':main()
