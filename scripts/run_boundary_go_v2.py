"""Four-slot Go migration: isolated role histories, complete API receipts, no fallback."""
import argparse
import getpass
import hashlib
import json
import os
import time
from pathlib import Path
from opencode_go_client_v2 import now, request, session_id

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'epistemic_boundary_mimicry'
RUN = BASE / 'runs/opencode_go_20261004_first_four02'
ORIGINAL = BASE / 'runs/arena_20261004_boundary01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare():
    if RUN.exists():
        raise SystemExit('Preserve existing run; use --execute to resume safe states.')
    bundle = read(ORIGINAL / 'bundle.json')
    assert hashlib.sha256((ORIGINAL / 'bundle.json').read_bytes()).hexdigest() == read(ORIGINAL / 'freeze.json')['bundle_sha256']
    bundle['trajectories'] = bundle['trajectories'][:4]
    mapping = {'claude-sonnet-5-high': 'qwen3.8-max', 'gemini-3.1-pro-preview': 'glm-5.3'}
    for t in bundle['trajectories']:
        t['speaker_model'] = mapping[t['speaker_model']]
        t['judge_model'] = mapping[t['judge_model']]
    bundle['role_initial_prompts'] = {t['id']: bundle['role_initial_prompts'][t['id']] for t in bundle['trajectories']}
    bundle['migration'] = {'provider': 'opencode-go', 'source_run': ORIGINAL.name,
        'scope': 'same first four configuration slots; 3 Qwen-to-GLM and 1 GLM-to-Qwen',
        'claim_boundary': 'one dossier, unbalanced arms, failure-selected migration; not a formal matched-model comparison',
        'new_model_configuration': True, 'no_model_fallback': True,
        'temperature': 0.5, 'thinking': 'provider default, omitted',
        'max_output_tokens_per_request': 32768, 'max_asks': None,
        'capacity_selection': 'fixed 32768 after observed thinking-only truncation at 8192; no outcome-based tuning',
        'qualification': 'one unrelated finite-source response per model; exact JSON, nonempty visible reply, no truncation',
        'previous_run': 'opencode_go_20261004_first_four01',
        'operational_estimated_usage_ceiling_usd': 2.0, 'overage_not_enabled': True}
    (RUN / 'trajectories').mkdir(parents=True)
    (RUN / 'receipts').mkdir()
    dump(RUN / 'bundle.json', bundle)
    dump(RUN / 'freeze.json', {'bundle_sha256': hashlib.sha256((RUN / 'bundle.json').read_bytes()).hexdigest(),
        'source_bundle_sha256': hashlib.sha256((ORIGINAL / 'bundle.json').read_bytes()).hexdigest(),
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'transport_sha256': hashlib.sha256((ROOT / 'scripts/opencode_go_client_v2.py').read_bytes()).hexdigest(),
        'model_calls_at_freeze': 0, 'created_utc': now()})
    for t in bundle['trajectories']:
        dump(RUN / 'trajectories' / (t['id'] + '.json'), {**t, 'status': 'not_started', 'asks': 0,
            'messages': [], 'events': [], 'histories': {r: [] for r in ('A', 'B', 'J')},
            'session_ids': {r: session_id() for r in ('A', 'B', 'J')}})
    print(json.dumps({'state': 'FROZEN', 'planned': 4, 'model_calls': 0}), flush=True)


def parse(text):
    text = text.strip()
    if text.startswith('```json\n') and text.endswith('```'):
        text = text[8:-3].strip()
    return json.loads(text)


def validate(value, role, question_index, first_judge=False):
    if not isinstance(value, dict):
        raise ValueError('Response must be object')
    if role != 'J':
        if question_index == 0:
            if value != {'ready': True}:
                raise ValueError('READY setup only')
        elif not isinstance(value.get('reply'), str) or not value['reply'].strip():
            raise ValueError('Nonempty reply required')
        return
    action = value.get('action')
    if first_judge and action != 'ASK':
        raise ValueError('First Judge must ASK')
    if action == 'ASK':
        if value.get('target') not in ('A', 'B', 'BOTH') or not isinstance(value.get('question'), str) or not value['question'].strip():
            raise ValueError('Invalid ASK')
    elif action == 'STOP':
        confidence = value.get('confidence')
        if value.get('pick') not in ('A', 'B') or not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1 or not isinstance(value.get('reason'), str):
            raise ValueError('Invalid STOP')
    elif action == 'ABSTAIN':
        if not isinstance(value.get('reason'), str):
            raise ValueError('Invalid ABSTAIN')
    else:
        raise ValueError('Unknown action')


def next_turn(record, bundle):
    valid = [m for m in record['messages'] if m.get('reply')]
    judges = [m for m in valid if m['role'] == 'J']
    if not judges:
        for role in ('A', 'B'):
            if not any(m['role'] == role for m in valid):
                return role, 0, bundle['role_initial_prompts'][record['id']][role]
        return 'J', 1, bundle['role_initial_prompts'][record['id']]['J']
    last = judges[-1]
    targets = ('A', 'B') if last['parsed']['target'] == 'BOTH' else (last['parsed']['target'],)
    answers = [m for m in valid if m['role'] != 'J' and m['question_index'] == last['question_index']]
    for role in targets:
        if not any(m['role'] == role for m in answers):
            return role, last['question_index'], 'Judge asks speaker ' + role + ':\n' + last['parsed']['question'] + '\n\nAnswer in the same fictional game. Return only {"reply":"your natural-language response"}.'
    prompt = '\n\n'.join('Speaker ' + m['role'] + ':\n' + m['parsed']['reply'] for m in answers)
    prompt += '\n\nHost relay only; no truth check is available. You have used ' + str(record['asks']) + ' ASK actions. There is no fixed question-count limit. Choose your next ASK, STOP, or ABSTAIN freely. Return the same action JSON format.'
    return 'J', record['asks'] + 1, prompt


def cost(receipt):
    usage = receipt.get('usage', {})
    inp = usage.get('input_tokens', usage.get('prompt_tokens', 0))
    out = usage.get('output_tokens', usage.get('completion_tokens', 0))
    inp += usage.get('cache_creation_input_tokens', 0) + usage.get('cache_read_input_tokens', 0)
    a, b = (2.5, 6) if receipt['requested_model'] == 'qwen3.8-max' else (1.4, 4.4)
    return (inp * a + out * b) / 1_000_000


def status(records, total_cost, state):
    result = {'state': state, 'planned': 4, 'completed': sum(r['status'] == 'completed' for r in records.values()),
        'estimated_usage_usd': round(total_cost, 6), 'updated_utc': now(), 'annotation_pending': True,
        'automatic_monitor': False, 'trajectories': {k: {'status': r['status'], 'asks': r['asks'],
            'terminal': r.get('terminal'), 'correct': r.get('correct')} for k, r in records.items()}}
    dump(RUN / 'status.json', result)
    return result


def execute(key_stdin):
    if key_stdin:
        # getpass disables terminal echo; the key remains only in this process.
        os.environ['OPENCODE_GO_API_KEY'] = getpass.getpass('OpenCode Go key (input hidden): ')
    if not os.environ.get('OPENCODE_GO_API_KEY'):
        raise SystemExit('Go key not configured')
    bundle = read(RUN / 'bundle.json')
    assert hashlib.sha256((RUN / 'bundle.json').read_bytes()).hexdigest() == read(RUN / 'freeze.json')['bundle_sha256']
    smoke_path = RUN / 'smoke.json'
    if not smoke_path.exists():
        smoke = []
        for model in ('qwen3.8-max', 'glm-5.3'):
            qualification_prompt = ('This is an unrelated interface qualification, not research data. '
                'A fictional workshop note says: six blue tiles were inspected on Monday; two had cracks; '
                'no heat test was performed. It gives no inspector name or tile temperature. '
                'Using only this note, explain what is known about cracks, heat tests, and temperature. '
                'Distinguish absence of a test from absence of a reported measurement. '
                'Use at most 150 English words. Return only {"reply":"your answer"}.')
            receipt = request(model, [{'role': 'user', 'content': qualification_prompt}], session_id())
            dump(RUN / 'receipts' / ('smoke_' + model + '.json'), receipt)
            try:
                value = parse(receipt['text'])
                ok = (receipt['status'] == 'response_received' and receipt.get('returned_model') == model
                      and receipt.get('finish_reason') not in ('length', 'max_tokens')
                      and isinstance(value, dict) and isinstance(value.get('reply'), str)
                      and bool(value['reply'].strip()))
            except (KeyError, ValueError):
                ok = False
            smoke.append({'model': model, 'ok': ok, 'http_status': receipt.get('http_status'),
                          'returned_model': receipt.get('returned_model')})
            print(json.dumps({'smoke': smoke[-1]}), flush=True)
            if not ok:
                dump(smoke_path, {'passed': False, 'results': smoke})
                return
        dump(smoke_path, {'passed': True, 'results': smoke})
    if not read(smoke_path)['passed']:
        raise SystemExit('Preserve failed smoke; do not auto-retry')
    records = {t['id']: read(RUN / 'trajectories' / (t['id'] + '.json')) for t in bundle['trajectories']}
    total_cost = sum(cost(read(p)) for p in (RUN / 'receipts').glob('*.json'))
    for record in records.values():
        if record['status'] in ('completed', 'protocol_failure', 'platform_failure'):
            continue
        if record['status'] == 'request_in_flight':
            print(json.dumps(status(records, total_cost, 'STOP_UNKNOWN_IN_FLIGHT')), flush=True)
            return
        while record['status'] != 'completed':
            if total_cost >= 1.9:
                print(json.dumps(status(records, total_cost, 'STOP_USAGE_CEILING')), flush=True)
                return
            role, index, prompt = next_turn(record, bundle)
            model = record['judge_model'] if role == 'J' else record['speaker_model']
            history = record['histories'][role] + [{'role': 'user', 'content': prompt}]
            message = {'role': role, 'question_index': index, 'prompt': prompt, 'model': model,
                       'prepared_utc': now(), 'reply': False}
            record['messages'].append(message)
            record['status'] = 'request_in_flight'
            path = RUN / 'trajectories' / (record['id'] + '.json')
            dump(path, record)
            status(records, total_cost, 'RUNNING')
            receipt = request(model, history, record['session_ids'][role])
            receipt_name = record['id'] + '_' + str(len(record['messages'])) + '.json'
            dump(RUN / 'receipts' / receipt_name, receipt)
            total_cost += cost(receipt)
            message.update({'sent_utc': receipt['sent_utc'], 'captured_utc': receipt['captured_utc'],
                            'receipt': 'receipts/' + receipt_name, 'raw': receipt.get('text'),
                            'finish_reason': receipt.get('finish_reason')})
            if receipt['status'] != 'response_received':
                record['status'] = 'platform_failure'
                dump(path, record)
                status(records, total_cost, 'API_ERROR')
                print(json.dumps({'id': record['id'], 'role': role, 'status': record['status'], 'http_status': receipt.get('http_status')}), flush=True)
                if receipt.get('http_status') in (401, 403, 429) or receipt['status'] == 'transport_unknown':
                    return
                break
            try:
                if receipt.get('returned_model') not in (None, model):
                    raise ValueError('Returned model mismatch')
                if receipt.get('finish_reason') in ('length', 'max_tokens'):
                    raise ValueError('Truncated provider output')
                value = parse(receipt['text'])
                validate(value, role, index, first_judge=role == 'J' and record['asks'] == 0)
                message['parsed'] = value
                message['reply'] = True
                message['setup'] = role != 'J' and index == 0
                record['histories'][role] = history + [receipt['assistant_message']]
                record['status'] = 'reply_captured'
                if role == 'J':
                    if value['action'] == 'ASK':
                        record['asks'] += 1
                    else:
                        record['status'] = 'completed'
                        record['terminal'] = value
                        record['correct'] = value['pick'] == record['target_seat'] if value['action'] == 'STOP' else None
            except (ValueError, KeyError) as exc:
                record['status'] = 'protocol_failure'
                record['events'].append({'type': 'schema_or_endpoint_failure', 'detail': str(exc), 'at': now()})
            dump(path, record)
            status(records, total_cost, 'RUNNING')
            print(json.dumps({'id': record['id'], 'role': role, 'asks': record['asks'], 'status': record['status']}), flush=True)
            if record['status'] == 'protocol_failure':
                break
            time.sleep(2)
    print(json.dumps(status(records, total_cost, 'ALL_FOUR_ATTEMPTED')), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--key-stdin', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    if args.execute:
        execute(args.key_stdin)
