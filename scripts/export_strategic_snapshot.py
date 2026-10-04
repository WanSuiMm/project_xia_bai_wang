"""Export six first-completed endpoints without changing local receipts."""
import hashlib
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'strategic_bluff_pilot'
DEST = BASE / 'published_runs/six_completed_20261004'
RUNS = ['arena_20261003_strategic01', 'arena_20261003_strategic_retry01',
        'arena_20261003_strategic_recovery02', 'arena_20261003_strategic_recovery03']
EXPECTED = {'S01_D1_natural', 'S01_D1_strong', 'S01_D2_natural',
            'S01_D2_strong', 'S02_D1_strong', 'S02_D2_natural'}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def project(value, keys):
    return {k: value[k] for k in keys if k in value}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))

def main(completed=False):
    global DEST, RUNS, EXPECTED
    if completed:
        DEST = BASE/'published_runs/eight_completed_20261004'
        RUNS = RUNS+['arena_20261004_strategic_completion04']
        EXPECTED = EXPECTED|{'S02_D1_natural','S02_D2_strong'}
    if DEST.exists():
        raise SystemExit('Preserve the existing snapshot; choose a new name for another cutoff.')
    selected, coverage, provenance, amendments = {}, [], [], []
    bundle = read(BASE / 'runs' / RUNS[0] / 'bundle.json')
    for name in RUNS:
        run = BASE / 'runs' / name
        freeze = read(run / 'freeze.json')
        assert hashlib.sha256((run/'bundle.json').read_bytes()).hexdigest() == freeze['bundle_sha256']
        provenance.append({'run_id': name, 'original_bundle_sha256': freeze['bundle_sha256']})
        if (run/'question_limit_amendment.json').exists():
            amendments.append({'run_id':name,**read(run/'question_limit_amendment.json')})
        for path in sorted((run/'trajectories').glob('*.json')):
            r = read(path)
            new = [m for m in r['messages'] if not m.get('inherited_from_run')]
            coverage.append({'run_id': name, 'id': r['id'], 'status': r['status'], 'asks': r['asks'],
                'physical_submissions': sum(bool(m.get('sent_utc'))+len(m.get('retry_sends', [])) for m in new),
                'complete_replies': sum(bool(m.get('reply')) for m in new),
                'retained_partials': sum(m.get('capture_format')=='incomplete_final_visible_wrapper' for m in new),
                'inherited_openings': sum(bool(m.get('inherited_from_run')) for m in r['messages']),
                'own_partial_context_retry': any(e.get('type')=='authorized_incomplete_followup_retry' for e in r.get('events', []))})
            if r['status'] != 'completed' or r['id'] in selected:
                continue
            public = project(r, ['id','case_id','speaker_model','judge_model','knower','condition',
                                 'block','status','asks','terminal','correct'])
            public['run_id'] = name
            public['messages'] = []
            for m in r['messages']:
                p = project(m, ['role','prompt','model','question_index','prepared_utc','sent',
                    'sent_utc','raw','captured_utc','parsed','reply','capture_format','inherited_from_run'])
                p['transport_retries'] = [project(x, ['sent_utc','method','reason','prompt_unchanged']) for x in m.get('retry_sends', [])]
                assert all(p[k] == m[k] for k in ['prompt','raw','parsed'] if k in m)
                public['messages'].append(p)
            selected[r['id']] = public
    assert set(selected) == EXPECTED
    write(DEST/'bundle.json', {**project(bundle, ['study','seed','max_asks','models','speaker_template',
        'bluffer_templates','judge_template','cases','trajectories','source_hashes']),
        'publication_kind':'First completed endpoints across authorized attempts; not the original cutoff',
        'source_provenance': provenance})
    if amendments:
        write(DEST/'question_limit_amendments.json',{'records':amendments})
    write(DEST/'attempt_coverage.json', {'records': coverage,
        'scope':'All 21 attempt statuses; incomplete dialogue remains local. Inherited openings are counted once.'})
    for key, receipt in sorted(selected.items()):
        write(DEST/'trajectories'/f'{key}.json', receipt)
    manifest = {'policy':'Exact prompts and final visible raw and parsed replies. No account, UI DOM, tab identifiers, private session URLs, reasoning panels or anonymous candidates. Both attempted sources released. No model calls for publication.', 'records': []}
    for path in sorted(DEST.rglob('*.json')):
        manifest['records'].append({'file': path.relative_to(DEST).as_posix(),
            'sha256_lf_utf8': hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()})
    write(DEST/'publication_manifest.json', manifest)
    text = '# Six first-completed endpoints\n\nRead [snapshot results](../../SNAPSHOT_RESULTS.md), [protocol](../../PROTOCOL.md), then [retry amendments](../../RETRY_PROTOCOL.md). Individual trajectories are secondary evidence. Six of eight configured slots completed, across two fictional dossiers. The coverage ledger retains original and recovery failures; no missing request is scored as wrong. Exact prompts and final visible replies are preserved, private browser data excluded. Bundle contains source and gold labels: do not send it wholesale to tested roles. No new model calls were made for publication.\n'
    if completed:
        text = '# Eight first-completed endpoints\n\nRead [completed results](../../COMPLETED_RESULTS.md), [original protocol](../../PROTOCOL.md), then [completion and question-limit amendment](../../COMPLETION04_PROTOCOL.md). Eight slots completed across two fictional dossiers. Six endpoints used the frozen ten-ASK protocol; the two last endpoints use an amended continuation: strong receives removal of the cap after six ASK actions, natural starts without a cap. The latter uses fresh A/B/J sessions; strong inherits complete openings. Both Judges stopped themselves. Original failures and the earlier six-endpoint public snapshot remain separate. Exact prompts and final visible replies preserved; account/UI/session data excluded. Bundle contains source and gold labels: do not forward wholesale to tested roles. No provider calls for publication.\n'
    (DEST/'README.md').write_text(text,encoding='utf-8')
    print(json.dumps({'exported':len(selected),'attempt_records':len(coverage)}))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--completed',action='store_true')
    main(parser.parse_args().completed)
