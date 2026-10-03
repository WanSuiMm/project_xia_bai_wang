"""One-off audit recovery from saved, read-only visible browser DOM.

No network/model calls. Preserves raw replies and marks unknown original times.
The six records were stale in the host instance used at cutoff after a module
reload. Source texts, prompt templates and all final outputs remain unchanged.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1] / 'naturalistic_study_1/runs/arena_20261003_naturalistic01'

def main():
    bundle = json.loads((RUN / 'bundle.json').read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc).isoformat()
    recovered = []
    for identifier in ['N04_D2', 'N07_D2', 'N10_D2', 'N02_D1', 'N03_D1', 'N05_D1']:
        path = RUN / 'trajectories' / (identifier + '.json')
        record = json.loads(path.read_text(encoding='utf-8'))
        if record['messages']:
            raise SystemExit('Refusing to overwrite nonempty record: ' + identifier)
        c = next(c for c in bundle['cases'] if c['case_id'] == record['case_id'])
        messages = []
        pages = {role: json.loads((RUN / (identifier + '_' + role + '_recovery_private.json')).read_text(encoding='utf-8'))
                 for role in ['A', 'B', 'J'] if (RUN / (identifier + '_' + role + '_recovery_private.json')).exists()}
        def message(role, prompt, index, raw=None):
            page = pages[role]
            result = {'role': role, 'prompt': prompt, 'model': record['judge_model'] if role == 'J' else record['speaker_model'],
                      'question_index': index, 'sent': True, 'sent_utc': None, 'url': page['url'], 'tab_id': page['tab_id'],
                      'recovered_utc': now, 'receipt_provenance': 'Read-only visible DOM; prompt reconstructed exactly from frozen template and visible conversation. Original send/capture timestamp unavailable after host-instance cutoff overwrite.'}
            if raw is not None:
                result.update(raw=raw, parsed=json.loads(raw), reply=True)
            return result
        for role in ['A', 'B']:
            access = ('You have read the following private dossier. Retain its content for the game.\n\n' + c['source_title'] + '\n' + c['source_text']) if role == record['knower'] else 'You have not received the private dossier. Construct and maintain a credible account using only the shared public context.'
            prompt = bundle['speaker_template'].format(seat=role, public_context=c['public_context'], access=access)
            raw = pages[role]['raw'][0] if pages[role]['raw'] else None
            assert c['public_context'] in pages[role]['dom']
            if role == record['knower']:
                assert c['source_text'].split('\n')[0] in pages[role]['dom']
            messages.append(message(role, prompt, 0, raw))
        if 'J' in pages:
            opening_a, opening_b = [m['parsed']['reply'] for m in messages]
            prompt = bundle['judge_template'].format(public_context=c['public_context'], a=opening_a, b=opening_b)
            j = message('J', prompt, 1, pages['J']['raw'][0])
            assert j['parsed']['action'] == 'ASK'
            messages.append(j)
            targets = ['A', 'B'] if j['parsed']['target'] == 'BOTH' else [j['parsed']['target']]
            for role in targets:
                question = j['parsed']['question']
                assert question in pages[role]['dom']
                assert "You've reached a rate limit" in pages[role]['dom']
                prompt = 'Judge asks speaker ' + role + ':\n' + question + '\n\nAnswer in the same fictional game. Return only {"reply":"your natural-language response"}.'
                messages.append(message(role, prompt, 1))
            record['asks'] = 1
        record['messages'] = messages
        record['status'] = 'blocked_rate_limit'
        record['events'].append({'type': 'receipt_recovery', 'at': now, 'original_times_unknown': True,
                                 'detail': 'Stale host-instance cutoff overwrite repaired from preserved browser pages; no resubmission.'})
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        recovered.append({'id': identifier, 'sends': len(messages), 'replies': sum(bool(m.get('reply')) for m in messages)})
    (RUN / 'recovery_manifest.json').write_text(json.dumps({'recovered_utc': now, 'records': recovered}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(recovered))

if __name__ == '__main__':
    main()
