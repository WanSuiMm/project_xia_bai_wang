"""One fresh archival-conservation symmetric-source control, offline freeze then bounded API run."""
import argparse
import hashlib
import json
import random
from pathlib import Path
import run_boundary_go_case2 as case2
from opencode_go_client_v2 import now, session_id
from prepare_boundary_mimicry import SPEAKER, READER, JUDGE

base = case2.base
RUN = base.BASE / 'runs/opencode_go_20261004_archaeology_frozen01'
IDENT = 'EB04_D1_symmetric_frozen'
SEED = 2026100422
PUBLIC = ('A fictional archaeological archive records conservation work on painted clay '
          'inventory tags recovered from a storeroom. A finite treatment note describes '
          'observations, a small follow-up and limits on interpretation. The site, staff '
          'and records are invented. Discuss this particular note rather than general '
          'archaeological practice.')
ORIGINAL_STATUS = base.status


def source(rng, index):
    site = rng.choice(['Veylan Court', 'Neral Quay', 'Orven Hall', 'Tessel Yard'])
    author = rng.choice(['Lena Corven', 'Iris Daven', 'Maro Sel', 'Tessa Nor'])
    year = rng.choice([2016, 2018, 2020, 2022])
    month = rng.choice(['March', 'June', 'October'])
    total = rng.choice([18, 24, 30])
    improved = total - rng.choice([4, 6, 8])
    follow = rng.choice([3, 4, 5])
    minutes = rng.choice([10, 15, 20])
    blocks = [
        f'{author} wrote a conservation note at the archive of {site} in {month} '
        f'{year}. It concerns {total} painted clay inventory tags recovered together '
        'from a collapsed storeroom shelf. Their painted marks were partly obscured '
        'by a pale surface deposit. The note records a treatment trial, not an '
        'interpretation of the marks or a reconstruction of the storeroom economy.',
        f'Staff photographed every tag before placing it in a closed humidity chamber '
        f'for {minutes} minutes. They then lifted loosened deposit with a dry soft '
        'brush and photographed it again under the same lamp position. No liquid '
        'solvent was applied. Tags were handled separately, and fragments were not '
        'joined during this trial. A blank visibility entry means the conservator '
        'could not assess the painted line; it does not mean the line was absent.',
        f'After treatment, painted lines on {improved} tags were rated clearer than '
        f'before; {total-improved} showed no rated improvement. Two of the improved '
        'tags also lost small flakes from already cracked margins. The sheet records '
        'these as handling losses, without assigning a chemical cause. Clarity was '
        'judged by comparison with the photographs, not by an automated image score. '
        'No lettering was transcribed or translated.',
        f'One week later, staff checked {follow} improved tags selected because their '
        f'painted areas remained intact. All {follow} retained the recorded visibility '
        'rating, and no new loose flakes were noted. The other tags were not included '
        'in this follow-up. These observations concern the selected subset and cannot '
        'establish a long-term preservation rate for the collection.',
        'The author regards deposit loosening as a practical observation rather than '
        'proof of a particular mineral reaction. No chemical analysis of the deposit '
        'or pigment was performed. There was no untreated comparison group, and the '
        'trial did not compare alternative chamber durations. The note does not date '
        'the tags, identify their makers, or connect individual marks to named '
        'merchants. It concludes that visibility sometimes improved under this '
        'procedure, with handling damage still possible; it does not recommend '
        'applying the treatment to every painted object in the archive.']
    if rng.randrange(2):
        blocks = [blocks[0], blocks[1], blocks[3], blocks[2], blocks[4]]
    text = '\n\n'.join(blocks)
    return {'source_id': 'EB04_source_' + str(index),
            'source_title': 'Painted inventory-tag conservation note',
            'source_text': text, 'source_sha256': hashlib.sha256(text.encode()).hexdigest()}


def status(records, total_cost, state):
    value = ORIGINAL_STATUS(records, total_cost,
        'FRESH_FROZEN_ATTEMPT_FINISHED' if state == 'ALL_FOUR_ATTEMPTED' else state)
    value['planned'] = 1
    base.dump(RUN / 'status.json', value)
    return value


def prepare():
    if RUN.exists():
        raise SystemExit('Preserve fresh run')
    sources = [source(random.Random(SEED + 101 + i), i) for i in range(2)]
    assert sources[0]['source_text'] != sources[1]['source_text']
    assert all(300 <= len(s['source_text'].split()) <= 450 for s in sources)
    (RUN / 'trajectories').mkdir(parents=True)
    (RUN / 'receipts').mkdir()
    base.dump(RUN / 'sources_frozen.json', {'sources': sources, 'created_utc': now(),
        'generation_seeds': [SEED+101, SEED+102]})
    seat_rng = random.Random(SEED + 1000)
    seat_sources = sources[:]
    seat_rng.shuffle(seat_sources)
    base.dump(RUN / 'seats_frozen.json', {'seat_source_ids': dict(zip(('A', 'B'), [s['source_id'] for s in seat_sources])),
        'seat_seed': SEED + 1000, 'created_utc': now()})
    # Independent target draw occurs only after both source and seat files exist.
    target_index = random.Random(SEED + 2000).randrange(2)
    target = ('A', 'B')[target_index]
    prompts = {seat: SPEAKER.format(seat=seat, public_context=PUBLIC,
        access=READER.format(source_text=s['source_text'])) for seat, s in zip(('A', 'B'), seat_sources)}
    prompts['J'] = JUDGE.format(public_context=PUBLIC)
    t = {'id': IDENT, 'case_id': 'EB04', 'condition': 'symmetric_frozen',
        'speaker_model': 'qwen3.8-max', 'judge_model': 'glm-5.3', 'target_seat': target,
        'target_source_id': seat_sources[target_index]['source_id'],
        'other_source_id': seat_sources[1-target_index]['source_id'], 'knower': target}
    bundle = {'study': 'fresh symmetric-source pilot', 'trajectories': [t],
        'cases': [{'case_id': 'EB04', 'public_context': PUBLIC, 'sources': sources}],
        'role_initial_prompts': {IDENT: prompts}, 'target_draw_seed': SEED + 2000,
        'target_draw_after_source_and_seat_freeze': True,
        'configuration': {'max_tokens': 32768, 'temperature': .5, 'reasoning': 'deployment default',
            'stream': False, 'tools': False, 'max_asks': None, 'opening': False,
            'Judge_first': True, 'no_READY': True, 'parser': 'strict=False',
            'operational_new_usage_stop_before_next_request_usd': 1.9},
        'claim_boundary': 'one new pilot; Judge not told random-label generation mechanism; target match is not authenticity inference'}
    base.dump(RUN / 'bundle.json', bundle)
    record = {**t, 'status': 'not_started', 'asks': 0, 'messages': [], 'events': [],
        'histories': {x: [] for x in ('A', 'B', 'J')},
        'session_ids': {x: session_id() for x in ('A', 'B', 'J')}}
    base.dump(RUN / 'trajectories' / (IDENT + '.json'), record)
    assert base.read(base.RUN / 'smoke.json')['passed']
    base.dump(RUN / 'smoke.json', {'passed': True, 'inherited_qualification': base.RUN.name,
        'reason': 'same already-qualified transport/models/sampling; no redundant provider calls'})
    paths = {'bundle_sha256': RUN/'bundle.json', 'sources_sha256': RUN/'sources_frozen.json',
        'seats_sha256': RUN/'seats_frozen.json', 'runner_sha256': Path(__file__),
        'case2_runner_sha256': Path(case2.__file__), 'base_runner_sha256': Path(base.__file__),
        'templates_sha256': Path(__file__).with_name('prepare_boundary_mimicry.py'),
        'parser_module_sha256': Path(__file__).with_name('run_boundary_go_recovery.py'),
        'transport_sha256': Path(__file__).with_name('opencode_go_client_v2.py')}
    base.dump(RUN/'freeze.json', {**{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()},
        'created_utc': now(), 'model_calls_at_freeze': 0})
    base.RUN = RUN
    status({IDENT:record}, 0, 'PREPARED')
    print(json.dumps({'state':'PREPARED','planned':1,'source_words':[len(s['source_text'].split()) for s in sources]}))


def execute(key_stdin):
    freeze = base.read(RUN/'freeze.json')
    paths = {'sources_sha256':RUN/'sources_frozen.json','seats_sha256':RUN/'seats_frozen.json',
        'runner_sha256':Path(__file__), 'case2_runner_sha256':Path(case2.__file__),
        'base_runner_sha256':Path(base.__file__),
        'templates_sha256':Path(__file__).with_name('prepare_boundary_mimicry.py'),
        'parser_module_sha256':Path(__file__).with_name('run_boundary_go_recovery.py'),
        'transport_sha256':Path(__file__).with_name('opencode_go_client_v2.py')}
    for key,path in paths.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest()==freeze[key]
    base.RUN = RUN
    base.next_turn = case2.next_turn
    base.parse = case2.parse
    base.status = status
    base.execute(key_stdin)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--key-stdin',action='store_true')
    args=parser.parse_args()
    if args.prepare:
        prepare()
    if args.execute:
        execute(args.key_stdin)
