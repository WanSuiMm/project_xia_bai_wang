"""Bounded credential check and identical-design R0 infrastructure recovery.

Never pass a credential on the command line or write it to a file. The newly
supplied credential is read with echo disabled and remains process-local.
"""
from __future__ import annotations

import getpass
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
import warnings
from uuid import uuid4

import run_frozen_replay_r0 as runner


OLD_RUN = runner.DEFAULT_RUN
NEW_RUN = runner.BASE / 'runs/opencode_go_20261007_frozen_replay_r0_84_02'
AMENDMENT = runner.BASE / 'replay_r0/RECOVERY_AMENDMENT_20261007.md'
PROBE_PROMPT = (
    'Interface availability check, independent of all study materials. '
    'Return only this JSON: '
    '{"p_A":0.5,"decision":"ABSTAIN","reason":"Interface available."}'
)


def error_classification(raw: bytes) -> str:
    # Classify in memory; never copy an error body or private account URL.
    text = raw.decode('utf-8', errors='replace').lower()
    if 'subscription ended' in text or 'payment method needs authorization' in text:
        return 'subscription_ended_payment_authorization_required'
    if 'quota' in text or 'rate limit' in text or 'usage limit' in text:
        return 'quota_or_rate_limit'
    if 'invalid api key' in text or 'invalid key' in text or 'unauthorized' in text:
        return 'authentication_error'
    return 'provider_http_error'


def probe(label: str, model: str, key: str) -> dict:
    fmt = runner.ENDPOINTS[model]
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'XiaBaiWangResearch/1.0',
        'x-opencode-session': 'xia-r0-probe-' + str(uuid4()),
    }
    if fmt == 'messages':
        headers.update({'x-api-key': key, 'anthropic-version': '2023-06-01'})
    else:
        headers['Authorization'] = 'Bearer ' + key
    body = {
        'model': model, 'messages': [{'role': 'user', 'content': PROBE_PROMPT}],
        'max_tokens': runner.MAX_TOKENS, 'temperature': 0.5, 'stream': False,
    }
    out = {
        'credential_label': label, 'model': model, 'started_utc': runner.now(),
        'http_status': None, 'returned_model_matches': False,
        'parse_status': 'not_received', 'valid': False, 'usage': {},
    }
    start = time.monotonic()
    try:
        req = urllib.request.Request(
            'https://opencode.ai/zen/go/v1/' + fmt,
            data=json.dumps(body).encode('utf-8'), headers=headers,
        )
        with urllib.request.build_opener(runner.NoRedirect()).open(req, timeout=600) as response:
            out['http_status'] = response.status
            data = json.loads(response.read().decode('utf-8'))
        out['returned_model_matches'] = data.get('model') == model
        out['usage'] = data.get('usage', {})
        if fmt == 'messages':
            text = ''.join(b.get('text', '') for b in data.get('content', []) if b.get('type') == 'text')
            finish = data.get('stop_reason')
        else:
            choice = data['choices'][0]
            text = choice['message'].get('content') or ''
            finish = choice.get('finish_reason')
        _, out['parse_status'] = runner.parse(text, finish)
        out['valid'] = (
            out['parse_status'] == 'valid' and out['returned_model_matches']
            and finish in ('stop', 'end_turn')
        )
        out['classification'] = 'generation_available' if out['valid'] else 'invalid_check_response'
    except urllib.error.HTTPError as exc:
        out['http_status'] = exc.code
        out['classification'] = error_classification(exc.read())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        out['classification'] = 'transport_unknown'
        out['error_type'] = type(exc).__name__
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        out['classification'] = 'invalid_provider_response'
        out['error_type'] = type(exc).__name__
    out['elapsed_seconds'] = round(time.monotonic() - start, 3)
    out['completed_utc'] = runner.now()
    # No error bodies, visible answer text, session IDs or key identifiers saved.
    if key in json.dumps(out):
        raise RuntimeError('Credential echo detected; refuse persistence')
    return out


def prepare_identical() -> None:
    previous = runner.read(OLD_RUN / 'status.json')
    if previous['valid'] != 0 or previous['state'] != 'HALTED':
        raise RuntimeError('This amendment only covers the zero-answer infrastructure cutoff')
    runner.audit(OLD_RUN)
    runner.prepare(NEW_RUN)
    old_manifest = runner.read(OLD_RUN / 'manifest.json')
    new_manifest = runner.read(NEW_RUN / 'manifest.json')
    for manifest in (old_manifest, new_manifest):
        manifest.pop('created_utc')
    if old_manifest != new_manifest:
        raise RuntimeError('Recovery scientific configuration or schedule changed')
    runner.dump(NEW_RUN / 'recovery.json', {
        'created_utc': runner.now(), 'original_run': OLD_RUN.name,
        'original_dispatched': previous['provider_requests'],
        'original_valid_answers': previous['valid'],
        'identical_manifest_except_creation_time': True,
        'amendment_sha256': runner.sha_file(AMENDMENT),
        'recovery_helper_sha256': runner.sha_file(Path(__file__)),
        'reason': 'User authorized credential availability check and unchanged full replay.',
    })


def main() -> int:
    if NEW_RUN.exists():
        raise SystemExit('Recovery run exists; inspect it rather than duplicate dispatch')
    existing = os.environ.get('OPENCODE_GO_API_KEY')
    if not existing:
        raise SystemExit('Existing credential unavailable; no model request sent')
    # getpass refuses its insecure echoed fallback before reading any input.
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        supplied = getpass.getpass('Supplied credential (input hidden): ').strip()
    if not supplied:
        raise SystemExit('No supplied credential; no model request sent')
    prepare_identical()
    credentials = [('existing', existing)]
    if supplied != existing:
        credentials.append(('supplied', supplied))
    checks: list[dict] = []
    def record(label: str, model: str, key: str) -> dict:
        result = probe(label, model, key)
        checks.append(result)
        runner.dump(NEW_RUN / 'credential_checks.json', {
            'scope': 'Interface checks only; not replay observations',
            'checks': checks, 'selected_credential': None,
        })
        print(json.dumps({k: result[k] for k in (
            'credential_label', 'model', 'http_status', 'valid', 'classification'
        )}), flush=True)
        return result
    qualified = [
        (label, key) for label, key in credentials
        if record(label, 'glm-5.3', key)['valid']
    ]
    selected = None
    for label, key in qualified:
        if record(label, 'qwen3.8-max', key)['valid']:
            selected = (label, key)
            break
    if selected is None:
        runner.dump(NEW_RUN / 'status.json', {
            'state': 'BLOCKED_CREDENTIAL_CHECK', 'planned': 84,
            'provider_requests': 0, 'response_count': 0, 'valid': 0,
            'halt_reason': 'No supplied credential verified on both fixed model endpoints.',
            'interface_generation_checks': len(checks), 'updated_utc': runner.now(),
        })
        print('No credential verified on both endpoints; no replay requests dispatched.', flush=True)
        return 3
    label, key = selected
    runner.dump(NEW_RUN / 'credential_checks.json', {
        'scope': 'Interface checks only; not replay observations',
        'checks': checks, 'selected_credential': label,
    })
    os.environ['OPENCODE_GO_API_KEY'] = key
    print(json.dumps({'selected_credential': label, 'dispatching_frozen_requests': 84}), flush=True)
    runner.execute(NEW_RUN)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
