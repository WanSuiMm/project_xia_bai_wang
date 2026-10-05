"""Validate model-assisted event annotations and frozen replay cohort; no provider calls."""
import hashlib,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'epistemic_boundary_mimicry'
OUT=BASE/'analysis/offline_coding_20261005'

def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def audit():
 f=read(OUT/'freeze.json');errors=[];summary=[];annotation_hashes={}
 assert sha(BASE/'analysis/CODEBOOK_20261005.md')==f['codebook_sha256_lf']
 assert sha(BASE/'analysis/transcript_reuse_20261005/inventory.json')==f['inventory_sha256_lf']
 assert sha(OUT/'replay_cohort.json')==f['cohort_sha256_lf']
 assert sha(OUT/'public_contexts.json')==read(OUT/'public_context_provenance.json')['public_contexts_sha256_lf']
 cohort=read(OUT/'replay_cohort.json')
 assert len(cohort['records'])==7 and cohort['excluded_partial_ids']==['EB06_D2_symmetric_frozen']
 for r in cohort['records']:
  p=r['payload'];assert set(p)=={'public_context','dialogue'}
  assert hashlib.sha256(json.dumps(p,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==r['payload_sha256']
  for q in p['dialogue']:
   assert set(q)=={'question_index','target','question','answers'}
   assert all(set(a)=={'speaker','reply'} for a in q['answers'])
 for filename,digest in f['inputs'].items():
  path=OUT/'inputs'/filename;assert sha(path)==digest
  a_path=OUT/'annotations'/filename
  if not a_path.exists():errors.append('missing:'+filename);continue
  x=read(path);a=read(a_path);assert a['id']==x['id']
  assert sha(ROOT/x['evidence_path'])==x['evidence_sha256_lf']
  annotation_hashes[filename]=sha(a_path)
  messages={m['message_index']:m for m in x['messages']}
  speakers={i for i,m in messages.items() if m['role'] in ['A','B']}
  questions={i for i,m in messages.items() if m['role']=='J'}
  assert len(a['speaker_events'])==len(speakers) and {e['message_index'] for e in a['speaker_events']}==speakers
  assert len(a['judge_questions'])==len(questions) and {e['message_index'] for e in a['judge_questions']}==questions
  counts=collections.Counter();categories=set();adaptive=0;premises=0
  for e in a['speaker_events']:
   m=messages[e['message_index']];assert m['role']==e['seat']
   assert set(e['labels'])<=set(['source_assertion','qualified_inference','boundary_absence','uncertainty'])
   source=x['references'][e['seat']]['source_text']
   if e.get('boundary_span'):assert e['boundary_span'] in m['reply'],(x['id'],'boundary_span')
   if 'boundary_absence' in e['labels']:assert e.get('boundary_span'),(x['id'],'missing boundary_span')
   kinds=set()
   for issue in e['issues']:
    assert issue['span'] and issue['span'] in m['reply'],(x['id'],e['message_index'],'issue span')
    assert issue['kind'] in ['overclaim','source_contradiction','underclaim','inference_as_source','internal_inconsistency']
    assert issue['relation'] in ['supported','contradicted','unspecified','ambiguous']
    assert issue['attribution'] in ['source_assertion','qualified_inference','boundary_absence','uncertainty']
    if issue['relation']!='ambiguous' and issue['kind']=='overclaim':
     assert issue['relation']=='unspecified' and issue['attribution']=='source_assertion',(x['id'],'overclaim definition')
    if issue['relation']!='ambiguous' and issue['kind']=='source_contradiction':
     assert issue['relation']=='contradicted',(x['id'],'source contradiction definition')
    if issue.get('source_evidence'):assert issue['source_evidence'] in source,(x['id'],e['message_index'],'source span')
    if issue.get('earlier_evidence'):
     old=issue['earlier_evidence'];prior=messages[old['message_index']]
     assert old['message_index']<e['message_index'] and old['span'] in prior.get('reply','')
    # Ambiguous findings stay in qualitative records, outside definitive flag counts.
    if issue['relation']!='ambiguous':kinds.add(issue['kind'])
   for k in kinds:counts[k]+=1
   if 'boundary_absence' in e['labels']:counts['boundary_absence']+=1
  for q in a['judge_questions']:
   m=messages[q['message_index']];assert q['question_index']==m['question_index']
   assert set(q['categories'])<=set(['fact_probe','boundary_probe','consistency_followup','presupposition_probe','quotation_reconstruction','provenance_probe','consequence_probe'])
   categories.update(q['categories'])
   if q.get('premise_span'):assert q['premise_span'] in m['question']
   if q.get('adaptive_to'):
    old=q['adaptive_to'];prior=messages[old['message_index']]
    assert old['message_index']<q['message_index'] and old['span'] in prior.get('reply','')
    adaptive+=1
   if q.get('presupposition_status') in ['source_unspecified','source_contradicted']:premises+=1
  terminal=x['terminal'];rationale=a['rationale_components'];assert bool(rationale)==bool(terminal)
  relevance=collections.Counter();support=collections.Counter()
  for c in rationale:
   assert c['span'] and c['span'] in terminal['reason'],(x['id'],'rationale span')
   assert c['support'] in ['supported','misread','unsupported','ambiguous']
   assert c['target_relevance'] in ['potentially_identifying','not_identifying','limits_identification','not_applicable']
   if c.get('evidence'):
    old=c['evidence'];m=messages[old['message_index']]
    assert old['span'] in m.get('reply',m.get('question','')),(x['id'],'rationale evidence')
   if c.get('source_evidence'):assert any(c['source_evidence'] in ref['source_text'] for ref in x['references'].values()),(x['id'],'rationale source span',c['source_evidence'])
   support[c['support']]+=1;relevance[c['target_relevance']]+=1
  summary.append({'id':x['id'],'case_id':x['case_id'],'condition':x['condition'],
   'speaker_events':len(speakers),'ask_actions':len(questions),'terminal':terminal['action'] if terminal else None,
   'speaker_flag_event_counts':dict(counts),'ask_categories_present':sorted(categories),
   'evidence_linked_followups':adaptive,'source_unsupported_premise_questions':premises,
   'rationale_support_counts':dict(support),'rationale_relevance_counts':dict(relevance)})
 result={'audit_errors':errors,'covered_trajectories':len(summary),'speaker_events':sum(r['speaker_events'] for r in summary),
  'ask_actions':sum(r['ask_actions'] for r in summary),'complete_replay_cohort':7,'api_calls':0,
  'annotation_status':'model-assisted first pass; exact-span validated; no independent human reliability',
  'annotation_sha256_lf':annotation_hashes,'rows':summary}
 (OUT/'coding_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:v for k,v in result.items() if k not in ['rows','annotation_sha256_lf']}))
 if errors:raise SystemExit(1)


if __name__=='__main__':audit()
