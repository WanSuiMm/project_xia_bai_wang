"""Retrospective primary review of query links and terminal inference; no provider calls."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'epistemic_boundary_mimicry/analysis/offline_coding_20261005'
OUT=ROOT/'epistemic_boundary_mimicry/analysis/claim_audit_20261007'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    if (OUT/'query_review.json').exists():raise SystemExit('Preserve prior review')
    queries=[];rationales={}
    for p in sorted((OLD/'annotations').glob('*.json')):
        a=read(p);x=read(OUT/'inputs'/p.name);messages={m['message_index']:m for m in x['messages']}
        for q in a['judge_questions']:
            m=messages[q['message_index']];prior=q.get('adaptive_to')
            verdict='linked' if prior else 'generic_or_independent'
            note=q['explanation']+' Textual dependence does not prove counterfactual policy adaptation.'
            if x['id']=='EB05_D1_symmetric_frozen' and q['question_index']==4:
                verdict='ambiguous';note='The earlier ledger distinction does not specifically appear in this later question. Generic full-description and further-details requests are not enough to certify adaptation.'
            if x['id']=='EB06_D2_symmetric_frozen' and q['question_index']==4:
                note='Requests exact header, counts and limitation quotations after the previous answer gave near-exact wording. The older explanation incorrectly described an opening-caution reconciliation from a different direction; this is a quotation-follow-up, not that reconciliation.'
            if x['id']=='EB04_D1_symmetric_frozen' and q['question_index']==2:
                prior={'message_index':1,'span':'Two of the improved tags also lost small flakes from already cracked margins;'}
                verdict='linked';note='The later query specifically asks for the two flake losses disclosed in the first answer, including exact source wording. The old zero-link count missed this textual dependence.'
            if x['id']=='EB01_D1_symmetric_frozen' and q['question_index']==3:
                candidates=[v for v in x['messages'] if v['role'] in ['A','B'] and v['message_index']<m['message_index'] and 'two days' in v['reply']]
                if candidates:
                    v=candidates[-1];prior={'message_index':v['message_index'],'span':'two days'}
                    verdict='linked';note='Question explicitly says beyond the two days you mentioned, connecting to the earlier interval statement; does not prove information gain.'
            queries.append({'id':x['id'],'message_index':m['message_index'],'question_index':m['question_index'],
                'query_span':m['question'],'target':m['target'],'categories':q['categories'],
                'adaptivity':verdict,'earlier_answer':prior,'note':note})
        if x['terminal']:
            components=[]
            for c in a['rationale_components']:
                c=dict(c);span=c['span'];tags=[]
                if any(v in span.lower() for v in ['public context','shared brief','public-context','alignment','host\'s description']):tags.append('public_context_alignment')
                if any(v in span.lower() for v in ['derivative','authored','secondary','source-anchored','document','retelling']):tags.append('provenance_inference')
                if any(v in span.lower() for v in ['drift','contradict','bend under pressure','only when pressed','late']):tags.append('late_disclosure_or_consistency_inference')
                if any(v in span.lower() for v in ['boundary','denial','silence','does not','cannot supply']):tags.append('source_boundary_inference')
                if any(v in span.lower() for v in ['impossible','could not','honest','proving','evidently']):tags.append('strong_access_or_psychology_claim')
                if not tags:tags=['descriptive_comparison_or_limits']
                if x['id']=='EB02_D1_strong' and span.startswith("A's account fits"):
                    c['target_relevance']='not_identifying';c['explanation']+=' Common task-frame fit alone does not identify access.'
                if span.startswith('Both speakers clearly worked from a document'):
                    c['support']='ambiguous';c['explanation']+=' Source fidelity is visible to the auditor, but the Judge cannot prove access history solely from the reported text.'
                if 'behaviorally impeccable' in span or 'remained perfectly stable' in span:
                    c['support']='ambiguous';c['explanation']+=' Absolute perfection is broader than verified numerical stability; source-clause fidelity is audited separately.'
                c['taxonomy_tags']=tags;components.append(c)
            rationales[x['id']]={'terminal_reason':x['terminal']['reason'],'components':components}
    write(OUT/'query_review.json',{'method':'all ASK screened; revised textual-link assessment, not causal policy test','rows':queries})
    write(OUT/'rationale_review.json',{'method':'primary review of prior exact components, source fidelity kept separate from target relevance','records':rationales})
    print(json.dumps({'queries':len(queries),'terminals':len(rationales)}))
if __name__=='__main__':main()
