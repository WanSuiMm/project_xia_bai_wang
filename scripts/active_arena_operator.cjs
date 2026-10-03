/* Load inside cua_repl only; all browser operations use supplied CUA tabs. */
module.exports=async function(fs,root,C){
 const run=root+'/runs/arena_20261003_active01',b=JSON.parse(await fs.readFile(root+'/bundle.json','utf8'));
 const S={b,run,cases:{},trajectories:{},pending:{},tabs:{}};
 const getc=id=>b.cases.find(c=>c.case_id===id),key=(id,j)=>id+'_'+j;
 const saveCase=id=>fs.writeFile(run+'/logs/'+id+'.json',JSON.stringify(S.cases[id],null,2)+'\n');
 const saveTraj=k=>fs.writeFile(run+'/trajectories/'+k+'.json',JSON.stringify(S.trajectories[k],null,2)+'\n');
 for(const c of b.cases){S.cases[c.case_id]=JSON.parse(await fs.readFile(run+'/logs/'+c.case_id+'.json','utf8'));for(let j=1;j<=3;j++)S.trajectories[key(c.case_id,'J'+j)]=JSON.parse(await fs.readFile(run+'/trajectories/'+key(c.case_id,'J'+j)+'.json','utf8'));}
 const sendUI=async(t,prompt,model)=>{
  await t.getAXState({emit:false});const dom=await t.playwright.domSnapshot();
  if(!dom.includes('paragraph: Direct')||!dom.includes(model))throw Error('Mode/model mismatch');
  await t.playwright.getByRole('textbox',{name:/Ask (anything|followup)/}).fill(prompt);
  await t.playwright.getByRole('button',{name:'Send message',exact:true}).click();await t.getAXState({emit:false});
 };
 S.sendSpeaker=async(id,seat,tab)=>{
  const r=S.cases[id],c=getc(id);if(r.raw[seat]||r.sessions?.[seat]||S.pending[id+'_'+seat])throw Error('Speaker already sent');
  const prompt=C.speakerPrompt(b,c,seat);r.sent_prompts[seat]=prompt;r.status='generating';r.events.push({at:new Date().toISOString(),type:'speaker_send_receipt',seat});await saveCase(id);
  await sendUI(tab,prompt,b.speaker_model);r.sessions||={};r.sessions[seat]={url:await tab.url(),tab_id:tab.id,sent_utc:new Date().toISOString()};await saveCase(id);
  S.pending[id+'_'+seat]={tab,prompt,model:b.speaker_model,id,seat,kind:'speaker'};return {sent:id+'_'+seat};
 };
 S.sendJudge=async(id,j,tab)=>{
  const k=key(id,j),t=S.trajectories[k],r=S.cases[id],c=getc(id);if(t.pending?.url)throw Error('Judge awaiting output');
  if(t.decisions.length&&C.parse(t.decisions.at(-1).raw).action!=='VERIFY')throw Error('Terminal decision already captured');
  const prompt=t.decisions.length?C.judgeFollow(b,c,t,t.observations.at(-1)):C.judgeInitial(b,c,r);
  t.pending={prompt,index:t.decisions.length,sent_utc:new Date().toISOString()};t.status='generating';t.events.push({at:new Date().toISOString(),type:'judge_send_receipt',index:t.decisions.length});await saveTraj(k);
  await sendUI(tab,prompt,b.judge_model);t.pending.url=await tab.url();t.pending.tab_id=tab.id;await saveTraj(k);
  S.pending[k]={tab,prompt,model:b.judge_model,id,j,kind:'judge'};S.tabs[k]=tab;return {sent:k,index:t.decisions.length};
 };
 S.capture=async(k)=>{
  const p=S.pending[k];if(!p)throw Error('No pending receipt '+k);const tab=p.tab;
  await tab.getAXState({emit:false});const dom=await tab.playwright.domSnapshot();
  const r=p.kind==='speaker'?S.cases[p.id]:S.trajectories[k],save=()=>p.kind==='speaker'?saveCase(p.id):saveTraj(k);
  if(dom.includes('Which response do you prefer?')){
   r.events.push({at:new Date().toISOString(),type:'anonymous_comparison',step:p.kind==='speaker'?p.seat:r.decisions.length});await fs.writeFile(run+'/'+k+'_comparison_private.txt',dom);await save();
   if(await tab.playwright.getByRole('button',{name:'跳过',exact:true}).count()){await tab.playwright.getByRole('button',{name:'跳过',exact:true}).click();await tab.getAXState({emit:false});return {key:k,state:'skipped'};}return {key:k,state:'comparison_pending'};
  }
  if(dom.includes('Something went wrong')||dom.includes('Session not found')){
   r.status='blocked_platform';r.events.push({at:new Date().toISOString(),type:'platform_error',step:p.kind==='speaker'?p.seat:r.decisions.length});await fs.writeFile(run+'/'+k+'_error_private.txt',dom);await save();delete S.pending[k];return {key:k,state:'error'};
  }
  if(dom.includes('Generating...')||await tab.playwright.getByRole('button',{name:'Stop generation',exact:true}).count())return {key:k,state:'pending'};
  const field=p.kind==='speaker'?'explanation':'p_informed_A';const raw=(await tab.playwright.locator('code, p').allTextContents()).find(x=>x.trim().startsWith('{')&&x.includes('"'+field+'"'));
  if(!raw)return {key:k,state:'no_reply'};
  if(p.kind==='judge'&&r.decisions.some(d=>d.raw===raw))return {key:k,state:'pending_old_reply'};
  if(!dom.includes('paragraph: Direct')||!dom.includes(p.model))throw Error('Unresolved model');
  const cap={raw,prompt:p.prompt,visible_model:p.model,url:await tab.url(),saved_utc:new Date().toISOString(),dom};
  if(p.kind==='speaker'){
   r.raw[p.seat]=raw;r.captures[p.seat]=cap;
   try{C.parseSpeaker(raw,getc(p.id));r.status=r.raw.A&&r.raw.B?'speakers_frozen':'partial_speakers';if(r.status==='speakers_frozen'){r.diagnostic=C.diagnostic(getc(p.id),r);r.frozen_utc=new Date().toISOString();}}
   catch(e){r.status='invalid_speaker';r.events.push({at:new Date().toISOString(),type:'schema_failure',detail:e.message});}
  }else{
   let x;try{x=C.parseDecision(raw,getc(p.id),r);}catch(e){r.invalid_decision=cap;r.status='invalid_decision';r.events.push({at:new Date().toISOString(),type:'schema_failure',detail:e.message});delete r.pending;await save();delete S.pending[k];return {key:k,state:'invalid_decision'};}
   r.decisions.push(cap);delete r.pending;
   if(x.action==='VERIFY'){r.observations.push({...C.observation(getc(p.id),S.cases[p.id],x.query_id),revealed_utc:new Date().toISOString()});r.status='awaiting_update';}
   else{r.status='completed';r.ended_utc=new Date().toISOString();}
  }
  r.events.push({at:new Date().toISOString(),type:'capture_saved',step:p.kind==='speaker'?p.seat:r.decisions.length-1});await save();delete S.pending[k];
  return {key:k,state:r.status,reply:C.parse(raw),diagnostic:p.kind==='speaker'?r.diagnostic:undefined};
 };
 S.reload=async(k)=>{const p=S.pending[k],r=p.kind==='speaker'?S.cases[p.id]:S.trajectories[k];r.events.push({at:new Date().toISOString(),type:'single_no_output_reload'});await(p.kind==='speaker'?saveCase(p.id):saveTraj(k));await p.tab.reload();await p.tab.getAXState({emit:false});};
 S.timeout=async(k)=>{const p=S.pending[k],r=p.kind==='speaker'?S.cases[p.id]:S.trajectories[k];r.status='blocked_no_output_timeout';r.events.push({at:new Date().toISOString(),type:'timeout_cutoff'});await(p.kind==='speaker'?saveCase(p.id):saveTraj(k));delete S.pending[k];};
 S.status=async(status='in_progress')=>{await fs.writeFile(run+'/status.json',JSON.stringify({status,planned_cases:6,planned_trajectories:18,speaker_replies:Object.values(S.cases).reduce((n,r)=>n+Object.keys(r.raw).length,0),completed_trajectories:Object.values(S.trajectories).filter(t=>t.status==='completed').length,verifications:Object.values(S.trajectories).reduce((n,t)=>n+t.observations.length,0),cases:Object.fromEntries(Object.entries(S.cases).map(([k,r])=>[k,r.status])),trajectories:Object.fromEntries(Object.entries(S.trajectories).map(([k,t])=>[k,{status:t.status,decisions:t.decisions.length,verifications:t.observations.length}])),pending:Object.keys(S.pending),automatic_monitor:false,updated_utc:new Date().toISOString()},null,2)+'\n');};
 return S;
};
