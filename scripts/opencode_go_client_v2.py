"""Direct OpenCode Go transport. No agent tools, hidden prompts or model fallback."""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4

BASE = 'https://opencode.ai/zen/go/v1'
MODELS = {'qwen3.8-max': 'messages', 'glm-5.3': 'chat/completions'}
USER_AGENT = 'XiaBaiWangResearch/1.0'


def now():
    return datetime.now(timezone.utc).isoformat()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request(model, history, session_id, max_tokens=32768):
    if model not in MODELS:
        raise ValueError('Unapproved model')
    key = os.environ.get('OPENCODE_GO_API_KEY')
    if not key:
        raise RuntimeError('OPENCODE_GO_API_KEY is not configured')
    payload = {'model': model, 'messages': history, 'max_tokens': max_tokens, 'stream': False, 'temperature': 0.5}
    headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
               'User-Agent': USER_AGENT, 'x-opencode-session': session_id}
    if MODELS[model] == 'messages':
        headers.pop('Authorization')
        headers['x-api-key'] = key
        headers['anthropic-version'] = '2023-06-01'
    receipt = {'requested_model': model, 'endpoint_format': MODELS[model], 'sent_utc': now(),
               'max_tokens': max_tokens, 'temperature': 0.5, 'session_id': session_id, 'retry_policy': 'none_in_transport'}
    receipt['auth_header_name'] = 'x-api-key' if MODELS[model] == 'messages' else 'Authorization'
    req = urllib.request.Request(BASE + '/' + MODELS[model],
                                 data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers)
    start = time.monotonic()
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=600) as response:
            raw = response.read().decode('utf-8')
            receipt['http_status'] = response.status
        data = json.loads(raw)
        receipt['response'] = data
        receipt['returned_model'] = data.get('model')
        receipt['usage'] = data.get('usage', {})
        if MODELS[model] == 'messages':
            content = data.get('content', [])
            receipt['text'] = ''.join(c.get('text', '') for c in content if c.get('type') == 'text')
            receipt['assistant_message'] = {'role': 'assistant', 'content': content}
            receipt['finish_reason'] = data.get('stop_reason')
        else:
            choice = data['choices'][0]
            assistant = choice['message']
            receipt['text'] = assistant.get('content') or ''
            receipt['assistant_message'] = {k: v for k, v in assistant.items()
                                             if k in ('role', 'content', 'reasoning_content')}
            receipt['finish_reason'] = choice.get('finish_reason')
        receipt['status'] = 'response_received'
    except urllib.error.HTTPError as exc:
        receipt['http_status'] = exc.code
        # Error bodies can contain account details. Retain only status/code, never headers or keys.
        receipt['status'] = 'http_error'
        try:
            data = json.loads(exc.read().decode('utf-8'))
            error = data.get('error', {})
            if isinstance(error, dict):
                receipt['error_code'] = str(error.get('code') or error.get('type') or '')[:120].replace(key, '[REDACTED]')
        except (ValueError, UnicodeError):
            pass
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        receipt['status'] = 'transport_unknown'
        receipt['error_type'] = type(exc).__name__
    except (ValueError, KeyError, IndexError) as exc:
        receipt['status'] = 'invalid_provider_response'
        receipt['error_type'] = type(exc).__name__
    receipt['captured_utc'] = now()
    receipt['elapsed_seconds'] = round(time.monotonic() - start, 3)
    return receipt


def session_id():
    return 'xia-bai-wang-' + str(uuid4())
