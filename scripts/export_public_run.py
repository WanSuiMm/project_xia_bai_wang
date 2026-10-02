"""Create a sanitized evidence copy; preserve source logs and prompt/reply bytes."""
from pathlib import Path
import hashlib
import json
import re
import shutil

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / 'xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1'
SOURCE = PACKAGE / 'runs/arena_20261002_direct_pilot01'
DEST = PACKAGE / 'published_runs/arena_20261002_direct_pilot01'
DROP = {'session_urls', 'session_url', 'url', 'evidence_screenshot'}

def sanitize(value):
    if isinstance(value, dict):
        return {k: sanitize(v) for k,v in value.items() if k not in DROP}
    if isinstance(value, list): return [sanitize(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r'https://arena\.ai/c/[\w-]+', '[private conversation removed]', value)
        value = re.sub(r'[A-Za-z]:[/\\][^\s"\n]+', '[local path removed]', value)
        value = re.sub(r'(?<!\w)[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[account removed]', value)
    return value

def digest(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = {'source_policy':'Original local run is unchanged and excluded from Git. Published records remove private conversation URLs, screenshots and machine paths.', 'records':[]}
    for path in sorted((SOURCE/'logs').glob('*.json')):
        original=json.loads(path.read_text(encoding='utf-8-sig'))
        public=sanitize(original)
        for field in ('raw','sent_prompts'):
            if public[field]!=original[field]: raise ValueError(f'Sanitizer would change {path.name}:{field}; stop for review')
        target=DEST/'logs'/path.name;target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        manifest['records'].append({'case_id':original['case_id'],'case_sha256':original['case_sha256'],'raw_sha256':{k:digest(v) for k,v in original['raw'].items()},'prompt_sha256':{k:digest(v) for k,v in original['sent_prompts'].items()}})
    for name in ('capture_audit.json','run_status.json','direct_battle_D01.json'):
        public=sanitize(json.loads((SOURCE/name).read_text(encoding='utf-8-sig')))
        (DEST/name).write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name in ('operator_capture.py','audit_capture.py'):
        text=(SOURCE/name).read_text(encoding='utf-8')
        if name=='operator_capture.py':
            text=re.sub(r"NODE = r'[^']+'", "import shutil\nNODE = shutil.which('node')\nif not NODE: raise RuntimeError('Node.js must be available on PATH')", text)
        (DEST/name).write_text(text,encoding='utf-8')
    (DEST/'publication_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Published copies:',len(manifest['records']),'cases; prompt and reply text unchanged.')

if __name__=='__main__': main()
