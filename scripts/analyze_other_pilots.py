"""Audit local Arena captures; produce descriptive summaries, not inference."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1] / 'v0_2_other'
RUN = ROOT / 'runs/arena_20261002_other_pairs01'
if not RUN.exists():
    RUN = ROOT / 'published_runs/arena_20261002_other_pairs01'
JS = "const fs=require('fs'),root=process.argv[1],C=require(root+'/console.js'),D=JSON.parse(fs.readFileSync(root+'/bundle.json','utf8')),r=JSON.parse(fs.readFileSync(0,'utf8')),c=D.cases.find(c=>c.case_id===r.case_id);console.log(JSON.stringify({steps:C.stepsFor(c),prompts:Object.fromEntries(Object.keys(r.sent_prompts).map(k=>[k,C.buildPrompt(D,c,r,k)])),diagnostic:C.diagnostic(c,r),parsed:Object.fromEntries(Object.entries(r.raw).map(([k,v])=>[k,C.parseObject(v)]))}));"

def main():
    data = json.loads((ROOT / 'bundle.json').read_text(encoding='utf-8'))
    rows, deviations, hashes = [], [], []
    for case in data['cases']:
        path = RUN / 'logs' / (case['case_id'] + '.json')
        if not path.exists():
            rows.append(dict(case=case['case_id'], status='not_started', replies=0, stages={}))
            continue
        rec = json.loads(path.read_text(encoding='utf-8'))
        out = json.loads(subprocess.run([shutil.which('node'), '-e', JS, str(ROOT)], input=json.dumps(rec), text=True, encoding='utf-8', capture_output=True, check=True).stdout)
        assert rec['case_sha256'] == case['case_sha256']
        assert all(out['prompts'][key] == value for key, value in rec['sent_prompts'].items())
        for key, raw in rec['raw'].items():
            cap = rec['captures'][key]
            assert cap['raw'] == raw and cap['prompt'] == rec['sent_prompts'][key]
            expected_model = 'gemini-3.8-flash-high' if key.startswith('judge_') else 'claude-sonnet-5-5-high'
            assert cap['visible_model'] == expected_model
            field = 'explanation' if key.startswith('opening_') else 'reason' if key.startswith('judge_') else 'answer'
            count = len(out['parsed'][key].get(field, '').split())
            low, high = (100, 140) if field == 'explanation' else (0, 50) if field == 'reason' else (60, 100)
            if not low <= count <= high:
                deviations.append(dict(case=case['case_id'], step=key, field=field, words=count, allowed=[low, high]))
            hashes.append(dict(case=case['case_id'], step=key, prompt_sha256=hashlib.sha256(cap['prompt'].encode()).hexdigest(), raw_sha256=hashlib.sha256(raw.encode()).hexdigest()))
        stages = {}
        for stage in ['P0', 'P1', 'P2', 'P3', 'N', 'E']:
            obj = out['parsed'].get('judge_' + stage)
            if obj:
                target = int(case['informed_seat'] == 'A')
                stages[stage] = dict(p_informed_A=obj['p_informed_A'], p_informed=obj['p_informed_A'] if target else 1-obj['p_informed_A'], pick=obj['pick'], correct=obj['pick'] == case['informed_seat'], insufficient_evidence=obj['insufficient_evidence'], brier=(obj['p_informed_A']-target)**2, reason=obj['reason'])
        rows.append(dict(case=case['case_id'], informed_seat=case['informed_seat'], status=rec['status'], replies=len(rec['raw']), missing=[key for key in out['steps'] if key not in rec['raw']], diagnostic=out['diagnostic'], stages=stages, platform_interventions=len({item['step'] for item in rec.get('platform_observations', []) if item.get('type') == 'anonymous_comparison'}), issue_flags=rec.get('issue_flags', [])))
    completed_priors = 0
    for prefix, prompt in data['prior_prompts'].items():
        path = RUN / ('prior_' + prefix + '.json')
        if path.exists():
            prior = json.loads(path.read_text(encoding='utf-8'))
            assert prior['prompt'] == prompt
            if prior.get('raw'):
                parsed = json.loads(prior['raw'])
                values = parsed['p_pass']
                if isinstance(values, dict):
                    values = [values[key] for key in ['Q1','Q2','Q3']]
                else:
                    assert isinstance(values, list) and len(values) == 3
                    assert 'p_pass_array_not_keyed' in prior.get('issue_flags', [])
                assert all(isinstance(value, (int, float)) and 0 <= value <= 1 for value in values)
                completed_priors += 1
    result = dict(status='complete' if all(row['status'] == 'completed' for row in rows) and completed_priors == 4 else 'partial', planned_background_pairs=4, complete_background_pairs=sum(all(row['status']=='completed' for row in rows if row['case'].startswith(prefix)) for prefix in ['T01','H01','E01','L01']), completed_game_replies=sum(row['replies'] for row in rows), planned_game_replies=112, completed_prior_replies=completed_priors, receipt_audit='passed', cases=rows, deviations=deviations, claim_boundary='Four planned background pairs; descriptive only. No population, grounding, or active-questioning causal claim.')
    (ROOT / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (RUN / 'receipt_hashes.json').write_text(json.dumps(hashes, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], completed_game_replies=result['completed_game_replies'], receipt_audit=result['receipt_audit'], cases=[dict(case=row['case'],status=row['status'],replies=row['replies'],diagnostic=row.get('diagnostic'),stages=row['stages']) for row in rows], deviations=deviations), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
