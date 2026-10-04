"""Publish only the two completed Go endpoints through an explicit field allowlist."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'epistemic_boundary_mimicry/runs/opencode_go_20261004_first_four02'
OUT = ROOT / 'epistemic_boundary_mimicry/published_runs/go_two_completed_20261004'
IDS = ('EB01_D1_strong', 'EB01_D1_boundary_aware')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    if OUT.exists() and list(OUT.glob('*.json')):
        raise SystemExit('Preserve existing public snapshot')
    bundle = read(RUN / 'bundle.json')
    OUT.mkdir(parents=True, exist_ok=True)
    source_id = bundle['trajectories'][0]['target_source_id']
    case = next(c for c in bundle['cases'] if c['case_id'] == 'EB01')
    source = next(s for s in case['sources'] if s['source_id'] == source_id)
    write(OUT / 'bundle.json', {
        'study': 'Epistemic Boundary Mimicry / Go qualification pilot',
        'source': {k: source[k] for k in ('source_id', 'source_title', 'source_text', 'source_sha256')},
        'public_context': case['public_context'],
        'role_initial_prompts': {i: bundle['role_initial_prompts'][i] for i in IDS},
        'configuration': {'provider': 'opencode-go', 'speaker_model': 'qwen3.8-max',
            'judge_model': 'glm-5.3', 'max_tokens': 32768, 'temperature': 0.5,
            'stream': False, 'reasoning': 'deployment default, omitted', 'max_asks': None,
            'host_truth': False, 'tools': False, 'opening': False},
        'scope': {'planned': 4, 'completed': 2, 'independent_dossiers': 1,
            'excluded': [{'id': 'EB01_D1_symmetric_frozen', 'status': 'protocol_failure', 'asks': 2,
                          'cause': 'unescaped control characters in visible JSON reply'},
                         {'id': 'EB01_D2_boundary_aware', 'status': 'protocol_failure', 'asks': 0,
                          'cause': 'empty visible setup output; do not promote reasoning to answer'}]},
        'claim_boundary': 'Descriptive two-endpoint pilot; not a causal condition effect, model ranking, or interrogation benefit.'})
    for ident in IDS:
        r = read(RUN / 'trajectories' / (ident + '.json'))
        assert r['status'] == 'completed'
        projected = {k: r[k] for k in ('id', 'case_id', 'condition', 'speaker_model',
                    'judge_model', 'target_seat', 'target_source_id', 'knower', 'status',
                    'asks', 'terminal', 'correct')}
        projected['messages'] = []
        for m in r['messages']:
            assert m['reply']
            receipt = read(RUN / m['receipt'])
            assert receipt['text'] == m['raw']
            projected['messages'].append({
                **{k: m[k] for k in ('role', 'question_index', 'prompt', 'model', 'raw', 'parsed', 'setup')},
                'returned_model': receipt['returned_model'],
                'finish_reason': receipt['finish_reason'], 'usage': receipt['usage']})
        write(OUT / (ident + '.json'), projected)
    files = sorted(OUT.glob('*.json'))
    write(OUT / 'manifest.json', {'files': [{'file': p.name,
        'sha256_lf_utf8': hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()}
        for p in files], 'projection': 'Exact prompts and visible replies; excludes hidden reasoning, API/auth/session/account/machine fields.'})
    print(json.dumps({'published_endpoints': len(IDS), 'files': len(files) + 1}))


if __name__ == '__main__':
    main()
