/* One UI step per call; no background timer, model substitution or CAPTCHA action. */
export default async function step(host, browser, tabs, fs) {
  const urls = {
    'claude-sonnet-5-high': 'https://arena.ai/text/direct?model_a=claude-sonnet-5-high',
    'gemini-3.1-pro-preview': 'https://arena.ai/text/direct?model_a=gemini-3.1-pro-preview'
  };
  if (Object.values(host.records).some(r => r.status === 'blocked_rate_limit')) return {state:'STOP_RATE_LIMIT'};
  for (const key of Object.keys(host.pending)) {
    const p = host.pending[key];
    const dom = await p.tab.playwright.domSnapshot();
    if (dom.includes('dialog "Security Verification"')) return {state:'human_verification',key,tab_id:p.tab.id};
    const result = await host.capture(key);
    if (result.state === 'anonymous_comparison') {
      await fs.writeFile(host.run+'/'+key+'_comparison_private.txt',result.dom);
      for (const name of ['跳过','Skip']) {
        if (await p.tab.playwright.getByRole('button',{name,exact:true}).count()) {
          host.records[p.id].events.push({type:'anonymous_comparison_skipped',at:new Date().toISOString()});
          await p.tab.playwright.getByRole('button',{name,exact:true}).click();
          return {state:'comparison_skipped',key};
        }
      }
    }
    return {state:result.state,key,decision:p.role==='J'?result.reply:undefined};
  }
  const latest = Math.max(0,...Object.values(host.records).flatMap(r=>r.messages.flatMap(m=>[Date.parse(m.sent_utc)||0,...(m.retry_sends||[]).map(s=>Date.parse(s.sent_utc)||0)])));
  if (Date.now()-latest<30000) return {state:'WAIT_PACING',seconds:Math.ceil((30000-Date.now()+latest)/1000)};
  const ended = ['completed','protocol_failure','blocked_platform','blocked_rate_limit','invalid_host_resend'];
  const id = host.bundle.trajectories.map(t=>t.id).find(id=>!ended.includes(host.records[id].status));
  if (!id) return {state:'ALL_ATTEMPTED'};
  const r = host.records[id], last = r.messages.filter(m=>m.role==='J'&&m.reply).at(-1);
  let needed;
  if (!last) {
    needed = ['A','B'].filter(role=>!r.messages.some(m=>m.role===role&&m.reply));
  } else {
    needed = (last.parsed.target==='BOTH'?['A','B']:[last.parsed.target]).filter(role=>!r.messages.some(m=>m.role===role&&m.reply&&m.question_index===last.question_index));
  }
  const role = needed[0] || 'J', key = id+'_'+role;
  const model = role==='J'?r.judge_model:r.speaker_model;
  let tab = tabs[key];
  if (!tab) {
    tab = await browser.tabs.new(); tabs[key]=tab;
    const previous = r.messages.filter(m=>m.role===role&&m.reply).at(-1);
    await tab.goto(previous?.url || urls[model]);
    await tab.markHandoff();
    return {state:previous?'restoring_original_tab':'tab_opened',id,role};
  }
  const dom = await tab.playwright.domSnapshot();
  if (!dom.includes('paragraph: Direct') || !dom.includes(model)) return {state:'awaiting_identity',id,role};
  return host.send(id,role,tab);
}
