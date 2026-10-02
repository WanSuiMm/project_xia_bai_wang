"""Check staged file scope, links, sensitive identifiers and evidence hashes."""
from pathlib import Path
import hashlib, json, re, subprocess
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')[:-1]
bad=[];total=0;links=0
pattern=re.compile(r'[A-Z]:[/\\](?:Users|Storage|deepseek)|/mnt/[a-z]/|(?:192\.168|172\.25)\.\d+\.\d+|https://arena\.ai/c/|BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}')
for name in files:
    if '/runs/' in name or '/screenshots/' in name or '__pycache__' in name:bad.append((name,'excluded path staged'))
    data=subprocess.check_output(['git','show',':'+name],cwd=ROOT);total+=len(data)
    try:text=data.decode('utf-8')
    except UnicodeDecodeError:bad.append((name,'unexpected binary'));continue
    if pattern.search(text):bad.append((name,'sensitive identifier match'))
    if name.endswith('.md'):
        for target in re.findall(r'\]\(([^)]+)\)',text):
            target=target.strip('<>').split('#')[0]
            if not target or '://' in target or target.startswith('mailto:'):continue
            links+=1
            path=(ROOT/name).parent/unquote(target)
            if not path.exists():bad.append((name,'missing link '+target))
pub=ROOT/'xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/published_runs/arena_20261002_direct_pilot01'
manifest=json.loads((pub/'publication_manifest.json').read_text(encoding='utf-8'))
for entry in manifest['records']:
    record=json.loads((pub/'logs'/f'{entry["case_id"]}.json').read_text(encoding='utf-8'))
    for field,key in [('raw','raw_sha256'),('sent_prompts','prompt_sha256')]:
        for step,digest in entry[key].items():
            if hashlib.sha256(record[field][step].encode()).hexdigest()!=digest:bad.append((entry['case_id'],field+' hash mismatch '+step))
print(json.dumps({'staged_files':len(files),'staged_bytes':total,'markdown_links_checked':links,'public_records_hashed':len(manifest['records']),'problems':bad},ensure_ascii=False,indent=2))
if bad:raise SystemExit(2)
