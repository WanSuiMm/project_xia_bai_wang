"""Publish a fixed nine-configuration slice; never modify local raw evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'naturalistic_study_1'
DEST = BASE / 'published_runs/nine_completed_20261003'
RUNS = ['arena_20261003_naturalistic01', 'arena_20261003_naturalistic_resume01',
        'arena_20261003_naturalistic_judge_recovery01']
EXPECTED = {'N01_D1', 'N01_D2', 'N02_D1', 'N02_D2', 'N03_D1', 'N03_D2',
            'N04_D2', 'N05_D1', 'N05_D2'}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def project(value, keys):
    return {k: value[k] for k in keys if k in value}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def main():
    if DEST.exists():
        raise SystemExit('Snapshot already exists; preserve it and use a new snapshot name.')
    selected, coverage, provenance, cases = {}, [], [], {}
    for run_id in RUNS:
        run = BASE / 'runs' / run_id
        bundle = read(run / 'bundle.json')
        freeze = read(run / 'freeze.json')
        assert hashlib.sha256((run / 'bundle.json').read_bytes()).hexdigest() == freeze['bundle_sha256']
        provenance.append({'run_id': run_id, 'original_bundle_sha256': freeze['bundle_sha256']})
        for path in sorted((run / 'trajectories').glob('*.json')):
            r = read(path)
            config = r['id'].replace('_Jretry01', '')
            sent = [m for m in r['messages'] if m.get('sent_utc')]
            coverage.append({'run_id': run_id, 'record_id': r['id'], 'configuration_id': config,
                             'status': r['status'], 'asks': r['asks'], 'sends': len(sent),
                             'new_replies': sum(bool(m.get('reply')) for m in sent),
                             'inherited_replies': sum(bool(m.get('reply') and m.get('inherited_from')) for m in r['messages'])})
            if r['status'] != 'completed':
                continue
            assert config in EXPECTED and config not in selected
            public = project(r, ['id', 'case_id', 'speaker_model', 'judge_model', 'knower',
                                 'status', 'asks', 'terminal', 'correct'])
            public.update(run_id=run_id, configuration_id=config)
            public['messages'] = [project(m, ['role', 'prompt', 'model', 'question_index',
                'prepared_utc', 'sent', 'sent_utc', 'raw', 'captured_utc', 'parsed', 'reply',
                'original_sent_utc', 'inherited_from']) for m in r['messages']]
            public['events'] = [project(e, ['type', 'role', 'at', 'question_index']) for e in r.get('events', [])]
            for original, projected in zip(r['messages'], public['messages']):
                for key in ['prompt', 'raw', 'parsed']:
                    if key in original:
                        assert original[key] == projected[key]
            selected[config] = public
            case = next(c for c in bundle['cases'] if c['case_id'] == r['case_id'])
            if case['case_id'] in cases:
                assert cases[case['case_id']] == case
            cases[case['case_id']] = case
    assert set(selected) == EXPECTED
    write(DEST / 'bundle.json', {'publication_kind': 'completed subset, not original frozen bundle',
          'original_planned_configurations': 24, 'current_completion_cap': 12,
          'seat_seed': 2026100305, 'cases': [cases[k] for k in sorted(cases)],
          'source_provenance': provenance})
    write(DEST / 'attempt_coverage.json', {'scope': 'All attempt statuses at this publication cutoff; incomplete dialogue is not exported in this nine-completed slice.',
          'records': coverage, 'local_recovery_session_audit': 'Original speaker-session reuse checked locally before publication; private session URLs excluded.'})
    for config, receipt in sorted(selected.items()):
        write(DEST / 'trajectories' / (config + '.json'), receipt)
    manifest = {'policy': 'Exact prompt, visible final raw reply and parsed reply strings preserved. Account/UI DOM, private sessions, tab IDs, reasoning panels and anonymous candidates excluded. Only sources for completed cases N01-N05 are released; unused fresh sources remain private.',
                'records': []}
    for path in sorted(DEST.rglob('*.json')):
        manifest['records'].append({'file': path.relative_to(DEST).as_posix(),
            'sha256_lf_utf8': hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()})
    write(DEST / 'publication_manifest.json', manifest)
    (DEST / 'README.md').write_bytes(b'# Nine completed configurations\n\nStart with [snapshot results](../../SNAPSHOT_RESULTS.md), then [protocol](../../PROTOCOL.md) and [scope amendment](../../COLLECTION_SCOPE.md). Individual trajectories are secondary evidence. `bundle.json` is a public subset, not the original full frozen bundle. Prompts and final visible replies are unchanged; UI/account data, private sessions, reasoning panels and anonymous candidates are omitted. The original cutoff, serial continuation and explicit N02 judge recovery remain separate attempts in `attempt_coverage.json`. Nine completed unique configurations, across five dossiers, are released. Remaining fresh sources are private. These files contain source access labels and full dossiers: never forward them wholesale to tested roles. No new model calls were made for publication.\n')
    print(json.dumps({'completed_exported': len(selected), 'published_cases': len(cases), 'manifest_files': len(manifest['records'])}))

if __name__ == '__main__':
    main()
