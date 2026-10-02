/* Mechanical fixtures: no actual model outputs. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..'),D=JSON.parse(fs.readFileSync(path.join(root,'data/HOST_ONLY/console_bundle.json'),'utf8'));
const C=require(path.join(root,'tools/console.js'));
let checks=0;
for(const c of D.cases){
 const r={raw:{},manual_questions:{}};
 const k=c.informed_seat,b=k==='A'?'B':'A';
 for(const s of ['A','B']){
  const p=C.buildPrompt(D,c,r,'opening_'+s);
  assert.strictEqual(p.includes(c.private_text),s===k);checks++;
  const ready=fs.readFileSync(path.join(root,'prompts/ready',c.case_id,'SPEAKER_'+s+'_OPEN.txt'),'utf8').trim();
  assert.strictEqual(p.trim(),ready);checks++;
  const cs=Object.fromEntries(c.check_ids.map(q=>[q,c.gold[q]]));if(s===b)cs[c.check_ids[0]]=cs[c.check_ids[0]]==='PASS'?'FAIL':'PASS';
  r.raw['opening_'+s]=JSON.stringify({explanation:'MECHANICAL FIXTURE.',checks:cs});
 }
 let p=C.buildPrompt(D,c,r,'judge_P0');assert(!p.includes(c.private_text));checks++;
 for(let n=0;n<=3;n++){
  r.raw['judge_P'+n]=JSON.stringify({p_informed_A:.5,pick:'A',insufficient_evidence:true,reason:'OLD_JUDGE_VERDICT_MUST_NOT_LEAK',question:n<3?'Discuss Q'+(n+1)+'.':null});
  if(n<3)for(const s of ['A','B']){const f=C.buildPrompt(D,c,r,'answer_'+(n+1)+'_'+s);assert(!f.includes('OLD_JUDGE_VERDICT_MUST_NOT_LEAK'));checks++;r.raw['answer_'+(n+1)+'_'+s]=JSON.stringify({answer:'FIXTURE answer.'});}
  if(n>0){p=C.buildPrompt(D,c,r,'judge_P'+n);assert(!p.includes(c.private_text));checks++;}
 }
 const n=C.buildPrompt(D,c,r,'judge_N'),e=C.buildPrompt(D,c,r,'judge_E');
 assert(!n.includes('OLD_JUDGE_VERDICT_MUST_NOT_LEAK'));checks++;
 assert(!e.includes('OLD_JUDGE_VERDICT_MUST_NOT_LEAK'));checks++;
 assert(!n.includes(c.private_text));checks++;
 assert(!e.includes(c.private_text));checks++;
 assert(e.includes('independently verified host observations'));checks++;
 assert(!n.includes('independently verified host observations'));checks++;
 assert.strictEqual(C.stepsFor(c).length,14);checks++;
 assert.strictEqual(C.diagnostic(c,r).status,'distinguishing');checks++;
 assert(n.split('DIALOGUE RECORD\n')[1].split('\n\nINDEPENDENT OBSERVATIONS')[0]===e.split('DIALOGUE RECORD\n')[1].split('\n\nINDEPENDENT OBSERVATIONS')[0]);checks++;
}
assert.throws(()=>C.parseJudge('{"p_informed_A":0.2,"pick":"A","insufficient_evidence":true,"reason":"bad"}'));checks++;
assert.throws(()=>C.parseJudge('{"p_informed_A":true,"pick":"A","insufficient_evidence":true,"reason":"bad"}'));checks++;
const c=D.cases[0];assert.throws(()=>C.buildPrompt(D,c,{raw:{},manual_questions:{}},'judge_E'));checks++;
console.log('PASS: '+checks+' frontend assertions across '+D.cases.length+' cases. No live model calls.');
