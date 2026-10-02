"""Audit real UI captures against frozen Core prompts; no model or network calls."""
import json, subprocess, base64
from pathlib import Path
import operator_capture as cap

report=[]
for path in sorted((cap.RUN/'logs').glob('*.json')):
    r=json.loads(path.read_text(encoding='utf-8-sig'))
    shot=r.get('rendered_sessions',{}).get('evidence_screenshot',{})
    if shot.get('base64'):
        image_path=cap.RUN/'screenshots'/f'{r["case_id"]}_judge_E.jpg'
        image_path.parent.mkdir(exist_ok=True)
        image_path.write_bytes(base64.b64decode(shot.pop('base64'),validate=True))
        shot['file']=str(image_path.relative_to(cap.RUN)).replace('\\','/')
    v=cap.canonical(r)
    mismatches=[k for k,p in r['sent_prompts'].items() if v['prompts'][k]!=p]
    lengths=[]
    for k,raw in r['raw'].items():
        obj=json.loads(raw)
        field='explanation' if k.startswith('opening') else 'answer' if k.startswith('answer') else 'reason'
        n=len(obj[field].split())
        low,high=(100,140) if field=='explanation' else (60,100) if field=='answer' else (0,50)
        if not low<=n<=high: lengths.append(dict(step=k,field=field,words=n,allowed=[low,high]))
    format_deviations=[]
    rendered_mismatches=[]
    if r['status']=='completed' and r.get('rendered_sessions'):
        full={}
        for seat in ('A','B'):
            keys=[f'answer_3_{seat}',f'answer_2_{seat}',f'answer_1_{seat}',f'opening_{seat}']
            vals=r['rendered_sessions']['speaker_'+seat]['responses']
            if len(vals)!=4:raise ValueError('Unexpected speaker response count')
            full.update(zip(keys,vals))
        full.update(zip(['judge_P3','judge_P2','judge_P1','judge_P0'],r['rendered_sessions']['judge']['responses']))
        for phase in ('N','E'):full['judge_'+phase]=r['rendered_sessions']['judge_'+phase]['responses'][0]
        for k,text in full.items():
            start=text.find('{')
            obj,end=json.JSONDecoder().raw_decode(text[start:])
            if obj!=json.loads(r['raw'][k]):rendered_mismatches.append(k)
            before=text[:start].strip()
            if before.endswith('JSON'):before=before[:-4].strip()
            after=text[start+end:].strip()
            if before or after:format_deviations.append(dict(step=k,kind='commentary_outside_required_json'))
        r['rendered_full_by_step']=full
    flags=set(r.get('issue_flags',[]))
    if 'model_change' in flags:
        flags.remove('model_change');flags.add('unexpected_model_change')
    if lengths or format_deviations or r.get('platform_observations'): flags.add('other')
    r['issue_flags']=sorted(flags)
    r['word_length_deviations']=lengths
    r['format_deviations']=format_deviations
    r['capture_provenance']='Verbatim rendered response text or code-block content captured through browser UI; Markdown wrappers/UI JSON labels not retained. Prompt receipts verified byte-for-byte with frozen Core.buildPrompt. Platform alternatives stored separately.'
    duplicate=[k for k,raw in r['raw'].items() if list(r['raw'].values()).count(raw)>1]
    row=dict(case_id=r['case_id'],status=r['status'],raw_count=len(r['raw']),sent_count=len(r['sent_prompts']),prompt_mismatches=mismatches,rendered_json_mismatches=rendered_mismatches,duplicate_raw_steps=duplicate,missing_steps=[k for k in v['steps'] if not r['raw'].get(k)],word_length_deviations=lengths,format_deviations=format_deviations,issue_flags=r['issue_flags'])
    report.append(row)
    path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(cap.RUN/'capture_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if any(x['prompt_mismatches'] or x['duplicate_raw_steps'] or x['rendered_json_mismatches'] for x in report):raise SystemExit(2)
