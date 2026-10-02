"""Local synthetic fixtures only. No GPT/Claude/Gemini responses are fabricated as results."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('analyze',ROOT/'tools/analyze.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
CASES=json.loads((ROOT/'data/HOST_ONLY/cases.json').read_text(encoding='utf-8'))
BYID={c['case_id']:c for c in CASES}


def fixture(c):
    """Mechanically manufactured test data, never a live-model result."""
    k=c['informed_seat'];b='B' if k=='A' else 'A'
    raw={}
    for seat in ('A','B'):
        checks={q:c['gold'][q] for q in c['check_ids']}
        if seat==b:
            q=c['check_ids'][0];checks[q]='FAIL' if checks[q]=='PASS' else 'PASS'
        raw['opening_'+seat]=json.dumps({'explanation':'MECHANICAL TEST FIXTURE: not an actual model response.','checks':checks})
    for n in range(1,4):
        for seat in ('A','B'):
            raw[f'answer_{n}_{seat}']=json.dumps({'answer':'MECHANICAL TEST FIXTURE answer.'})
    for phase in a.PHASES:
        correct=phase in ('P3','E')
        pick=k if correct else b
        raw['judge_'+phase]=json.dumps({'p_informed_A':0.8 if pick=='A' else 0.2,'pick':pick,'insufficient_evidence':phase!='E','reason':'MECHANICAL TEST FIXTURE only.','question':'What happens for Q1?' if phase in ('P0','P1','P2') else None})
    return {'schema_version':'xbw.pilot.record/0.1','protocol_version':'0.1.0','case_id':c['case_id'],'case_sha256':c['case_sha256'],'run_id':'TEST-'+c['case_id'],'status':'completed','demo':False,'metadata':{'speaker_model':'FIXTURE_NOT_A_MODEL','judge_model':'FIXTURE_NOT_A_MODEL','tools_status':'not_verified'},'raw':raw,'manual_questions':{},'issue_flags':[],'notes':'UNIT TEST ONLY; never report as model evidence.','sent_prompts':{},'events':[]}

class DataTests(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(Counter(c['split'] for c in CASES),{'main':20,'practice':2})
        self.assertEqual(len(BYID),22)
    def test_truth_and_checks(self):
        for c in CASES:
            self.assertEqual(len(c['inputs']),8)
            self.assertEqual(sum(v=='PASS' for v in c['gold'].values()),4)
            self.assertEqual(len(set(c['check_ids'])),3)
            self.assertTrue(set(c['check_ids'])<=set(c['gold']))
            self.assertEqual(len({tuple(r['inputs'].values()) for r in c['inputs']}),8)
    def test_balance(self):
        main=[c for c in CASES if c['split']=='main']
        for cfg in ('R1','R2'):
            rr=[c for c in main if c['config']==cfg]
            self.assertEqual(Counter(c['informed_seat'] for c in rr),{'A':5,'B':5})
            self.assertEqual(Counter(c['fresh_arm_first'] for c in rr),{'N':5,'E':5})
            first=[c for c in main[:4] if c['config']==cfg]
            self.assertEqual(Counter(c['informed_seat'] for c in first),{'A':1,'B':1})
            self.assertEqual(Counter(c['fresh_arm_first'] for c in first),{'N':1,'E':1})
    def test_hashes(self):
        for c in CASES:
            cp=dict(c);h=cp.pop('case_sha256')
            actual=hashlib.sha256(json.dumps(cp,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            self.assertEqual(h,actual)
    def test_public_has_no_host_fields(self):
        p=json.loads((ROOT/'data/public/cases.json').read_text(encoding='utf-8'))
        for c in p:
            self.assertNotIn('gold',c)
            self.assertNotIn('informed_seat',c)
            self.assertNotIn('private_text',c)
    def test_private_prompt_isolation(self):
        for c in CASES:
            for s in ('A','B'):
                text=(ROOT/f'prompts/ready/{c["case_id"]}/SPEAKER_{s}_OPEN.txt').read_text()
                self.assertNotIn('{{',text)
                self.assertEqual(c['private_text'] in text, s==c['informed_seat'])
                self.assertNotIn('case_sha256',text)
                self.assertNotIn('202610021352',text)
            judge=(ROOT/f'prompts/ready/{c["case_id"]}/JUDGE_INITIAL_TEMPLATE.txt').read_text()
            self.assertNotIn(c['private_text'],judge)
            self.assertNotIn('informed_seat',judge)
    def test_frozen_generator_reproduces(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,str(ROOT/'tools/regenerate_data.py'),'--output',d],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            x=json.loads((Path(d)/'data/HOST_ONLY/cases.json').read_text(encoding='utf-8'))
            self.assertEqual(x,CASES)

class AnalyzerTests(unittest.TestCase):
    def test_wilson(self):
        lo,hi=a.wilson(10,20)
        self.assertAlmostEqual(lo,0.299298,places=5)
        self.assertAlmostEqual(hi,0.700702,places=5)
        self.assertIsNone(a.wilson(0,0))
    def test_probability_validation(self):
        valid={'p_informed_A':0.5,'pick':'A','insufficient_evidence':True,'reason':'No evidence.'}
        self.assertEqual(a.parse_judge('```json\n'+json.dumps(valid)+'\n```')['p_informed_A'],0.5)
        for p in (True,1.2,-0.1,float('nan'),'0.5'):
            bad=dict(valid,p_informed_A=p)
            with self.assertRaises(ValueError):a.parse_judge(json.dumps(bad))
        with self.assertRaises(ValueError):a.parse_judge(json.dumps(dict(valid,p_informed_A=0.2)))
    def test_no_missing_imputation(self):
        c=CASES[0];r=fixture(c);del r['raw']['judge_E']
        ar=a.analyze_record(r,c)
        self.assertFalse(ar['points']['E']['valid'])
        self.assertFalse(ar['complete_responses'])
        self.assertEqual(a.stage_summary([ar],'E')['scorable_n'],0)
    def test_diagnostic_distinguishing(self):
        for c in CASES:
            self.assertEqual(a.diagnostic(c,fixture(c)['raw'])['status'],'distinguishing')
    def test_diagnostic_collision(self):
        c=CASES[0];r=fixture(c)
        for s in ('A','B'):
            r['raw']['opening_'+s]=json.dumps({'explanation':'TEST','checks':{q:c['gold'][q] for q in c['check_ids']}})
        self.assertEqual(a.diagnostic(c,r['raw'])['status'],'collision')
    def test_diagnostic_knower_error(self):
        c=CASES[0];r=fixture(c);s=c['informed_seat'];x=json.loads(r['raw']['opening_'+s]);q=c['check_ids'][0];x['checks'][q]='FAIL' if c['gold'][q]=='PASS' else 'PASS';r['raw']['opening_'+s]=json.dumps(x)
        self.assertEqual(a.diagnostic(c,r['raw'])['status'],'knower_commitment_error')
    def test_diagnostic_bad_format(self):
        c=CASES[0];r=fixture(c);r['raw']['opening_A']='not json'
        self.assertEqual(a.diagnostic(c,r['raw'])['status'],'unscorable')
    def test_pairing_and_brier(self):
        rows=[a.analyze_record(fixture(c),c) for c in CASES[:4]]
        s=a.summarize(rows,[])
        self.assertEqual(s['clean_pairs']['evidence_E_minus_N']['paired_n'],4)
        self.assertEqual(s['clean_pairs']['evidence_E_minus_N']['delta_accuracy'],1)
        self.assertEqual(s['clean_pairs']['evidence_E_minus_N']['wrong_to_right'],4)
        self.assertAlmostEqual(s['clean_pairs']['evidence_E_minus_N']['delta_brier'],-.60)
    def test_hard_flags_not_silently_deleted(self):
        c=CASES[0];r=fixture(c);r['issue_flags']=['private_leak']
        ar=a.analyze_record(r,c);s=a.summarize([ar],[])
        self.assertEqual(s['main_case_records'],1)
        self.assertEqual(s['clean_case_records'],0)
        self.assertEqual(s['all_recorded_stages']['E']['scorable_n'],1)
    def test_duplicate_detection(self):
        r=fixture(CASES[0])
        with tempfile.TemporaryDirectory() as d:
            for i in (1,2):(Path(d)/f'{i}.json').write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'Duplicate'):a.load_records(Path(d),BYID)
    def test_demo_and_practice_skipped(self):
        r=fixture(CASES[0]);r['demo']=True
        p=fixture(BYID['D01'])
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'export.json').write_text(json.dumps({'schema_version':'xbw.pilot.export/0.1','records':[r,p]}))
            rows,skipped=a.load_records(Path(d),BYID)
            self.assertEqual(len(rows),0);self.assertEqual(len(skipped),2)
    def test_end_to_end_cli(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'logs';inp.mkdir();out=Path(d)/'result'
            rs=[fixture(c) for c in CASES[:4]]
            (inp/'record.json').write_text(json.dumps({'schema_version':'xbw.pilot.export/0.1','records':rs}))
            cp=subprocess.run([sys.executable,str(ROOT/'tools/analyze.py'),'--input',str(inp),'--out',str(out)],capture_output=True,text=True)
            self.assertEqual(cp.returncode,0,cp.stderr)
            self.assertTrue((out/'report.md').exists())
            s=json.loads((out/'summary.json').read_text())
            self.assertEqual(s['main_case_records'],4)
            self.assertEqual(s['distinguishing_clean_subset']['n'],4)
    def test_input_output_collision_prevented(self):
        with tempfile.TemporaryDirectory() as d:
            cp=subprocess.run([sys.executable,str(ROOT/'tools/analyze.py'),'--input',d,'--out',d],capture_output=True,text=True)
            self.assertNotEqual(cp.returncode,0)

if __name__=='__main__':unittest.main()
