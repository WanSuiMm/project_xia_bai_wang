/* Loaded only inside cua_repl. All UI interaction uses its documented tab API. */
module.exports = async function operator(fs, root, Core) {
  const run = root+'/runs/arena_20261002_other_pairs01';
  const data = JSON.parse(await fs.readFile(root+'/bundle.json','utf8'));
  const state = {data, records:{}, pending:{}, tabs:{}, run};
  const caseFor = id => data.cases.find(c=>c.case_id===id);
  const write = async id => fs.writeFile(run+'/logs/'+id+'.json',JSON.stringify(state.records[id],null,2)+'\n');
  for (const c of data.cases) state.records[c.case_id]=JSON.parse(await fs.readFile(run+'/logs/'+c.case_id+'.json','utf8'));
  state.attach = function(id,key,tab) {
    const r=state.records[id];
    const sameConversation = k => key.startsWith('judge_') ? /^judge_P[0-3]$/.test(k) : !k.startsWith('judge_') && k.endsWith('_'+key.slice(-1));
    state.pending[id] ||= {};
    state.pending[id][key]={tab,prompt:r.sent_prompts[key],model:key.startsWith('judge_')?'gemini-3.8-flash-high':'claude-sonnet-5-5-high',likes:Object.keys(r.raw).filter(sameConversation).length};
  };
  state.send = async function(id,key,tab) {
    const c=caseFor(id),r=state.records[id],next=Core.stepsFor(c).find(k=>!r.raw[k]);
    if(key!==next && !['judge_N','judge_E'].includes(key))throw Error('Unexpected step '+next);
    if(r.raw[key])throw Error('Already captured');
    await tab.getAXState({emit:false});
    const dom=await tab.playwright.domSnapshot(), model=key.startsWith('judge_')?'gemini-3.8-flash-high':'claude-sonnet-5-5-high';
    if(!dom.includes('paragraph: Direct')||!dom.includes(model))throw Error('Model/mode mismatch');
    const prompt=Core.buildPrompt(data,c,r,key);
    if(r.sent_prompts[key] && r.sent_prompts[key]!==prompt)throw Error('Changed receipt');
    r.sent_prompts[key]=prompt;r.status='in_progress';
    r.events.push({at:new Date().toISOString(),type:'ui_send_attempt',step:key});await write(id);
    const likes=await tab.playwright.getByRole('button',{name:'Like this response',exact:true}).count();
    await tab.playwright.getByRole('textbox',{name:/Ask (anything|followup)/}).fill(prompt);
    await tab.playwright.getByRole('button',{name:'Send message',exact:true}).click();
    await tab.getAXState({emit:false});
    state.pending[id] ||= {};state.pending[id][key]={tab,prompt,model,likes};
    r.pending_sessions ||= {};r.pending_sessions[key]={tab_id:tab.id,url:await tab.url(),model,prompt};
    r.events.push({at:new Date().toISOString(),type:'sent_session_receipt',step:key,url:await tab.url()});await write(id);
    return {sent:id+'/'+key};
  };
  state.capture = async function(id,key) {
    const r=state.records[id],c=caseFor(id),p=state.pending[id]?.[key];if(!p)throw Error('Not attached');
    const t=p.tab;await t.getAXState({emit:false});const dom=await t.playwright.domSnapshot();
    if(dom.includes('Which response do you prefer?')) {
      r.platform_observations.push({at:new Date().toISOString(),step:key,type:'anonymous_comparison',dom});await write(id);
      if(await t.playwright.getByRole('button',{name:'跳过',exact:true}).count()) {
        await t.playwright.getByRole('button',{name:'跳过',exact:true}).click();await t.getAXState({emit:false});return {case:id,step:key,state:'anonymous_skipped'};
      }
      return {case:id,step:key,state:'anonymous_blocked'};
    }
    if(dom.includes('Something went wrong')||dom.includes('Session not found')) {
      r.status='blocked_platform_generation';r.events.push({at:new Date().toISOString(),type:'no_output_platform_error',step:key,dom});await write(id);return {case:id,step:key,state:'error'};
    }
    const likes=await t.playwright.getByRole('button',{name:'Like this response',exact:true}).count();
    const codes=await t.playwright.locator('code').count();
    const texts=await t.playwright.locator('code, p').allTextContents();
    const field=key.startsWith('judge_')?'p_informed_A':key.startsWith('opening_')?'explanation':'answer';
    const raw=texts.find(x=>x.trim().startsWith('{')&&x.includes('"'+field+'"'));
    const unseenReply=raw && !Object.values(r.raw).includes(raw);
    const completed=likes>p.likes || (key.startsWith('judge_') && codes>p.likes) || unseenReply;
    if(dom.includes('paragraph: Generating...')||!completed)return {case:id,step:key,state:'pending'};
    if(!dom.includes('paragraph: Direct')||!dom.includes(p.model))throw Error('Unknown model/mode');
    if(!raw) {
      r.events.push({at:new Date().toISOString(),type:'render_without_expected_json',step:key,dom});await write(id);
      return {case:id,step:key,state:'no_expected_json'};
    }
    const parsed=key.startsWith('judge_')?Core.parseJudge(raw):key.startsWith('opening_')?Core.parseChecks(raw,c):Core.parseObject(raw);
    r.raw[key]=raw;r.captures[key]={prompt:p.prompt,raw,dom,url:await t.url(),visible_model:p.model,saved_utc:new Date().toISOString()};
    r.events.push({at:new Date().toISOString(),type:'ui_capture_saved',step:key});
    r.status=Core.stepsFor(c).every(k=>r.raw[k])?'completed':'in_progress';
    delete r.pending_sessions?.[key];delete state.pending[id][key];await write(id);
    return {case:id,step:key,state:'saved',reply:parsed};
  };
  state.note = async function(id,event,status) {
    state.records[id].events.push({at:new Date().toISOString(),...event});if(status)state.records[id].status=status;await write(id);
  };
  state.status = async function(status='in_progress') {
    await fs.writeFile(run+'/status.json',JSON.stringify({status,planned_game_replies:112,completed_game_replies:Object.values(state.records).reduce((n,r)=>n+Object.keys(r.raw).length,0),cases:Object.fromEntries(Object.entries(state.records).map(([id,r])=>[id,{status:r.status,replies:Object.keys(r.raw).length,pending:Object.keys(r.pending_sessions||{})}])),updated_utc:new Date().toISOString(),automatic_monitor:false},null,2)+'\n');
  };
  return state;
};
