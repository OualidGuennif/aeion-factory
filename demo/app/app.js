/* Spec: knowledge/components/operator-cockpit.md */
const $ = (id) => document.getElementById(id);
let refreshing = false;
let busy = false, evidence = 'real', runsPage = 1, checkpointsPage = 1, cachedRuns = [], cachedRows = [], signature = '', fleetSignature = '', catalog = {}, recommendations = {}, campaigns = [];
const RUNS_PER_PAGE = 5;
const TIERS = {'flue-just-bash': '1 · triage', 'flue-local': '2 · assistant', 'flue-openshell': '3 · OpenShell'};
const LANGFUSE = 'http://localhost:3300';
const pretty = (n) => Number(n ?? 0).toLocaleString('en-US');
const money = (n) => n == null ? '—' : '$' + Number(n).toFixed(5);
const seconds = (n) => n == null ? '—' : (n / 1000).toFixed(1) + 's';
const label = (name) => Object.values(catalog.profiles??{}).find(p=>p.model===name)?.name ?? (name==='synthetic-replay'?'Synthetic replay':name??'Unknown model');
const taskInfo = (id) => catalog.scenarios?.[id] ?? catalog.triage?.[id];
const checkTotal = (r) => r.check?.total ?? taskInfo(r.task_id ?? 'pricing-js-v1')?.checks ?? '—';
function el(tag, text = '', cls = '') { const e = document.createElement(tag); e.textContent = text; e.className = cls; return e; }
function switchLabTab(tabName) {
  if (!tabName) return;
  document.querySelectorAll('[data-lab-tab]').forEach((btn) => {
    const active = btn.dataset.labTab === tabName;
    btn.classList.toggle('is-active', active);
    btn.setAttribute('aria-pressed', String(active));
  });
  document.querySelectorAll('[data-lab-panel]').forEach((panel) => {
    panel.hidden = panel.dataset.labPanel !== tabName;
  });
}
function selected(r) { return r.synthetic === (evidence === 'synthetic') && r.profile_version===catalog.profile_version && (r.runtime??'legacy')===$('runtime').value && (r.task_id??'pricing-js-v1')===$('scenario').value; }
function syncTasks() { const ids=catalog.runtimes?.[$('runtime').value]?.tasks??[]; if(!ids.length||ids.join()===[...$('scenario').options].map(o=>o.value).join())return; $('scenario').replaceChildren(...ids.map(id=>{const o=el('option',taskInfo(id)?.name??id);o.value=id;return o;})); }
function renderPager(id, page, totalItems, perPage, onPage) {
  const nav = $(id);
  if (!nav) return;
  const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
  if (totalItems <= perPage) { nav.hidden = true; nav.replaceChildren(); return; }
  nav.hidden = false; nav.replaceChildren();
  const start = (page - 1) * perPage + 1, end = Math.min(totalItems, page * perPage);
  nav.append(el('span', `${start}–${end} of ${totalItems} · Page ${page} / ${totalPages}`, 'pager-info'));
  const controls = el('div', '', 'pager-controls');
  const prev = el('button', '← Prev', 'pager-btn'); prev.type = 'button'; prev.disabled = page <= 1;
  prev.onclick = () => onPage(page - 1); controls.append(prev);
  const pages = [];
  for (let p = 1; p <= totalPages; p++) {
    if (p === 1 || p === totalPages || Math.abs(p - page) <= 1) pages.push(p);
    else if (pages[pages.length - 1] !== '…') pages.push('…');
  }
  for (const p of pages) {
    if (p === '…') controls.append(el('span', '…', 'pager-ellipsis'));
    else {
      const btn = el('button', String(p), 'pager-btn' + (p === page ? ' is-active' : ''));
      btn.type = 'button'; btn.onclick = () => { if (p !== page) onPage(p); };
      controls.append(btn);
    }
  }
  const next = el('button', 'Next →', 'pager-btn'); next.type = 'button'; next.disabled = page >= totalPages;
  next.onclick = () => onPage(page + 1); controls.append(next);
  nav.append(controls);
}
function setFilter(value) {
  evidence = value;
  runsPage = 1;
  document.querySelectorAll('[data-filter]').forEach(b => {b.classList.toggle('selected', b.dataset.filter === value); b.setAttribute('aria-pressed', String(b.dataset.filter === value));});
  render();
}
function renderFleet(runs) {
  const host = $('fleet'); if (!host) return;
  const list = [...runs].sort((a, b) => (b.started_ns ?? 0) - (a.started_ns ?? 0)).slice(0, 6);
  const next = JSON.stringify(list.map(r => [r.id, r.status, r.runtime, r.check?.passed, r.ended_ns, r.synthetic]));
  if (next === fleetSignature) return;
  fleetSignature = next;
  host.replaceChildren();
  if (!list.length) { host.append(el('p', 'No agent has run yet. Start a build or replay the handover.', 'muted')); return; }
  for (const run of list) {
    const card = el('a', '', 'fleet-card'); card.href = LANGFUSE; card.target = '_blank'; card.rel = 'noreferrer';
    const top = el('div', '', 'fleet-top');
    top.append(el('span', TIERS[run.runtime ?? 'legacy'] ?? (run.runtime ?? 'legacy'), 'fleet-tier'));
    top.append(el('span', run.synthetic ? 'simulation' : run.status.replaceAll('_', ' '),
                  'fleet-state ' + (run.status === 'passed' ? 'ok' : run.status === 'running' ? 'live' : '')));
    card.append(top);
    card.append(el('strong', taskInfo(run.task_id ?? 'pricing-js-v1')?.name ?? run.task_id ?? 'Cart totals', 'fleet-task'));
    card.append(el('span', [run.synthetic ? 'replay' : label(run.model), run.check ? `${run.check.passed}/${checkTotal(run)} checks` : '',
      run.ended_ns ? seconds((run.ended_ns - run.started_ns) / 1e6) : 'running'].filter(Boolean).join(' · '), 'fleet-meta'));
    host.append(card);
  }
}
function render() {
  $('task-title').textContent=taskInfo($('scenario').value)?.name??'Cart totals';
  const runs = cachedRuns.filter(selected), rows = cachedRows.filter(selected), latest = runs[0];
  $('runs').replaceChildren(); $('kpi-cards').replaceChildren(); $('model-rows').replaceChildren();
  const completed = runs.filter(r=>r.ended_ns), successes = completed.filter(r=>r.status==='passed' && Number.isInteger(r.human_interventions) && r.human_interventions===0);
  const costs = runs.reduce((s,r)=>s+Number(r.native_cost_usd),0);
  const costResolved=runs.length>0&&runs.every(r=>r.synthetic||r.usage_complete===true)&&runs.every(r=>r.ended_ns);
  const times = completed.map(r=>(r.ended_ns-r.started_ns)/1e6).sort((a,b)=>a-b);
  const median = times.length ? (times[Math.floor((times.length-1)/2)] + times[Math.ceil((times.length-1)/2)])/2 : null;
  const usages = runs.flatMap(r=>r.events.filter(e=>e.name==='gen_ai.request'));
  const cards = [
    ['Passed without help', completed.length ? Math.round(successes.length/completed.length*100)+'%' : '—', `${successes.length} of ${completed.length} passed on their own · sandbox fixture`],
    ['Cost per clean pass*', successes.length&&costResolved ? money(costs/successes.length) : '—', evidence==='synthetic'?'Synthetic replay · no model calls':costResolved?'Includes failed attempts · CLI estimate':'Usage incomplete · no cost ranking'],
    ['Median run time', seconds(median), `${completed.length} finished runs · end to end`],
    ['Total tokens', pretty(usages.reduce((s,e)=>s+e['gen_ai.usage.input_tokens']+e['gen_ai.usage.output_tokens'],0)), `${runs.reduce((s,r)=>s+r.events.filter(e=>e.name==='agent.handover').length,0)} context handover(s)`]
  ];
  for(const [title,value,note] of cards) { const c=el('article','','kpi');c.append(el('span',title,'eyebrow'),el('strong',value),el('small',note));$('kpi-cards').append(c); }
  $('execution-status').textContent = latest ? latest.status.replaceAll('_',' ') : 'Ready';
  document.querySelector('.execution-panel').classList.toggle('running', latest?.status==='running');
  const peak = Math.max(0,...(latest?.events ?? []).map(e=>e['aeion.context.observed'] ?? 0));
  $('context-value').textContent = `${pretty(peak)} / ${pretty(latest?.limit ?? 250000)}`;
  $('context-fill').style.width = Math.min(100,peak/(latest?.limit ?? 250000)*100)+'%';
  $('active-detail').replaceChildren();
  if(latest) {
    const detail=$('active-detail');
    detail.append(el('p', latest.synthetic ? 'Handover replay: fresh agent session continues from the saved checkpoint.' : label(latest.model)+' · sandbox run', 'detail-heading'));
    const info=el('div','','detail-meta');info.append(el('div',`${latest.agents} agent(s) · ${latest.check?.passed ?? '—'}/${checkTotal(latest)} checks · ${latest.human_interventions ? 'human assisted' : 'zero human help'}`));
    info.append(el('div',latest.events.some(e=>e.name==='agent.handover') ? 'First agent retired at 250k tokens; second agent resumed from the verified handover file.' : 'Frozen task · protected Deno verifier · bounded sandbox.'));
    info.append(el('code',`Trace ${latest.trace_id ?? 'pending'}`));detail.append(info);
    const statuses=el('div','','memory-status');statuses.append(el('span',latest.claude_mem_id ? `Checkpoint #${latest.claude_mem_id} verified` : 'Checkpoint · waiting'),el('span',`Hindsight · ${latest.memory?.status ?? 'waiting'}`));detail.append(statuses);
  } else $('active-detail').append(el('p','Start a live build or replay the 250k handover. Runtime state, test verdicts, and memory confirmations appear here.'));
  const totalRunPages = Math.max(1, Math.ceil(runs.length / RUNS_PER_PAGE));
  if (runsPage > totalRunPages) runsPage = totalRunPages;
  const pagedRuns = runs.slice((runsPage - 1) * RUNS_PER_PAGE, runsPage * RUNS_PER_PAGE);
  for(const run of pagedRuns) {
    const card=el('article','','run'), head=el('div','','run-header');
    head.append(el('h2',run.synthetic ? '250k handover · synthetic replay' : label(run.model)+' · '+(taskInfo(run.task_id)?.name??run.task_id??'Cart totals')),el('span',run.status.replaceAll('_',' '),'tag'));card.append(head);
    const cost = run.synthetic ? 'synthetic · no model call' : run.usage_complete ? `${money(run.native_cost_usd)} native estimate` : 'cost unresolved';
    card.append(el('div',`${run.agents} agent(s) · ${run.check?.passed ?? '—'}/${checkTotal(run)} checks · ${cost} · ${run.human_interventions ? 'assisted' : 'zero human help'}`,'run-meta'));
    const timeline=el('div','','timeline');
    const names={'agent.started':'Agent started','gen_ai.request':'Model response','gate.closed':'Gate closed','agent.handover':'Fresh session','artifact.checked':'Artifact checked','memory.checkpoint':'Checkpoint verified','task.failed':'Task stopped','handover.prepared':'Handover MD ready','handover.acknowledged':'MD acknowledged','context.preflight':'Input counted','memory.retained':'Summary saved','process.retired':'Process retired','session.wiped':'Context wiped','model.step.started':'Model step','tool.finished':'Tool finished'};
    for(const event of run.events) {let text=names[event.name]??event.name;if(event['aeion.context.observed']!==undefined)text+=' · '+pretty(event['aeion.context.observed']);timeline.append(el('span',text,'event'+(['agent.handover','gate.closed'].includes(event.name)?' handover':'')));}
    card.append(timeline);
    const actions=el('div','','run-actions');
    const copy=el('button','Copy trace ID','text-button');copy.onclick=()=>navigator.clipboard?.writeText(run.trace_id ?? '').then(()=>{$('message').textContent='Trace ID copied.';});actions.append(copy);
    if(run.ended_ns && !run.human_interventions) {const assist=el('button','Log manual help','text-button');assist.disabled=busy;assist.onclick=async()=>{await post({mode:'intervention',run_id:run.id});};actions.append(assist);}
    const logs=el('a','Correlated logs ↗','text-button');logs.href=`/api/runs/${run.id}/logs`;logs.target='_blank';actions.append(logs);if(run.handover_md_sha256){const md=el('a','HANDOVER.md ↗','text-button');md.href=`/api/runs/${run.id}/handover`;md.target='_blank';actions.append(md);}card.append(actions);if(run.failure)card.append(el('p',run.failure,'fineprint'));$('runs').append(card);
  }
  if(!runs.length)$('runs').append(el('p',evidence==='real' ? 'No real runs recorded for this filter yet. Click "Run Flue build" to start one.' : 'Click "Replay 250k handover" to run the synthetic handover demo.','empty'));
  renderPager('runs-pager', runsPage, runs.length, RUNS_PER_PAGE, (p) => { runsPage = p; render(); });
  for(const row of rows) {
    const tr=el('tr');const model=el('td',label(row.model));model.append(el('small',`${row.synthetic?'Synthetic':'Real Go'} · ${row.profile_version??'unversioned'} · ${pretty(row.limit)} ${row.metric.replaceAll('_',' ')}`));tr.append(model);
    for(const text of [`${row.completed} / ${row.offered}`,`${row.autonomous} / ${row.completed}`,seconds(row.median_ms),`${pretty(row.input_tokens)} / ${pretty(row.output_tokens)}`,money(row.cost_per_autonomous_success_usd)])tr.append(el('td',text));$('model-rows').append(tr);
  }
  const recommendation=recommendations[$('scenario').value];
  $('decision').textContent = evidence==='synthetic' ? 'Synthetic replays show how the 250k handover works, not how real models rank.' : recommendation?.basis==='best_observed_for_task' ? `${label(recommendation.model)} leads on this task (${recommendation.objective}) based on at least two clean passes.` : 'Default profile: GLM 5.3 Flash. Run at least two unassisted passes per model before comparing cost and speed.';
  chart(rows);
}
function svg(tag,attrs={},text='') {const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,String(v));e.textContent=text;return e;}
function chart(rows) {
  const host=$('pareto');host.replaceChildren();const points=rows.filter(r=>r.median_ms!==null&&r.cost_per_autonomous_success_usd!==null);
  for(let i=0;i<4;i++){const y=35+i*58;host.append(svg('line',{x1:65,x2:570,y1:y,y2:y,class:'chart-grid'}));}
  host.append(svg('line',{x1:65,x2:570,y1:225,y2:225,class:'chart-axis'}),svg('line',{x1:65,x2:65,y1:25,y2:225,class:'chart-axis'}));
  host.append(svg('text',{x:65,y:17},'Estimated cost per clean pass ($)'),svg('text',{x:390,y:277},'Median run time (seconds) →'));
  const xmax=Math.max(10,...points.map(r=>r.median_ms/1000))*1.2,ymax=Math.max(.0001,...points.map(r=>Number(r.cost_per_autonomous_success_usd)))*1.3;
  for(let i=0;i<4;i++){const v=i*ymax/3;host.append(svg('text',{x:3,y:228-i*62},v.toFixed(5)));host.append(svg('text',{x:65+i*165,y:247},(i*xmax/3).toFixed(1)));}
  points.forEach((row,i)=>{const x=65+row.median_ms/1000/xmax*495,y=225-Number(row.cost_per_autonomous_success_usd)/ymax*186;const circle=svg('circle',{cx:x,cy:y,r:12,class:row.autonomous_rate===1?'point pass':'point',tabindex:0});circle.append(svg('title',{},`${label(row.model)}: ${row.autonomous}/${row.completed} autonomous, ${seconds(row.median_ms)}, ${money(row.cost_per_autonomous_success_usd)}/success`));host.append(circle,svg('text',{x:Math.min(x+16,455),y:y+(i%2?22:-17)},label(row.model)));});
  if(!points.length)host.append(svg('text',{x:185,y:130},'Run a task to plot cost and speed.'));
  $('chart-count').textContent=`${points.length} profile(s) · ${evidence==='real'?'real runs':'synthetic replay'}`;
}
async function refresh() {
  if(refreshing)return;
  refreshing=true;
  try {
    const [health,runs,rows,configuration,choices,batches]=await Promise.all(['/api/health','/api/runs','/api/kpis','/api/catalog','/api/recommendations?objective='+$('objective').value+'&runtime='+$('runtime').value,'/api/campaigns'].map(url=>fetch(url).then(r=>r.json())));
    catalog=configuration;recommendations=choices;campaigns=batches;syncTasks();
    busy=campaigns.some(c=>c.status==='running')||runs.some(r=>r.status==='running'||r.postprocessing||r.memory?.status==='pending');
    $('limit').replaceChildren(document.createTextNode(pretty(health.limit)+' '),el('small','tokens'));
    $('metric').textContent=health.metric==='active_context'?'Active input context · cache included':'Cumulative input per agent';
    const tier=health.ready?.[$('runtime').value];
    $('live').disabled=busy||!tier?.live;$('simulate').disabled=busy||!tier?.simulation;$('tour').disabled=busy||!tier?.simulation;$('benchmark').disabled=busy||!health.live_ready;
    stackState('controller',true,'Online','');stackState('flue',health.live_ready===true,'Ready','Not ready');stackState('sandbox',health.sandbox_ready===true,'Qualified','Unavailable');
    $('sandbox-status').textContent=health.sandbox_ready?'OpenShell qualified · NVIDIA telemetry disabled':'OpenShell unavailable or expired · live builds paused';
    const batch=campaigns[0];$('campaign-status').textContent=batch?`${batch.status} · ${batch.run_ids.length}/${batch.planned} runs · ${money(batch.native_cost_estimate_usd)} native estimate`:'';
    const next=JSON.stringify([runs,rows,evidence,choices,$('runtime').value,$('scenario').value]);cachedRuns=runs;cachedRows=rows;renderFleet(runs);renderCheckpoints(runs);if(next!==signature){signature=next;render();}
  } catch {$('message').textContent='Local server temporarily unreachable.';} finally {refreshing=false;}
}
function stackState(name,good,yes,no){document.querySelectorAll(`[data-stack="${name}"] .stack-state`).forEach(e=>{e.textContent=good?yes:no;e.classList.toggle('ok',good);e.classList.toggle('bad',!good);});}
const SERVICES=['otel','langfuse','hindsight'];
async function integrations(){try{const states=await fetch('/api/integrations').then(r=>r.json());document.querySelectorAll('[data-service]').forEach(e=>{const good=states[e.dataset.service]==='connected';e.classList.toggle('connected',good);e.title=good?'Connected':'Unavailable';});const connected=SERVICES.filter(n=>states[n]==='connected').length;for(const n of SERVICES)stackState(n,states[n]==='connected','Connected','Unavailable');$('system-dot').classList.toggle('connected',connected===SERVICES.length);$('system-status').textContent=`${connected}/${SERVICES.length} services online`;}catch{$('system-status').textContent='Services unknown';for(const n of SERVICES){document.querySelectorAll(`[data-stack="${n}"] .stack-state`).forEach(e=>{e.textContent='Unknown';e.classList.remove('ok','bad');});}}}
async function post(payload){$('message').textContent='';try{const r=await fetch('/api/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)$('message').textContent=result.error;}catch{$('message').textContent='Unable to send request.';}await refresh();}
async function start(mode){setFilter(mode==='simulation'?'synthetic':'real');await post({mode,profile:$('profile').value,task_id:$('scenario').value,objective:$('objective').value,runtime:$('runtime').value});}
document.querySelectorAll('[data-lab-tab]').forEach((btn) => {
  btn.addEventListener('click', () => switchLabTab(btn.dataset.labTab));
});
$('benchmark').onclick=()=>post({mode:'benchmark'});$('scenario').onchange=render;$('objective').onchange=refresh;$('runtime').onchange=()=>{syncTasks();refresh();};
$('simulate').onclick=()=>start('simulation');$('live').onclick=()=>start('live');$('tour').onclick=async()=>{switchLabTab('sessions');await start('simulation');};
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>setFilter(b.dataset.filter));
let bank='real',checkpointSignature='';
function renderCheckpoints(runs){
  const all=runs.filter(r=>Number.isInteger(r.claude_mem_id)).sort((a,b)=>(b.started_ns??0)-(a.started_ns??0));
  const next=JSON.stringify([checkpointsPage,all.map(r=>[r.id,r.claude_mem_id,r.artifact_sha256])]);if(next===checkpointSignature)return;checkpointSignature=next;
  const host=$('checkpoints');host.replaceChildren();
  if(!all.length){host.append(el('p','No checkpoints saved yet. Replay the 250k handover in the Run a task section to create one.','muted'));renderPager('checkpoints-pager',1,0,RUNS_PER_PAGE,()=>{});return;}
  const totalPages = Math.max(1, Math.ceil(all.length / RUNS_PER_PAGE));
  if (checkpointsPage > totalPages) checkpointsPage = totalPages;
  const list = all.slice((checkpointsPage - 1) * RUNS_PER_PAGE, checkpointsPage * RUNS_PER_PAGE);
  for(const run of list){
    const item=el('div','','memory-item');
    item.append(el('strong',`Checkpoint #${run.claude_mem_id} · ${taskInfo(run.task_id??'pricing-js-v1')?.name??run.task_id??'Task'}`));
    item.append(el('span',`${run.synthetic?'Synthetic replay':label(run.model)} · ${run.agents} agent(s) · ${run.check?.passed??'unknown'}/${checkTotal(run)} checks`));
    item.append(el('code',`Run artifact SHA-256 ${run.artifact_sha256??'unknown'}`));
    const result=el('div');const button=el('button','Verify local checkpoint ↗','text-button');button.type='button';
    button.onclick=async()=>{button.disabled=true;result.replaceChildren(el('p','Reading from disk…'));try{const r=await fetch(`/api/memory/checkpoint/${run.claude_mem_id}`);const c=await r.json();if(!r.ok||c.status!=='ok'){result.replaceChildren(el('p',r.status===404?'This checkpoint was not written by this server.':'Checkpoint unavailable on disk.'));return;}
      const same=c.sha256&&c.sha256===run.artifact_sha256;const dl=el('dl');for(const [k,v] of [['Task',c.task],['Previous agent',c.previous_agent],['Artifact',c.artifact],['Checks',c.check?.passed!=null?`${c.check.passed}/${c.check.total??'unknown'}`:'unknown'],['SHA-256',c.sha256]]){dl.append(el('dt',k),el('dd',v==null?'unknown':String(v)));}
      const verdict=el('span',same?'matches the run artifact':'digest mismatch','verdict '+(same?'ok':'bad'));const head=el('p','Verified from disk');head.append(verdict);result.replaceChildren(head,dl);}catch{result.replaceChildren(el('p','Checkpoint unavailable on disk.'));}finally{button.disabled=false;}};
    item.append(button,result);host.append(item);
  }
  renderPager('checkpoints-pager', checkpointsPage, all.length, RUNS_PER_PAGE, (p) => { checkpointsPage = p; checkpointSignature = ''; renderCheckpoints(cachedRuns); });
}
function setBank(value){bank=value;document.querySelectorAll('[data-bank]').forEach(b=>{b.classList.toggle('selected',b.dataset.bank===value);b.setAttribute('aria-pressed',String(b.dataset.bank===value));});$('recalled').replaceChildren(el('p',`Ask a question to search the ${value==='real'?'real sessions':'synthetic replays'} bank.`,'muted'));$('recall-summary').textContent='';}
function recalledCard(item){
  const card=el('div','','memory-item');let a=null;try{a=JSON.parse(item.text);}catch{}
  if(a&&a.schema==='aeion.model-decision.v1'){card.append(el('strong','Model decision'),el('span',Object.values(a.recommendations??{}).map(r=>`${r.task_id}: ${label(r.model)} (${r.basis})`).join(' · ')||'No recommendation recorded'));return card;}
  if(a&&typeof a==='object'){
    card.append(el('strong',`${a.task??'Task'} · ${a.model?label(a.model):'unknown model'}`));
    const dl=el('dl');for(const [k,v] of [['Outcome',a.status],['Input tokens',a.input_tokens!=null?pretty(a.input_tokens):null],['Output tokens',a.output_tokens!=null?pretty(a.output_tokens):null],['Duration',a.duration_ms!=null?seconds(a.duration_ms):null],['Agents',a.agents],['Human interventions',a.human_interventions],['Accounting',a.accounting_basis]]){dl.append(el('dt',k),el('dd',v==null?'unknown':String(v)));}
    card.append(dl);if(a.assessment)card.append(el('p',a.assessment));return card;
  }
  card.append(el('strong','Recalled note'),el('span',item.text));return card;
}
async function recall(question){
  const button=$('recall');button.disabled=true;$('recall-summary').textContent='';$('recalled').replaceChildren(el('p','Searching Hindsight…','muted'));
  const params=new URLSearchParams();if(bank==='synthetic')params.set('synthetic','true');if(question)params.set('q',question);
  try{const r=await fetch('/api/memory'+(params.toString()?'?'+params:''));const result=await r.json();
    if(r.status===400){$('recalled').replaceChildren(el('p','Use up to 160 printable characters.','muted'));return;}
    if(!r.ok||result.status!=='ok'){$('recalled').replaceChildren(el('p','Hindsight is offline or returned no results.','muted'));return;}
    const items=result.results??[];$('recall-summary').textContent=`${items.length} result${items.length===1?'':'s'} from ${bank==='real'?'real sessions':'synthetic replays'} for “${result.query}”.`;
    $('recalled').replaceChildren(...items.map(recalledCard));if(!items.length)$('recalled').append(el('p','No matching session notes found.','muted'));
  }catch{$('recalled').replaceChildren(el('p','Hindsight is offline or returned no results.','muted'));}finally{button.disabled=false;}
}
document.querySelectorAll('[data-bank]').forEach(b=>b.onclick=()=>setBank(b.dataset.bank));
$('recall-form').onsubmit=(event)=>{event.preventDefault();recall($('recall-query').value.trim());};
document.querySelectorAll('[data-query]').forEach(b=>b.onclick=()=>{$('recall-query').value=b.dataset.query;recall(b.dataset.query);});
refresh();integrations();setInterval(refresh,1500);setInterval(integrations,20000);
