"""Export allowlisted evidence, preserving exact submitted prompts and final replies."""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parents[1] / 'v0_4_active'
RUN_ID = 'arena_20261003_active01'
SOURCE = BASE / 'runs' / RUN_ID
DEST = BASE / 'published_runs' / RUN_ID


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def fields(value, keys):
    return {k: value[k] for k in keys if k in value}


def capture(value):
    return fields(value, ['raw', 'prompt', 'visible_model', 'saved_utc'])


def events(value):
    return [fields(e, ['at', 'type', 'step', 'seat', 'index']) for e in value]


def main():
    manifest = {'policy': 'Original raw run unchanged. Account DOM, model reasoning panels, private sessions, tab identifiers, screenshots and anonymous candidate text excluded. Submitted prompts and captured final JSON replies are unchanged.', 'records': []}
    for folder in ['logs', 'trajectories']:
        for path in sorted((SOURCE / folder).glob('*.json')):
            r = read(path)
            public = fields(r, ['case_id', 'case_sha256', 'judge_id', 'status', 'raw', 'sent_prompts', 'diagnostic', 'frozen_utc', 'ended_utc', 'observations'])
            public['events'] = events(r.get('events', []))
            if 'captures' in r:
                public['captures'] = {s: capture(v) for s, v in r['captures'].items()}
            if 'sessions' in r:
                public['sessions'] = {s: fields(v, ['sent_utc']) for s, v in r['sessions'].items()}
            if 'decisions' in r:
                public['decisions'] = [capture(v) for v in r['decisions']]
            if 'pending' in r:
                public['pending'] = fields(r['pending'], ['prompt', 'index', 'sent_utc'])
                public['pending']['sent'] = bool(r['pending'].get('url'))
            if 'invalid_decision' in r:
                public['invalid_decision'] = capture(r['invalid_decision'])
            relative = f'{folder}/{path.name}'
            write(DEST / relative, public)
            # Receipt strings are preserved by structural projection, never rewritten.
            for key in ['raw', 'sent_prompts']:
                if key in r:
                    assert public[key] == r[key]
            if 'decisions' in r:
                assert [(d['raw'], d['prompt']) for d in public['decisions']] == [(d['raw'], d['prompt']) for d in r['decisions']]
            manifest['records'].append({'file': relative, 'sha256_lf_utf8': hashlib.sha256((DEST / relative).read_bytes().replace(b'\r\n', b'\n')).hexdigest()})
    for name in ['status.json', 'freeze_audit.json']:
        write(DEST / name, read(SOURCE / name))
    write(DEST / 'publication_manifest.json', manifest)
    (DEST / 'README.md').write_text('# Published Active Verification evidence\n\nRead [results](../../RESULTS.md), then [protocol](../../PROTOCOL.md), before individual logs. Six cases, 18 planned trajectories, platform missing retained. Prompts and final JSON replies are preserved verbatim; UI/account data, private sessions, model reasoning panels and anonymous candidate text are excluded. No new model calls were made for publication. These records contain private role cards and Host truth; never forward the complete directory to a tested role.\n', encoding='utf8')
    print(json.dumps({'exported_records': len(manifest['records'])}))


if __name__ == '__main__':
    main()
