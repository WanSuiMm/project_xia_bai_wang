"""One fresh ecological symmetric-source control, offline freeze then bounded API run."""
import argparse
import hashlib
import json
import random
from pathlib import Path
import run_boundary_go_case2 as case2
from opencode_go_client_v2 import now, session_id
from prepare_boundary_mimicry import SPEAKER, READER, JUDGE

base = case2.base
RUN = base.BASE / 'runs/opencode_go_20261004_fresh_frozen01'
IDENT = 'EB03_D1_symmetric_frozen'
SEED = 2026100421
PUBLIC = ('A fictional ecological field station records where an invented adult moth rests '
          'when cloth shade screens are rearranged around its enclosure. A finite research '
          'note describes short observations, a follow-up and limits on what the observations '
          'establish. The station, species and records are invented. Discuss this particular '
          'note rather than established facts about a real species.')
ORIGINAL_STATUS = base.status


def source(rng, index):
    station = rng.choice(['Linden Reach', 'Tamar Cove', 'Harrow Fen', 'Nacre Ridge'])
    species = rng.choice(['silverfold moth', 'umberveil moth', 'reedmantle moth', 'palehinge moth'])
    author = rng.choice(['Nessa Vail', 'Tarin Moss', 'Edda Roan', 'Sol Arven'])
    year = rng.choice([2017, 2019, 2021, 2023])
    month = rng.choice(['April', 'May', 'September'])
    total = rng.choice([24, 30, 36])
    responsive = total - rng.choice([5, 7, 9])
    follow = rng.choice([4, 5, 6])
    minutes = rng.choice([12, 18, 24])
    blocks = [
        f'{author} kept a field-station note at {station} in {month} {year}. It concerns '
        f'{total} adult {species}s housed individually in mesh enclosures. The animals were '
        'collected from one sheltered grove. Their resting positions were recorded before '
        'any cloth screen was moved. The note concerns resting behavior in enclosures, '
        'not the abundance or migration of moths outside the station.',
        f'A cloth screen shaded one side of each enclosure. Staff moved that screen to the '
        f'opposite side, waited {minutes} minutes, and recorded resting position again. '
        'They left the support branches in place, did not turn the enclosures, and used '
        'the same recording sheet before and after each move. A blank resting-position '
        'entry means the observer could not locate the animal; it is not a recorded '
        'absence of movement. The note supplies no instrument readings for illumination.',
        f'After the screen move, {responsive} animals rested on the newly shaded side; '
        f'{total-responsive} remained at their recorded original positions. No individual '
        'tracking path was recorded between the two observations. Staff therefore could '
        'not tell whether an animal moved directly or explored several positions first. '
        'The record does not classify nonresponders as a different variety.',
        f'The next afternoon, {follow} of the responding animals received a reverse screen '
        f'move. All {follow} were found on the newly shaded side at the second observation. '
        'The branch positions were unchanged. This short follow-up shows repeatable '
        'position changes in that selected subset; it does not estimate a response rate '
        'for an independent sample.',
        'The author treats shelter from light as a working explanation, not an isolated '
        'mechanism. The screen might also alter air movement or local temperature. '
        'The observers did not run a screen-free control and did not compare juveniles '
        'with adults. No sensory-organ examination was performed. The note contains '
        'no sex breakdown, enclosure dimensions or thermometer specification. It does '
        'not report behavior after release. Its conclusion is restricted to the recorded '
        'screen moves and cannot establish a seasonal habitat preference.']
    # Draw document organization independently for each source, without reference
    # to the other source or the later target designation.
    if rng.randrange(2):
        blocks = [blocks[0], blocks[1], blocks[3], blocks[2], blocks[4]]
    text = '\n\n'.join(blocks)
    return {'source_id': 'EB03_source_' + str(index), 'source_title': 'Resting-position field note',
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
    t = {'id': IDENT, 'case_id': 'EB03', 'condition': 'symmetric_frozen',
        'speaker_model': 'qwen3.8-max', 'judge_model': 'glm-5.3', 'target_seat': target,
        'target_source_id': seat_sources[target_index]['source_id'],
        'other_source_id': seat_sources[1-target_index]['source_id'], 'knower': target}
    bundle = {'study': 'fresh symmetric-source pilot', 'trajectories': [t],
        'cases': [{'case_id': 'EB03', 'public_context': PUBLIC, 'sources': sources}],
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
