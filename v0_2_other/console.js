/* Offline operator console. No network APIs, page control, or model calls. */
(function (root) {
  'use strict';
  function fill(text, values) {
    for (const [key, value] of Object.entries(values)) text = text.split('{{'+key+'}}').join(String(value));
    return text;
  }
  function parseObject(raw) {
    if (typeof raw !== 'string' || !raw.trim()) throw new Error('尚无回复');
    let text = raw.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim();
    try { const x = JSON.parse(text); if (!x || Array.isArray(x) || typeof x !== 'object') throw new Error('not object'); return x; }
    catch (_) {
      const start = text.indexOf('{'), end = text.lastIndexOf('}');
      if (start < 0 || end < start) throw new Error('没有可解析的 JSON 对象；请保留原文');
      try { const x = JSON.parse(text.slice(start, end+1)); if (!x || Array.isArray(x) || typeof x !== 'object') throw new Error('not object'); return x; }
      catch (_) { throw new Error('JSON 无法解析；不自动补造内容'); }
    }
  }
  function parseJudge(raw) {
    const x = parseObject(raw), p = x.p_informed_A;
    if (typeof p !== 'number' || !Number.isFinite(p) || p<0 || p>1) throw new Error('概率必须是 0–1 数值');
    if (!['A','B'].includes(x.pick)) throw new Error('pick 必须为 A 或 B');
    if ((p>0.5 && x.pick!=='A') || (p<0.5 && x.pick!=='B')) throw new Error('pick 与概率冲突；保留原文，记为不可评分');
    if (typeof x.insufficient_evidence !== 'boolean' || typeof x.reason !== 'string') throw new Error('缺少不足信息标记或理由');
    return x;
  }
  function parseChecks(raw, c) {
    const x=parseObject(raw);
    if (typeof x.explanation !== 'string' || !x.explanation.trim()) throw new Error('缺少 explanation');
    if (!x.checks || typeof x.checks!=='object' || Array.isArray(x.checks)) throw new Error('缺少 checks');
    for (const q of c.check_ids) if (!['PASS','FAIL'].includes(x.checks[q])) throw new Error('检查项 '+q+' 必须明确为 PASS/FAIL');
    return x;
  }
  function questionFor(record, round) {
    const override=(record.manual_questions||{})[String(round)];
    if (typeof override==='string' && override.trim()) return override.trim();
    const x=parseObject((record.raw||{})['judge_P'+(round-1)] || '');
    if (typeof x.question!=='string' || !x.question.trim()) throw new Error('上一轮裁判没有有效问题；只能手工提取原文已有问题');
    return x.question.trim();
  }
  function stepsFor(c) {
    const other=s=>s==='A'?'B':'A';
    const out=['opening_'+c.generation_first,'opening_'+other(c.generation_first),'judge_P0'];
    for (let n=1;n<=3;n++) {
      const first=c.round_response_first[n-1];
      out.push('answer_'+n+'_'+first,'answer_'+n+'_'+other(first),'judge_P'+n);
    }
    out.push('judge_'+c.fresh_arm_first, 'judge_'+(c.fresh_arm_first==='N'?'E':'N'));
    return out;
  }
  function requireRaw(record, key) {
    const raw=(record.raw||{})[key];
    if (typeof raw!=='string' || !raw.trim()) throw new Error('请先保存 '+key+' 的原始回复');
    return raw;
  }
  function transcript(c,record,full) {
    let out='<SPEAKER_A_OPENING>\n'+requireRaw(record,'opening_A')+'\n</SPEAKER_A_OPENING>\n\n<SPEAKER_B_OPENING>\n'+requireRaw(record,'opening_B')+'\n</SPEAKER_B_OPENING>';
    if (full) for(let n=1;n<=3;n++) out+='\n\n<ROUND_'+n+'>\nJUDGE QUESTION:\n'+questionFor(record,n)+'\n\nSPEAKER A:\n'+requireRaw(record,'answer_'+n+'_A')+'\n\nSPEAKER B:\n'+requireRaw(record,'answer_'+n+'_B')+'\n</ROUND_'+n+'>';
    return out;
  }
  function buildPrompt(data,c,record,key) {
    if (key.startsWith('opening_')) {
      const seat=key.slice(-1), checks={};for(const q of c.check_ids)checks[q]='PASS or FAIL';
      return fill(data.templates.speaker_open,{PUBLIC:c.public_text,SEAT:seat,PRIVATE:seat===c.informed_seat?c.private_text:'No complete reference card is supplied to you. You have only the public game card above.',CHECK_SCHEMA:JSON.stringify(checks,null,4)});
    }
    if(key.startsWith('answer_')) {
      const [,n,seat]=key.split('_');requireRaw(record,'opening_'+seat);
      return fill(data.templates.speaker_follow,{SEAT:seat,QUESTION:questionFor(record,Number(n))});
    }
    if(key==='judge_P0')return fill(data.templates.judge_base,{PUBLIC:c.public_text,STAGE_INSTRUCTION:data.stage_initial,TRANSCRIPT:transcript(c,record,false),OBSERVATIONS:'No independent observations are supplied.'});
    if(/^judge_P[123]$/.test(key)) {
      const n=Number(key.slice(-1));
      return fill(data.templates.judge_follow,{ROUND:n,QUESTION:questionFor(record,n),ANSWER_A:requireRaw(record,'answer_'+n+'_A'),ANSWER_B:requireRaw(record,'answer_'+n+'_B'),STAGE_INSTRUCTION:n===3?data.stage_last:data.stage_mid});
    }
    if(key==='judge_N' || key==='judge_E') {
      requireRaw(record,'judge_P3');
      let obs='No independent observations are supplied in this adjudication. The speakers\' check values remain unverified claims.';
      if(key==='judge_E')obs='These are independently verified host observations, fixed before either speaker responded. They do not directly label a speaker.\n'+c.check_ids.map(q=>q+': '+c.gold[q]).join('\n')+'\nCompare these with the original frozen check commitments, not a later revision. Do not assume every speaker executed its instructions perfectly.';
      return fill(data.templates.judge_base,{PUBLIC:c.public_text,STAGE_INSTRUCTION:data.stage_fresh,TRANSCRIPT:transcript(c,record,true),OBSERVATIONS:obs});
    }
    throw new Error('未知步骤 '+key);
  }
  function diagnostic(c,record) {
    try {
      const a=parseChecks(requireRaw(record,'opening_A'),c),b=parseChecks(requireRaw(record,'opening_B'),c);
      const match=x=>c.check_ids.every(q=>x.checks[q]===c.gold[q]);
      const ka=c.informed_seat==='A'?match(a):match(b),bb=c.informed_seat==='A'?match(b):match(a);
      return {status:!ka?'knower_commitment_error':bb?'collision':'distinguishing',informed_seat:c.informed_seat,A_matches:match(a),B_matches:match(b),verified:Object.fromEntries(c.check_ids.map(q=>[q,c.gold[q]]))};
    }catch(e){return {status:'unscorable',error:e.message};}
  }
  const Core={fill,parseObject,parseJudge,parseChecks,questionFor,stepsFor,buildPrompt,diagnostic,transcript};
  if(typeof module!=='undefined' && module.exports)module.exports=Core;
  root.XBWCore=Core;
  if(typeof document==='undefined' || !root.PILOT_DATA)return;
  const D=root.PILOT_DATA, key='xbw_offline_v0_1', $=id=>document.getElementById(id);
  let storage={records:{},models:{M1:'',M2:''},current:'D01'}, currentStep=0;
  try { const saved=localStorage.getItem(key);if(saved){const x=JSON.parse(saved);if(x && x.records)storage=x;} } catch(e){$('storageNotice').textContent='浏览器本地保存不可用；务必导出 JSON。';}
  function currentCase(){return D.cases.find(c=>c.case_id===storage.current)||D.cases[0];}
  function save(){try{localStorage.setItem(key,JSON.stringify(storage));$('storageNotice').textContent='本地自动保存已尝试；每题仍应导出备份。';}catch(e){$('storageNotice').textContent='本地自动保存失败；请立即导出。';}}
  function makeRecord(c){const m1=storage.models.M1,m2=storage.models.M2;return {schema_version:'xbw.pilot.record/0.1',protocol_version:D.version,case_id:c.case_id,run_id:c.case_id+'-'+Date.now(),case_sha256:c.case_sha256,status:'not_started',demo:false,metadata:{speaker_model:c.config==='R1'?m1:m2,judge_model:c.config==='R1'?m2:m1,platform:'Arena',mode:'Direct',effort:'unknown',temperature:'unknown',tools_status:'not_verified',started_utc:new Date().toISOString(),ended_utc:''},raw:{},manual_questions:{},issue_flags:[],notes:'',sent_prompts:{},events:[]};}
  function record(){const c=currentCase();if(!storage.records[c.case_id])storage.records[c.case_id]=makeRecord(c);return storage.records[c.case_id];}
  function touch(){const r=record();r.updated_utc=new Date().toISOString();if(r.status==='not_started')r.status='in_progress';save();}
  const issueNames={private_leak:'暴露角色/私有卡片来源',model_identity_leak:'发言泄漏模型身份',cross_speaker_leak:'speaker 见到了另一会话',tool_use_observed:'观察到搜索/工具',unexpected_model_change:'中途模型变化',question_protocol_breach:'提问越界/多问',speaker_refusal:'speaker 拒答',judge_refusal:'judge 拒答',format_problem:'格式问题',technical_retry:'技术重试',other:'其他偏离'};
  function label(k){if(k.startsWith('opening_'))return '解释者 '+k.slice(-1)+' · 开场（新会话）';if(k.startsWith('answer_')){const a=k.split('_');return '第 '+a[1]+' 问 → 解释者 '+a[2];}if(k==='judge_P0')return 'P0 · 被动判断 + 第 1 问（新裁判）';if(k==='judge_P1'||k==='judge_P2')return k.slice(6)+' · 更新 + 下一问';if(k==='judge_P3')return 'P3 · 三轮后的判断';return k==='judge_N'?'N · 全新裁判 / 无独立证据':'E · 全新裁判 / 加核验证据';}
  function target(k){const r=record();if(k.startsWith('opening_')||k.startsWith('answer_'))return '发给 speaker '+k.slice(-1)+'：'+(r.metadata.speaker_model||'尚未填写模型');return '发给 '+(k==='judge_N'?'全新的 N 裁判':k==='judge_E'?'全新的 E 裁判':k==='judge_P0'?'新的交互裁判':'原交互裁判')+'：'+(r.metadata.judge_model||'尚未填写模型');}
  function wordCount(s){return s.trim()?s.trim().split(/\s+/).length:0;}
  function validateCurrent(){const c=currentCase(),r=record(),k=stepsFor(c)[currentStep],raw=r.raw[k]||'';if(!raw.trim()){$('parseStatus').textContent='尚未保存此步回复。';return;}
    try {let msg;if(k.startsWith('judge_')){const x=parseJudge(raw);msg='可评分：P(A)='+x.p_informed_A+'；选择 '+x.pick+'；信息不足='+x.insufficient_evidence;if(['judge_P0','judge_P1','judge_P2'].includes(k)&&!(typeof x.question==='string'&&x.question.trim()))msg+='。注意：缺少下一问';if(wordCount(x.reason)>50)msg+='。理由超过 50 词（记录，不裁剪）';}
      else if(k.startsWith('opening_')){const x=parseChecks(raw,c),n=wordCount(x.explanation);msg='检查字段可解析；解释 '+n+' 词'+(n<100||n>140?'（超出约定范围；保留）':'');}
      else{const x=parseObject(raw);if(typeof x.answer!=='string')throw new Error('缺少 answer');const n=wordCount(x.answer);msg='答复可解析；'+n+' 词'+(n<60||n>100?'（超出约定范围；保留）':'');}
      $('parseStatus').textContent=msg;
    } catch(e){$('parseStatus').textContent='⚠ '+e.message;}
  }
  function renderNav(){const c=currentCase(),r=record(),steps=stepsFor(c);$('stepList').replaceChildren();steps.forEach((k,i)=>{const b=document.createElement('button');b.className='step '+(i===currentStep?'active ':'')+(r.raw[k]&&r.raw[k].trim()?'done':'');b.textContent=(r.raw[k]&&r.raw[k].trim()?'✓ ':'')+(i+1)+'. '+label(k);b.onclick=()=>{currentStep=i;renderStep();renderNav();};$('stepList').appendChild(b);});$('progress').textContent=steps.filter(k=>(r.raw[k]||'').trim()).length+' / '+steps.length+' 步已记录';}
  function renderStep(){const c=currentCase(),r=record(),steps=stepsFor(c),k=steps[currentStep];$('stepTitle').textContent=label(k);$('target').textContent=target(k);$('rawReply').value=r.raw[k]||'';$('stepKey').textContent=k;
    try{$('prompt').value=buildPrompt(D,c,r,k);$('copyPrompt').disabled=false;}catch(e){$('prompt').value='尚不能生成：'+e.message;$('copyPrompt').disabled=true;}
    $('prev').disabled=currentStep===0;$('next').disabled=currentStep===steps.length-1;
    const n=k.startsWith('answer_')?Number(k.split('_')[1]):/^judge_P[123]$/.test(k)?Number(k.slice(-1)):0;
    $('manualWrap').hidden=!n;$('manualQuestion').value=n?((r.manual_questions||{})[String(n)]||''):'';$('manualQuestion').dataset.round=n;
    validateCurrent();
  }
  function render(){const c=currentCase(),r=record();$('caseSelect').value=c.case_id;$('caseTitle').textContent=c.case_id+' · '+c.term;$('configInfo').textContent=(c.split==='practice'?'练习题 · 不计入统计':'正式题')+' | '+c.config+' | '+(c.config==='R1'?'M1 speakers → M2 judges':'M2 speakers → M1 judges');
    $('speakerModel').value=r.metadata.speaker_model||'';$('judgeModel').value=r.metadata.judge_model||'';$('mode').value=r.metadata.mode||'Direct';$('effort').value=r.metadata.effort||'unknown';$('toolsStatus').value=r.metadata.tools_status||'not_verified';$('notes').value=r.notes||'';$('runStatus').value=r.status;$('publicCard').textContent=c.public_text;$('hostDiagnostic').textContent='未展开；建议全部结束后再查看。';
    $('flags').replaceChildren();for(const [flag,name]of Object.entries(issueNames)){const lab=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=(r.issue_flags||[]).includes(flag);input.onchange=()=>{const s=new Set(record().issue_flags||[]);input.checked?s.add(flag):s.delete(flag);record().issue_flags=[...s];touch();};lab.append(input,document.createTextNode(name));$('flags').append(lab);}
    renderNav();renderStep();save();
  }
  function download(name,value){const b=new Blob([JSON.stringify(value,null,2)],{type:'application/json;charset=utf-8'}),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);}
  const select=$('caseSelect');for(const c of [...D.cases.filter(c=>c.split==='practice'),...D.cases.filter(c=>c.split==='main')]){const o=document.createElement('option');o.value=c.case_id;o.textContent=c.case_id+' · '+c.term;select.append(o);}select.onchange=()=>{storage.current=select.value;currentStep=0;render();};
  $('model1').value=storage.models.M1||'';$('model2').value=storage.models.M2||'';
  $('applyModels').onclick=()=>{storage.models.M1=$('model1').value.trim();storage.models.M2=$('model2').value.trim();const r=record(),c=currentCase();r.metadata.speaker_model=c.config==='R1'?storage.models.M1:storage.models.M2;r.metadata.judge_model=c.config==='R1'?storage.models.M2:storage.models.M1;r.events.push({at:new Date().toISOString(),type:'model_metadata_set'});touch();render();};
  for(const [id,prop]of [['speakerModel','speaker_model'],['judgeModel','judge_model'],['mode','mode'],['effort','effort'],['toolsStatus','tools_status']])$(id).onchange=()=>{record().metadata[prop]=$(id).value;if(prop==='tools_status'&&$(id).value==='tool_use_observed'&&!record().issue_flags.includes('tool_use_observed'))record().issue_flags.push('tool_use_observed');touch();render();};
  $('rawReply').addEventListener('input',()=>{const k=stepsFor(currentCase())[currentStep],r=record(),previous=r.raw[k]||'',next=$('rawReply').value;if(previous!==next){r.events.push({at:new Date().toISOString(),type:previous?'raw_response_replaced':'raw_response_recorded',step:k,before:previous,after:next});}r.raw[k]=next;touch();validateCurrent();renderNav();});
  $('notes').oninput=()=>{record().notes=$('notes').value;touch();};
  $('runStatus').onchange=()=>{record().status=$('runStatus').value;if(record().status==='completed'||record().status==='aborted')record().metadata.ended_utc=new Date().toISOString();save();};
  $('manualQuestion').onchange=()=>{const n=$('manualQuestion').dataset.round;if(n){record().manual_questions[n]=$('manualQuestion').value;record().events.push({at:new Date().toISOString(),type:'verbatim_question_override',round:Number(n),text:$('manualQuestion').value});if(!record().issue_flags.includes('format_problem'))record().issue_flags.push('format_problem');touch();renderStep();}};
  $('prev').onclick=()=>{currentStep--;renderStep();renderNav();};$('next').onclick=()=>{currentStep++;renderStep();renderNav();};
  $('copyPrompt').onclick=async()=>{const c=currentCase(),r=record(),k=stepsFor(c)[currentStep];try{const text=buildPrompt(D,c,r,k);$('prompt').value=text;let copied=false;try{await navigator.clipboard.writeText(text);copied=true;}catch(_){$('prompt').focus();$('prompt').select();try{copied=document.execCommand('copy');}catch(_){}}
      const event={at:new Date().toISOString(),type:'prompt_prepared_for_manual_send',step:k,text};r.events.push(event);r.sent_prompts[k]=text;touch();$('copyNotice').textContent=copied?'已复制并本地记录。请亲自粘贴到指定会话发送。':'文本已选中并记录；请 Ctrl+C，然后亲自发送。';
    }catch(e){$('copyNotice').textContent=e.message;}};
  $('exportOne').onclick=()=>download(record().run_id+'.json',record());
  $('exportAll').onclick=()=>download('xbw-pilot-export-'+new Date().toISOString().slice(0,10)+'.json',{schema_version:'xbw.pilot.export/0.1',exported_utc:new Date().toISOString(),records:Object.values(storage.records)});
  $('importFile').onchange=async e=>{try{const file=e.target.files[0];if(!file)return;const x=JSON.parse(await file.text()),rs=x.schema_version==='xbw.pilot.export/0.1'?x.records:[x];if(!Array.isArray(rs))throw new Error('记录格式不正确');for(const r of rs){const c=D.cases.find(z=>z.case_id===r.case_id);if(!c||r.schema_version!=='xbw.pilot.record/0.1'||r.case_sha256!==c.case_sha256)throw new Error('题目/版本校验失败：'+r.case_id);if(!r.raw||!r.metadata)throw new Error('缺失 raw/metadata');}
      if(!confirm('将导入 '+rs.length+' 条记录。若本地已有同题记录，将被覆盖；请先导出备份。'))return;
      for(const r of rs)storage.records[r.case_id]=r;storage.current=rs[0].case_id;currentStep=0;save();render();$('copyNotice').textContent='导入完成。';
    }catch(err){alert('导入失败：'+err.message);}finally{e.target.value='';}};
  $('showHost').onclick=()=>{$('hostDiagnostic').textContent=JSON.stringify(diagnostic(currentCase(),record()),null,2);};
  if(!D.cases.some(c=>c.case_id===storage.current))storage.current='D01';render();
})(typeof globalThis!=='undefined'?globalThis:this);
