"""Offline canonical API inventory and terminal-blind Frozen transcript projection; no API imports."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'epistemic_boundary_mimicry'
OUT=BASE/'analysis/transcript_reuse_20261005'
FOLDERS=['go_two_completed_20261004','go_frozen_recovery_20261004',
    'go_reverse_recovery_20261004','go_case02_three_20261004',
    'go_frozen_pair_completed_20261004','go_surface_diverse_cutoff_20261005']


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def context(folder,b,ident,case_id):
    if folder=='go_frozen_pair_completed_20261004':return b[ident]['public_context']
    if 'public_context' in b:return b['public_context']
    return next(c for c in b['cases'] if c['case_id']==case_id)['public_context']


def main():
    if OUT.exists():raise SystemExit('Preserve existing analysis output')
    rows=[];transcripts=[];seen=set();physical=0;valid_answers=0
    for folder in FOLDERS:
        directory=BASE/'published_runs'/folder
        manifest=read(directory/'manifest.json')
        for e in manifest['files']:
            expected=e.get('sha256_lf_utf8',e.get('sha256'))
            if expected:
                data=(directory/e['file']).read_bytes()
                assert hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()==expected or hashlib.sha256(data).hexdigest()==expected
        b=read(directory/'bundle.json')
        for path in sorted(directory.glob('EB*.json')):
            r=read(path);ident=r['id'];assert ident not in seen;seen.add(ident)
            interactions=[];valid=[]
            for i,m in enumerate(r['messages']):
                v=m.get('parsed')
                if m.get('reply') is False or not isinstance(v,dict) or m.get('setup'):continue
                if m['role']=='J' and v.get('action')=='ASK':
                    interactions.append({'question_index':m['question_index'],'target':v['target'],
                        'question':v['question'],'answers':[], 'evidence_message_index':i})
                elif m['role'] in ['A','B'] and 'reply' in v:
                    q=next(x for x in interactions if x['question_index']==m['question_index'])
                    q['answers'].append({'speaker':m['role'],'reply':v['reply'],'evidence_message_index':i})
                    valid_answers+=1
                valid.append(m)
            assert len(interactions)==r['asks']
            complete=sum(set(a['speaker'] for a in q['answers'])==
                (set(['A','B']) if q['target']=='BOTH' else set([q['target']])) for q in interactions)
            terminal=r.get('terminal');physical+=len(r['messages'])
            rows.append({'id':ident,'case_id':r['case_id'],'condition':r['condition'],
                'readers':r['speaker_model'],'judge':r['judge_model'],'status':r['status'],
                'asks':r['asks'],'fully_answered_asks':complete,'physical_requests':len(r['messages']),
                'terminal_action':terminal['action'] if terminal else None,
                'terminal_pick':terminal.get('pick') if terminal else None,
                'confidence':terminal.get('confidence') if terminal else None,
                'evidence_path':path.relative_to(ROOT).as_posix(),
                'evidence_sha256_lf':hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
                'annotation_required':True})
            if r['condition']=='symmetric_frozen':
                # Deliberately exclude source text, role setup prompts, terminal decisions,
                # rationales, target labels, confidence and original scoring from the payload.
                payload={'public_context':context(folder,b,ident,r['case_id']),
                    'dialogue':[{'question_index':q['question_index'],'target':q['target'],
                        'question':q['question'],
                        'answers':[{'speaker':a['speaker'],'reply':a['reply']} for a in q['answers']]}
                        for q in interactions]}
                assert set(payload)=={'public_context','dialogue'}
                transcripts.append({'id':ident,'completed':terminal is not None,
                    'default_endpoint_replay_eligible':terminal is not None,
                    'payload':payload,
                    'evidence_mapping':interactions,
                    'payload_sha256':hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest()})
    frozen=[r for r in rows if r['condition']=='symmetric_frozen']
    other=[r for r in rows if r['condition']!='symmetric_frozen']
    assert len(frozen)==8 and sum(r['terminal_action'] is not None for r in frozen)==7
    assert len(other)==5 and all(r['terminal_action'] for r in other)
    summary={'api_calls':0,'canonical_trajectories':len(rows),'completed':sum(bool(r['terminal_action']) for r in rows),
        'independent_material_families':len(set(r['case_id'] for r in rows)),
        'frozen_complete':7,'frozen_partial':1,'strategic_complete':5,
        'frozen_complete_abstentions':sum(r['terminal_action']=='ABSTAIN' for r in frozen),
        'frozen_complete_selections':sum(r['terminal_action']=='STOP' for r in frozen),
        'physical_requests_in_canonical_records':physical,'speaker_answer_events':valid_answers,
        'scope':'API EB01-EB06 only; Arena studies excluded from this inventory',
        'warning':'six families are not uniform IID replicates; original failed prefixes excluded from endpoint counts, recoveries retained in provenance'}
    OUT.mkdir(parents=True)
    write(OUT/'inventory.json',{'summary':summary,'trajectories':rows})
    write(OUT/'frozen_terminal_blind_dialogues.json',{'purpose':'offline replay preparation only; no new Judge calls',
        'excluded_from_payload':['private_sources','role_setup','original_terminal','original_rationale','target_label','confidence','score'],
        'records':transcripts})
    print(json.dumps(summary))


if __name__=='__main__':main()
