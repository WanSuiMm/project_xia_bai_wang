"""Export explicit research fields; never publish UI DOM, sessions or account data."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
RUNS = [('v0_2_math', 'arena_20261002_selvar_pair01'),
        ('v0_2_other', 'arena_20261002_other_pairs01')]
PRIVATE = re.compile(r'https://arena\.ai/c/|[A-Za-z]:[/\\]+(?:Users|Storage|deepseek)|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|BEGIN .*PRIVATE KEY|(?:192\.168|172\.25)\.\d+\.\d+')

def select(obj, fields):
    return {key: obj[key] for key in fields if key in obj}

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def export():
    for domain, run in RUNS:
        source = ROOT/domain/'runs'/run
        dest = ROOT/domain/'published_runs'/run
        dest.mkdir(parents=True, exist_ok=True)
        manifest = {'policy': 'Original prompts and replies unchanged. UI DOM, session URLs, account data, screenshots and pending browser handles omitted.', 'records': [], 'priors': []}
        for path in sorted((source/'logs').glob('*.json')):
            original = json.loads(path.read_text(encoding='utf-8-sig'))
            public = select(original, ['schema_version','protocol_version','case_id','case_sha256','run_id','status','demo','raw','sent_prompts','manual_questions','issue_flags'])
            public['metadata'] = select(original.get('metadata', {}), ['speaker_model','judge_model','platform','mode','temperature','tools_status','started_utc','ended_utc'])
            public['captures'] = {key: select(value, ['prompt','raw','visible_model','model','saved_utc']) for key,value in original['captures'].items()}
            public['events'] = [select(value, ['at','type','step','action']) for value in original.get('events', [])]
            public['platform_observations'] = [select(value, ['at','type','kind','step','action']) for value in original.get('platform_observations', [])]
            text = json.dumps(public, ensure_ascii=False, indent=2)+'\n'
            assert not PRIVATE.search(text), path.name
            assert public['raw'] == original['raw'] and public['sent_prompts'] == original['sent_prompts']
            (dest/'logs').mkdir(exist_ok=True)
            (dest/'logs'/path.name).write_text(text, encoding='utf-8')
            manifest['records'].append({'case_id': original['case_id'], 'prompt_sha256': {key:digest(value) for key,value in original['sent_prompts'].items()}, 'raw_sha256': {key:digest(value) for key,value in original['raw'].items()}})
        for path in sorted(source.glob('prior*.json')):
            original = json.loads(path.read_text(encoding='utf-8-sig'))
            public = select(original, ['prompt','raw','status','issue_flags','saved_utc'])
            public['capture'] = select(original.get('capture',{}), ['prompt','raw','visible_model','model','saved_utc'])
            text = json.dumps(public, ensure_ascii=False, indent=2)+'\n'
            assert not PRIVATE.search(text), path.name
            (dest/path.name).write_text(text, encoding='utf-8')
            manifest['priors'].append({'file':path.name, 'prompt_sha256':digest(original['prompt']), 'raw_sha256':digest(original['raw'])})
        (dest/'publication_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
        (dest/'README.md').write_text('# Published evidence\n\nRead ../../RESULTS.md first, then ../../PROTOCOL.md and ../../analysis.json. These records contain host answers and private role prompts; do not forward an entire log to a tested role.\n\nThe logs preserve exact prompts, raw JSON replies, failed-send event types and platform intervention steps. Publication omits UI DOM (including anonymous candidates), account information, private conversation URLs, screenshots and browser handles. Hashes bind the published prompt and reply strings to the local originals. Missing responses remain missing; no model error is inferred from a platform failure.\n', encoding='utf-8')
        print(domain, len(manifest['records']), 'records;', len(manifest['priors']), 'priors')

if __name__ == '__main__':
    export()
