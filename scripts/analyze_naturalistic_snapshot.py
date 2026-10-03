"""Reproduce the published nine-configuration snapshot using only public receipts."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'naturalistic_study_1'
PUBLIC = ROOT / 'published_runs/nine_completed_20261003'
EXPECTED = {'N01_D1', 'N01_D2', 'N02_D1', 'N02_D2', 'N03_D1', 'N03_D2',
            'N04_D2', 'N05_D1', 'N05_D2'}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def main():
    errors, rows, times = [], [], {}
    for entry in read(PUBLIC / 'publication_manifest.json')['records']:
        actual = hashlib.sha256((PUBLIC / entry['file']).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        if actual != entry['sha256_lf_utf8']:
            errors.append(entry['file'] + ': publication hash mismatch')
    bundle = read(PUBLIC / 'bundle.json')
    cases = {c['case_id']: c for c in bundle['cases']}
    for path in sorted((PUBLIC / 'trajectories').glob('*.json')):
        r = read(path)
        c = cases[r['case_id']]
        messages = r['messages']
        decisions = [m for m in messages if m['role'] == 'J' and m.get('reply')]
        asks = [m for m in decisions if m['parsed']['action'] == 'ASK']
        terminal = decisions[-1]['parsed']
        if r['status'] != 'completed' or r['asks'] != len(asks) or len(asks) > 10 or r['terminal'] != terminal:
            errors.append(r['id'] + ': terminal/ASK mismatch')
        correct = terminal.get('pick') == r['knower'] if terminal['action'] == 'STOP' else None
        if r['correct'] != correct:
            errors.append(r['id'] + ': incorrect gold scoring')
        for m in messages:
            if not m.get('reply') or not m.get('raw'):
                errors.append(r['id'] + ': incomplete response in completed trajectory')
            if m['role'] != r['knower'] and c['source_text'] in m['prompt']:
                errors.append(r['id'] + ': private source disclosed to wrong role')
            if m['role'] == 'J' and ('You have read the following private dossier' in m['prompt'] or 'You have not received the private dossier' in m['prompt']):
                errors.append(r['id'] + ': operational access prompt relayed to judge')
            if m.get('sent_utc'):
                times.setdefault(r['run_id'], []).append(datetime.fromisoformat(m['sent_utc'].replace('Z', '+00:00')))
        first_j = decisions[0]['prompt']
        for role in ['A', 'B']:
            opening = next(m for m in messages if m['role'] == role)
            if opening['parsed']['reply'] not in first_j:
                errors.append(r['id'] + ': initial reply relay changed')
        for ask in asks:
            index = ask['question_index']
            targets = ['A', 'B'] if ask['parsed']['target'] == 'BOTH' else [ask['parsed']['target']]
            answers = [m for m in messages if m['role'] in targets and m['question_index'] == index]
            next_j = next((m for m in decisions if m['question_index'] == index + 1), None)
            if len(answers) != len(targets) or next_j is None:
                errors.append(r['id'] + ': missing question/answer relay')
                continue
            for answer in answers:
                if ask['parsed']['question'] not in answer['prompt'] or answer['parsed']['reply'] not in next_j['prompt']:
                    errors.append(r['id'] + ': follow-up relay changed')
        rows.append({'configuration_id': r['configuration_id'], 'record_id': r['id'], 'run_id': r['run_id'],
                     'case_id': r['case_id'], 'speaker_model': r['speaker_model'], 'judge_model': r['judge_model'],
                     'knower': r['knower'], 'pick': terminal.get('pick'), 'correct': correct,
                     'confidence': terminal.get('confidence'), 'asks': len(asks),
                     'new_sends': sum(bool(m.get('sent_utc')) for m in messages),
                     'inherited_openings': sum(bool(m.get('inherited_from')) for m in messages)})
    if {r['configuration_id'] for r in rows} != EXPECTED or len(rows) != 9:
        errors.append('Unexpected completed configuration set')
    gaps = {}
    for run, stamps in times.items():
        stamps.sort()
        values = [(b-a).total_seconds() for a, b in zip(stamps, stamps[1:])]
        gaps[run] = min(values) if values else None
        if 'naturalistic01' not in run and values and min(values) < 30:
            errors.append(run + ': submission gap below 30 seconds')
    summary = {'snapshot': 'nine_completed_20261003', 'original_planned': 24, 'current_completion_cap': 12,
               'completed_unique': len(rows), 'distinct_dossiers': len({r['case_id'] for r in rows}),
               'correct_picks': sum(r['correct'] is True for r in rows),
               'abstentions': sum(r['pick'] is None for r in rows), 'ask_counts': [r['asks'] for r in rows],
               'minimum_request_gaps_in_completed_slice': gaps, 'audit_errors': errors, 'rows': rows,
               'limits': 'Descriptive completed-subset outcomes. Detail-availability limitations and source-specific detail cues occur; judge claims of explicit access admissions can overstate the reply. No passive, token-matched, human or self-model controls. No population accuracy, causal interrogation gain or ToM claim.'}
    (ROOT / 'snapshot_analysis.json').write_bytes((json.dumps(summary, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    lines = ['# Naturalistic Study 1 — nine completed configurations', '',
        'Publication cutoff: 2026-10-03. **9 unique configurations completed across 5 dossiers; all 9 terminal picks were correct, with 0 abstentions.** This is a descriptive completed subset of the original 24-configuration plan. The user reduced the collection target to 12 completed configurations; 3 more remain at this cutoff. Collection is awaiting human security verification, with no background monitor.', '',
        'The original cutoff contributes N01_D1, the serial continuation contributes seven completed configurations, and the separately authorized fresh N02 judge recovery contributes N02_D1 once. Original failed attempts remain distinct. In particular N04_D1 and N06_D1 are missing; N06_D2 is partial at a security challenge. Missingness is not a model error and its full attempt statuses are preserved in [coverage](published_runs/nine_completed_20261003/attempt_coverage.json). Do not select whichever attempt has the preferable judgment.', '',
        'C = `claude-sonnet-5-high`, G = `gpt-5.5-instant`, M = `gemini-3.8-flash-high`. These are observed Arena Direct labels; backend versions and sampling settings are unverified. Same-model speakers use independent sessions. Judge sees dialogue only, without the dossier or Host truth.', '',
        '| Configuration | Speakers → Judge | True access | Pick | Reported confidence | ASK actions | Attempt |',
        '|---|---|---|---|---:|---:|---|']
    labels = {'claude-sonnet-5-high':'C', 'gpt-5.5-instant':'G', 'gemini-3.8-flash-high':'M'}
    for r in rows:
        attempt = 'original cutoff' if r['run_id'].endswith('naturalistic01') else 'N02 recovery' if 'recovery' in r['run_id'] else 'serial continuation'
        lines.append(f"| [{r['configuration_id']}](published_runs/nine_completed_20261003/trajectories/{r['configuration_id']}.json) | {labels[r['speaker_model']]} → {labels[r['judge_model']]} | {r['knower']} | {r['pick']} | {r['confidence']} | {r['asks']} | {attempt} |")
    lines += ['', 'ASK actions range from 1 to 6. BOTH counts once, and questions may contain several subquestions; this is not an equal-token or equal-subquestion cost metric. Reciprocal configurations share a dossier, so nine configurations are not nine independent background samples.', '',
        'Important cue limitation: in N03_D1 the uninformed speaker said "I can’t reliably give the report’s exact trench coordinates, layer numbers, object count, or associated finds from what I have available" and that supplying them "would be invention." This is a strong detail-availability cue, not a literal statement that it was denied source access. The judge overstated it as an explicit no-access admission. Other trajectories contain hedging or detail asymmetry. The observed 9/9 cannot establish successful detection of a consistently maintained bluff. The N05_D2 judge said its chosen speaker matched the original dossier, but it had no access to that dossier; that is a judge claim, not an independent truth check.', '',
        'Question-premise caution: N01_D2 asked for a cargo-declaration mismatch procedure absent from the dossier; the informed speaker flagged the gap while the bluff supplied a plausible procedure. The judge later criticized a mismatch-related detail it had itself prompted. N04_D2 similarly asked where a lamp was stored until the next year although storage was unspecified. Such probes can reveal source boundaries, but the judge’s premise and verdict rationale are not source truth. These observations are tied to the exact trajectory records, not independently coded causal mechanisms.', '',
        'Candidate observations include source-bounded uncertainty, requests for names/dates and concrete examples, and an instrument-category error in the N02 bluff. These are post-hoc case observations, not a stable behavioral taxonomy or preregistered mechanism. There is no passive baseline, human baseline, matched token budget, self-model condition or matched actor–observer test. Interrogation improvement, cross-family rankings and ToM dissociations remain untested.', '',
        f"Receipt/manifest/routing audit errors: **{len(errors)}**. Reproduce from repository root with `python -X utf8 -B scripts/analyze_naturalistic_snapshot.py` (Python standard library only). Read [protocol](PROTOCOL.md), [scope amendment](COLLECTION_SCOPE.md), then [published evidence](published_runs/nine_completed_20261003/README.md). Exact submitted prompts and visible final replies are preserved; visible Markdown-rendered capture is not asserted to equal the original generation byte stream. Only N01–N05 sources are published; unused fresh sources remain private. No new model calls were made for publication."]
    (ROOT / 'SNAPSHOT_RESULTS.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
    print(json.dumps({k:v for k,v in summary.items() if k != 'rows'}, ensure_ascii=False))
    if errors:
        raise SystemExit(2)

if __name__ == '__main__':
    main()
