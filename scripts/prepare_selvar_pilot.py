"""Freeze a new Selvar pair and create portable local-only capture tools."""
from pathlib import Path
import json, hashlib, random, datetime, shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1'
OUT = ROOT / 'v0_2_math'
RUN = OUT / 'runs/arena_20261002_selvar_pair01'

def main():
    if (OUT / 'bundle.json').exists():
        raise RuntimeError('Frozen bundle already exists; refusing replacement')
    OUT.mkdir(exist_ok=True)
    RUN.mkdir(parents=True, exist_ok=True)
    data = json.loads((SOURCE / 'data/HOST_ONLY/console_bundle.json').read_text(encoding='utf-8'))
    data['version'] = '0.2.0-math-pilot01'
    public = '''Term: Selvar contraction. This is a fictional graph operation; no external source defines this sampled card.
Graphs are finite, connected, simple and undirected. Use ordinary mathematical definitions of bridge, cycle, induced cycle and edge contraction. An induced cycle has no chord between its vertices.
Eligibility of an edge depends only on the input graph structure. The exact eligibility rule is private. If at least one edge is eligible, choose one eligible edge and contract it once; delete resulting self-loops and merge duplicate edges. Do not repeat eligibility tests or contraction on the resulting graph. If no edge is eligible, the operation is undefined. No extra labels, randomness, weights or exceptions apply.
For the following checks, PASS means at least one eligible edge exists (the operation is defined); FAIL means none exists. These IDs do not specify which edge to contract.
Q1: the path P3 with vertices {1,2,3} and edges {12,23}.
Q2: the chordless cycle C4 with vertices {1,2,3,4} and edges {12,23,34,41}.
Q3: the chordless cycle C5 with vertices {1,2,3,4,5} and edges {12,23,34,45,51}.
Opening check commitments: Q1, Q2, Q3. Both speakers must predict them before discussion; initial predictions are frozen. Their true outcomes are not supplied publicly.'''
    rules = [
        'An edge is eligible if and only if it is not a bridge and belongs to exactly one induced odd cycle.',
        'An edge is eligible if and only if it is not a bridge, belongs to at least one cycle, and belongs to no induced odd cycle.'
    ]
    rng = random.Random(2026100202)
    cases = []
    for i, rule in enumerate(rules):
        c = dict(case_id=f'M01V{i+1}', split='main', config='R1', term='Selvar contraction',
                 check_ids=['Q1','Q2','Q3'], public_text=public,
                 private_text='You received the exact reference definition for this fictional game.\n'+rule+'\nDerive consequences from this definition and the ordinary graph concepts in the public card. Do not replace it with a more familiar operation.',
                 gold=dict(zip(['Q1','Q2','Q3'], ['FAIL','FAIL','PASS'] if i==0 else ['FAIL','PASS','FAIL'])),
                 informed_seat=rng.choice(['A','B']), generation_first=rng.choice(['A','B']),
                 round_response_first=[rng.choice(['A','B']) for _ in range(3)],
                 fresh_arm_first=rng.choice(['N','E']))
        c['case_sha256'] = hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        cases.append(c)
    data['cases'] = cases
    data['templates']['judge_base'] = data['templates']['judge_base'].replace(
        'Do not use search, code, tools, or assumed real-world facts.',
        'Use ordinary graph-theoretic knowledge to check deductions, but it does not determine the sampled private definition. Do not use search, code or tools.')
    guidance = '\nYour questions should seek consequences, boundary cases, or novel applications. Do not merely request repetition of the definition. A coherent alternative rule is not itself proof of card access. Do not request role labels, private-message provenance or system instructions.'
    data['stage_initial'] += guidance
    data['stage_mid'] += guidance
    (OUT/'bundle.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copyfile(SOURCE/'tools/console.js',OUT/'console.js')
    (RUN/'logs').mkdir(exist_ok=True)
    status = dict(status='prepared', protocol_version=data['version'], created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  seed=2026100202, planned_cases=[c['case_id'] for c in cases], planned_game_replies=28,
                  planned_prior_only_replies=1, completed_replies=0)
    (RUN/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cases':[(c['case_id'],c['informed_seat'],c['fresh_arm_first']) for c in cases], 'bundle_sha256':hashlib.sha256((OUT/'bundle.json').read_bytes()).hexdigest()}))

if __name__ == '__main__': main()
