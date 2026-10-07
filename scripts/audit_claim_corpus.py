"""Validate retrospective clause labels and interaction ledgers; export descriptive tables."""
import collections,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'epistemic_boundary_mimicry/analysis/claim_audit_20261007'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def main():
    f=read(BASE/'freeze.json');assert sha(BASE/'PROTOCOL.md')==f['protocol_sha256_lf']
    old=ROOT/'epistemic_boundary_mimicry/analysis/offline_coding_20261005'
    assert sha(old/'freeze.json')==f['original_freeze_sha256_lf']
    summaries=[];export=[];missing=[];annotation_hashes={};corpora={}
    for filename,digest in f['inputs'].items():
        p=BASE/'inputs'/filename;assert sha(p)==digest
        x=read(p);corpora[x['id']]=x
        labelpath=BASE/'labels'/filename
        if not labelpath.exists():missing.append(filename);continue
        a=read(labelpath);assert a['id']==x['id'];annotation_hashes[filename]=sha(labelpath)
        for m in x['messages']:
            if m['role'] not in ['A','B']:continue
            end=0
            for u in m['units']:
                assert not m['reply'][end:u['start']].strip()
                end=u['end']
            assert not m['reply'][end:].strip()
        units={u['id']:(m,u) for m in x['messages'] if m['role'] in ['A','B'] for u in m['units']}
        assert len(a['labels'])==len(units),(x['id'],'count')
        assert len({v[0] for v in a['labels']})==len(units) and {v[0] for v in a['labels']}==set(units)
        counts=collections.Counter();state=collections.Counter();role_counts={};flagged=[]
        for row in a['labels']:
            assert len(row)==8,(x['id'],row)
            uid,kind,relation,source_ids,silence,transition,priors,note=row
            m,u=units[uid];seat=m['role'];ref=x['references'][seat]
            assert u['text']==m['reply'][u['start']:u['end']]
            assert kind in ['assertion','source_boundary','inference','conversational']
            assert relation in ['supported','contradicted','unspecified','ambiguous','not_applicable']
            assert transition in ['new_detail','consistent_elaboration','revision','contradiction','ambiguous','not_applicable']
            source={v['id']:v for v in ref['source_units']}
            assert isinstance(source_ids,list) and set(source_ids)<=set(source),(x['id'],uid,'sourceids')
            for i in source_ids:
                s=source[i];assert s['text']==ref['source_text'][s['start']:s['end']]
            if relation=='supported' and kind!='conversational':assert source_ids or silence,(x['id'],uid,'support evidence')
            if relation=='contradicted':assert source_ids and note,(x['id'],uid,'contradiction evidence')
            if relation=='ambiguous':assert note,(x['id'],uid,'ambiguous note')
            if ref['reference_type']=='own_source':assert transition=='not_applicable' and not priors
            if transition in ['revision','contradiction']:assert priors and note
            for prior in priors:
                pm,pu=units[prior]
                assert pm['role']==seat and (pm['message_index']<m['message_index'] or
                    (pm['message_index']==m['message_index'] and pu['start']<u['start'])),(x['id'],uid,prior,'prior role/order')
            role='Reader' if ref['reference_type']=='own_source' else 'Bluffer_proxy'
            counts[kind+':'+relation]+=1;role_counts.setdefault(role,collections.Counter())[kind+':'+relation]+=1
            state[transition]+=1
            if relation in ['contradicted','ambiguous'] or transition in ['revision','contradiction']:flagged.append(uid)
            export.append({'trajectory':x['id'],'case_id':x['case_id'],'seat':seat,'role':role,
                'question_index':m['question_index'],'unit_id':uid,'answer_span':u['text'],
                'type':kind,'relation':relation,'source_span':' || '.join(source[i]['text'] for i in source_ids),
                'silence_check':silence or '', 'state_transition':transition,'prior_unit_ids':'|'.join(priors),
                'state_scope':'cross_answer' if any(units[v][0]['message_index']<m['message_index'] for v in priors) else ('within_answer' if priors else 'none'),
                'note':note or '', 'terminal_ref':x['id'] if x['terminal'] else 'none_partial'})
        summaries.append({'id':x['id'],'case_id':x['case_id'],'condition':x['condition'],
            'units':len(units),'counts':dict(counts),'by_role':{k:dict(v) for k,v in role_counts.items()},
            'state_counts':dict(state),'flagged_units':flagged})
    if missing:raise SystemExit(json.dumps({'missing_labels':missing}))
    for finding in read(BASE/'subclaim_findings.json')['findings']:
        x=corpora[finding['id']]
        matches=[(m,u) for m in x['messages'] if m['role'] in ['A','B'] for u in m['units'] if u['id']==finding['unit_id']]
        assert len(matches)==1
        m,u=matches[0];assert finding['span'] in u['text']
        assert set(finding['source_ids'])<={s['id'] for s in x['references'][m['role']]['source_units']}
    query=read(BASE/'query_review.json');rationale=read(BASE/'rationale_review.json')
    assert len(query['rows'])==57
    expected={(x['id'],m['message_index']) for x in corpora.values() for m in x['messages'] if m['role']=='J'}
    assert {(r['id'],r['message_index']) for r in query['rows']}==expected
    for q in query['rows']:
        x=corpora[q['id']];messages={m['message_index']:m for m in x['messages']};m=messages[q['message_index']]
        assert q['query_span'] in m['question'] and q['adaptivity'] in ['linked','generic_or_independent','ambiguous']
        if q.get('earlier_answer'):
            e=q['earlier_answer'];assert e['message_index']<m['message_index'] and e['span'] in messages[e['message_index']]['reply']
    assert set(rationale['records'])=={x['id'] for x in corpora.values() if x['terminal']}
    for ident,record in rationale['records'].items():
        x=corpora[ident];messages={m['message_index']:m for m in x['messages']}
        assert record['terminal_reason']==x['terminal']['reason']
        for c in record['components']:
            assert c['span'] in x['terminal']['reason']
            if c.get('evidence'):
                e=c['evidence'];assert e['span'] in messages[e['message_index']].get('reply',messages[e['message_index']].get('question',''))
    terminals=read(BASE/'terminal_units.json')['records']
    assert set(terminals)==set(rationale['records'])
    terminal_counts=collections.Counter()
    for ident, rows in terminals.items():
        reason=corpora[ident]['terminal']['reason']
        assert [r['unit_id'] for r in rows]==list(range(len(rows)))
        covered=set()
        for r in rows:
            assert r['text']==reason[r['start']:r['end']] and r['note']
            assert r['support'] in ['S','A','U','C']
            covered.update(range(r['start'],r['end']))
            terminal_counts[r['support']]+=1
        assert all(i in covered for i,c in enumerate(reason) if not c.isspace())
    premises=read(BASE/'premise_responses.json');paired=collections.defaultdict(collections.Counter)
    for p in premises['opportunities']:
        x=corpora[p['id']];messages={m['message_index']:m for m in x['messages']};q=messages[p['query_index']]
        assert p['query_span'] in q['question']
        assert p['mode'] in ['assertive_presupposition','recognition_candidate','hypothetical']
        for seat, ids in p['source_ids_by_seat'].items():
            assert set(ids)<={s['id'] for s in x['references'][seat]['source_units']}
        if p.get('matched_judge_first'):
            assert p['origin']=='judge_first' and len(p['answer_responses'])==2
            assert {a['seat'] for a in p['answer_responses']}=={'A','B'}
            assert {v['reference_type'] for v in x['references'].values()}=={'own_source','target_source_proxy_for_bluffer'}
            assert x['references']['A']['source_text']==x['references']['B']['source_text']
            assert set(p['source_relation_by_seat'].values())<={'unspecified','contradicted'}
        for answer in p['answer_responses']:
            m=messages[answer['message_index']];assert m['role']==answer['seat'] and m['question_index']==q['question_index']
            assert answer['span'] in m['reply']
            assert answer['response'] in ['accept_as_source','reject_as_source','qualify','hypothetical_only','unaddressed','ambiguous']
            if p.get('matched_judge_first'):
                role='Reader' if x['references'][m['role']]['reference_type']=='own_source' else 'Bluffer'
                paired[p['id']+':'+role][answer['response']]+=1
    result={'status':'retrospective model-assisted sentence/clause audit; not human reliability',
        'counts':f['counts'],'experimental_api_calls':0,'missing':missing,'annotation_sha256_lf':annotation_hashes,
        'review_sha256_lf':{name:sha(BASE/name) for name in ['query_review.json','rationale_review.json','terminal_units.json','premise_responses.json','subclaim_findings.json']},
        'query_adaptivity':dict(collections.Counter(q['adaptivity'] for q in query['rows'])),
        'terminal_units':sum(terminal_counts.values()),'terminal_unit_support':dict(terminal_counts),
        'premise_opportunities':len(premises['opportunities']),'matched_judge_first_counts':{k:dict(v) for k,v in paired.items()},
        'trajectories':summaries}
    (BASE/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    with (BASE/'claim_table.tsv').open('w',encoding='utf8',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(export[0]),delimiter='\t');writer.writeheader();writer.writerows(export)
    print(json.dumps({k:v for k,v in result.items() if k not in ['trajectories','annotation_sha256_lf']}))
if __name__=='__main__':main()
