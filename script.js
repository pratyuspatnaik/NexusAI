/* Loom — Domain-Adaptive AI Orchestration (frontend prototype)
   Everything below the "MOCK DATA" and "MOCK ENGINE" sections is simulated.
   Integration seams are marked INTEGRATION: Gemini (reasoning), Supabase + pgvector (memory/RAG),
   Node.js (tool execution). No real model or backend is called. */
'use strict';

/* ============================ MOCK DATA ============================ */
const S = s => ({ type: 'object', properties: Object.fromEntries(s.split(',').map(x => { const [k, t] = x.split(':'); return [k, { type: t }]; })), required: s.split(',').map(x => x.split(':')[0]) });
const T = (name, desc, cat, scope, risk, status, reg, params, perm = 'write') =>
  ({ name, desc, cat, scope, risk, status, registered: reg, enabled: reg, params: S(params), handler: `handlers/${name}.js`, perm });

const PROJECTS = {
  event: {
    name: 'College Event Management', short: 'Tech Fest 2026',
    prompt: 'Acme Corporation has reduced its sponsorship commitment from ₹10 lakh to ₹6 lakh.',
    domain: 'Event & sponsorship operations',
    modules: ['Sponsor tracking', 'Budget management', 'Promotional deliverables', 'Approval workflows'],
    entities: ['Sponsor', 'Budget', 'Deliverable', 'Approval', 'Email thread'],
    rels: [['Sponsor', 'Budget', 'funds'], ['Sponsor', 'Deliverable', 'entitles'], ['Deliverable', 'Approval', 'needs'], ['Budget', 'Approval', 'needs'], ['Email thread', 'Sponsor', 'mentions']],
    roles: ['Event lead', 'Finance coordinator', 'Sponsorship manager', 'Dean (approver)'],
    workflows: ['Sponsor commitment change', 'Budget revision', 'Deliverable re-tiering', 'Dean approval'],
    reqs: ['Record Acme commitment as ₹6,00,000 (was ₹10,00,000)', 'Recalculate sponsorship income and budget gap of ₹4,00,000', 'Downgrade promotional tier from Title to Gold', 'Notify Acme and route revised budget for approval'],
    deps: ['Budget depends on sponsor commitments', 'Deliverables depend on sponsor tier', 'Approvals depend on budget revision'],
    docs: [
      { t: 'Acme Corporation sponsorship agreement', src: 'sponsor_agreements/acme.pdf', type: 'Document', score: .96, why: 'Defines ₹10L Title tier and the deliverables tied to it.' },
      { t: 'Sponsorship tier policy', src: 'rules/tiers.md', type: 'Business rule', score: .91, why: 'Commitments under ₹8L qualify for Gold, not Title.' },
      { t: 'Budget revision rule', src: 'rules/finance.md', type: 'Business rule', score: .88, why: 'Any change above ₹1L needs Dean approval.' },
      { t: 'Event budget sheet', src: 'sheets/budget_v7.xlsx', type: 'Schema', score: .84, why: 'Sponsorship income line currently shows ₹10,00,000 for Acme.' },
      { t: 'Thread: "Acme update — revised amount"', src: 'gmail/thread/8f21', type: 'Email', score: .8, why: 'Source of the change; sent by Acme CSR lead.' },
      { t: 'Sponsor update workflow', src: 'templates/sponsor_change.yaml', type: 'Workflow template', score: .74, why: 'Standard order: record, rebudget, re-tier, notify, approve.' }
    ],
    stm: ['Active entity: Acme Corporation', 'Open thread 8f21', 'Pending: budget revision'],
    ltm: ['Acme sponsored 2024 and 2025', 'Dean approves within 2 days', 'Finance prefers ₹ lakh notation'],
    tools: [
      T('update_sponsor', 'Update a sponsor record and commitment amount.', 'Sponsors', 'domain', 'high', 'available', true, 'sponsor_id:string,new_amount:number'),
      T('update_budget', 'Adjust a budget line and recompute totals.', 'Finance', 'domain', 'high', 'available', true, 'line_id:string,delta:number'),
      T('flag_promotion', 'Flag deliverables for tier change.', 'Promotion', 'domain', 'medium', 'available', true, 'sponsor_id:string,new_tier:string'),
      T('draft_email', 'Draft an email for review before sending.', 'Communication', 'domain', 'low', 'available', true, 'to:string,subject:string,body:string', 'draft'),
      T('manage_approvals', 'Create or route an approval request.', 'Approvals', 'domain', 'low', 'available', true, 'item:string,approver:string'),
      T('search_knowledge', 'Semantic search over project knowledge.', 'Knowledge', 'universal', 'low', 'available', false, 'query:string', 'read'),
      T('create_calendar_event', 'Create a calendar event.', 'Calendar', 'integration', 'low', 'available', false, 'title:string,when:string'),
      T('notify_whatsapp', 'Send a WhatsApp message to a contact.', 'Communication', 'integration', 'medium', 'missing', false, 'phone:string,message:string')
    ],
    actions: [
      { tool: 'update_sponsor', label: 'Update Acme commitment', expected: '₹6,00,000', approval: true, why: 'Changes a financial record' },
      { tool: 'update_budget', label: 'Reduce sponsorship income by ₹4,00,000', expected: 'Sponsorship line = ₹6,00,000', approval: true, why: 'Budget change above ₹1L' },
      { tool: 'flag_promotion', label: 'Move Acme from Title to Gold tier', expected: 'Tier = Gold', approval: true, why: 'Alters promised deliverables' },
      { tool: 'draft_email', label: 'Draft confirmation to Acme', expected: 'Draft saved', fail: 'Gmail API timed out (504)' },
      { tool: 'manage_approvals', label: 'Route revised budget to Dean', expected: 'Pending approvals = 1' }
    ],
    impact: 'Budget gap ₹4,00,000 · 3 deliverables affected · 1 approval required'
  },
  erp: {
    name: 'College ERP', short: 'Campus ERP',
    prompt: 'Build a College ERP with student management, faculty management, attendance tracking, fee management, examination management, and timetable scheduling.',
    domain: 'Higher-education administration (ERP)',
    modules: ['Student management', 'Faculty management', 'Attendance tracking', 'Fee management', 'Examination management', 'Timetable scheduling'],
    entities: ['Student', 'Faculty', 'Course', 'Attendance', 'Fee', 'Exam', 'Timetable'],
    rels: [['Student', 'Course', 'enrolls'], ['Faculty', 'Course', 'teaches'], ['Student', 'Attendance', 'has'], ['Student', 'Fee', 'owes'], ['Course', 'Exam', 'has'], ['Course', 'Timetable', 'scheduled in']],
    roles: ['Admin', 'Faculty', 'Student', 'Accounts officer', 'Exam controller'],
    workflows: ['Admission and enrollment', 'Daily attendance', 'Fee collection', 'Exam scheduling', 'Timetable generation'],
    reqs: ['Create and update student records', 'Assign faculty to courses', 'Mark attendance per session', 'Calculate fees with late charges', 'Generate conflict-free timetable'],
    deps: ['Attendance depends on enrollment', 'Timetable depends on faculty assignment', 'Exam eligibility depends on attendance'],
    docs: [
      { t: 'Academic regulations 2026', src: 'docs/regulations.pdf', type: 'Business rule', score: .93, why: '75% attendance needed for exam eligibility.' },
      { t: 'Fee structure by program', src: 'sheets/fees.xlsx', type: 'Schema', score: .9, why: 'Defines fee heads and late-fee slabs.' },
      { t: 'Student table schema', src: 'db/schema.sql', type: 'Schema', score: .85, why: 'Existing columns for student_id, program, year.' },
      { t: 'Timetable constraint template', src: 'templates/timetable.yaml', type: 'Workflow template', score: .78, why: 'No faculty double-booking; 4 slots per day.' }
    ],
    stm: ['Active module: Student management', 'Draft schema generated'],
    ltm: ['Semester starts in August', 'Accounts closes fee window after 15 days'],
    tools: [
      T('create_student', 'Create a student record.', 'Students', 'domain', 'medium', 'available', true, 'name:string,program:string,year:number'),
      T('update_student', 'Update fields on a student record.', 'Students', 'domain', 'medium', 'available', true, 'student_id:string,fields:object'),
      T('mark_attendance', 'Mark attendance for a session.', 'Attendance', 'domain', 'low', 'available', true, 'student_id:string,status:string'),
      T('calculate_fees', 'Compute fee due including late charges.', 'Fees', 'domain', 'low', 'available', true, 'student_id:string', 'read'),
      T('generate_timetable', 'Generate a timetable from constraints.', 'Timetable', 'domain', 'high', 'available', true, 'term:string,constraints:object'),
      T('assign_faculty', 'Assign a faculty member to a course.', 'Faculty', 'domain', 'medium', 'available', false, 'faculty_id:string,course_id:string'),
      T('search_knowledge', 'Semantic search over project knowledge.', 'Knowledge', 'universal', 'low', 'available', false, 'query:string', 'read'),
      T('send_sms', 'Send SMS to parents or students.', 'Communication', 'integration', 'medium', 'missing', false, 'phone:string,message:string')
    ],
    actions: [
      { tool: 'create_student', label: 'Create sample student Aarav Das', expected: 'Student ID = S-1042' },
      { tool: 'assign_faculty', label: 'Assign Dr. Mehta to CS201', expected: 'Faculty = Dr. Mehta' },
      { tool: 'mark_attendance', label: 'Mark Aarav present for CS201', expected: 'Attendance = Present', fail: 'Write conflict on attendance table' },
      { tool: 'calculate_fees', label: 'Calculate Semester 3 fees', expected: '₹84,500' },
      { tool: 'generate_timetable', label: 'Generate Semester 3 timetable', expected: '0 conflicts', approval: true, why: 'Overwrites the published timetable' }
    ],
    impact: '6 modules · 7 entities · 5 starter actions'
  }
};

const AGENTS = {
  coord: { n: 'Coordinator', x: 50, y: 12, d: 'Interprets the request, delegates, and decides when to stop or replan.' },
  know: { n: 'Knowledge', x: 18, y: 40, d: 'Retrieves entities, rules, and memory relevant to the request.' },
  plan: { n: 'Planning', x: 50, y: 40, d: 'Builds the impact analysis and an ordered action plan.' },
  comm: { n: 'Communication', x: 82, y: 40, d: 'Drafts and routes messages and notifications.' },
  exec: { n: 'Execution', x: 33, y: 76, d: 'Calls registered tools using idempotency keys and retries.' },
  ver: { n: 'Verification', x: 67, y: 76, d: 'Reads back state and compares it with the expected result.' }
};
const EDGES = [['coord', 'know'], ['coord', 'plan'], ['know', 'plan'], ['plan', 'comm'], ['plan', 'exec'], ['exec', 'ver'], ['comm', 'ver']];
const TABS = [['req', 'Requirement'], ['request', 'Request'], ['output', 'Output']];
const EXAMPLES = ['Manage a college technical fest with sponsor tracking, budget management, promotional deliverables, and approval workflows.', PROJECTS.erp.prompt, 'Acme Corporation has reduced its sponsorship commitment from ₹10 lakh to ₹6 lakh.'];

/* ============================ STATE ============================ */
const state = {
  pid: 'event', tab: 'req',
  analyzed: { event: true, erp: false },
  history: { event: [{ text: PROJECTS.event.prompt, at: 'Today' }], erp: [] },
  tools: {}, runs: {},
  analyzing: null, error: '', draft: '', kq: '', dfilter: 'all', rq: '', rrisk: 'all', selAgent: 'coord', editedReqs: {}
};
for (const id in PROJECTS) { state.tools[id] = structuredClone(PROJECTS[id].tools); state.editedReqs[id] = [...PROJECTS[id].reqs]; }
const P = () => PROJECTS[state.pid];
const run = () => state.runs[state.pid] || (state.runs[state.pid] = { status: 'idle', idx: 0, steps: [], agent: {}, text: {}, prev: null, res: [], audit: [], appr: [], skipped: {}, token: 0 });
const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const $ = s => document.querySelector(s);

/* ============================ MOCK ENGINE ============================ */
// INTEGRATION: replace with a Gemini function-calling request that returns the same shape.
function matchProject(text) {
  if (/erp|student|faculty|attendance|timetable/i.test(text)) return 'erp';
  if (/sponsor|event|fest|budget|deliverable/i.test(text)) return 'event';
  return null;
}
function buildSteps(p) {
  const s = [
    { a: 'coord', t: 'Parsed request and delegated retrieval' },
    { a: 'know', t: `Retrieved ${p.docs.length} context items from memory` },
    { a: 'plan', t: `Impact: ${p.impact}` }
  ];
  p.actions.forEach((x, i) => { if (x.approval) s.push({ a: 'coord', t: `Awaiting approval: ${x.label}`, ap: i }); });
  s.push({ a: 'exec', t: `Executing ${p.actions.length} actions with idempotency keys`, exec: true });
  if (p.actions.some(x => x.tool === 'draft_email')) s.push({ a: 'comm', t: 'Drafted message for review' });
  s.push({ a: 'ver', t: 'Reading back state and comparing with expected', ver: true });
  return s;
}
function startRun() {
  const r = run(), p = P();
  r.token++; Object.assign(r, { status: 'running', idx: 0, steps: buildSteps(p), agent: {}, text: {}, prev: null, res: [], audit: [], appr: [], skipped: {} });
  audit(`Run started for “${p.name}”`);
  advance(r.token, state.pid);
}
function audit(t) { run().audit.unshift({ at: now(), t }); }
function advance(token, pid) {
  const r = state.runs[pid]; if (!r || r.token !== token) return;
  if (r.idx >= r.steps.length) { r.status = 'done'; r.prev = null; audit('Workflow finished'); refresh(); return; }
  const st = r.steps[r.idx];
  r.agent[st.a] = st.ap !== undefined ? 'waiting' : 'processing'; r.text[st.a] = st.t;
  if (st.ap !== undefined) { r.status = 'waiting'; audit(`Approval requested: ${PROJECTS[pid].actions[st.ap].label}`); refresh(); return; }
  refresh();
  setTimeout(() => {
    if (r.token !== token) return;
    if (st.exec) executeActions(r, pid);
    r.agent[st.a] = 'completed'; r.prev = st.a; r.idx++; advance(token, pid);
  }, 1100);
}
function executeActions(r, pid) {
  PROJECTS[pid].actions.forEach((a, i) => {
    if (r.skipped[i]) { r.res[i] = { s: 'skipped', actual: 'Not executed (rejected)' }; return; }
    if (a.fail && !a.retried) { r.res[i] = { s: 'failed', actual: a.fail }; audit(`${a.tool} failed: ${a.fail}`); }
    else { r.res[i] = { s: 'verified', actual: a.expected }; audit(`${a.tool} executed · key ${a.tool}-${(i + 1) * 7919}`); }
  });
}
function decide(ok) {
  const r = run(), st = r.steps[r.idx], a = P().actions[st.ap];
  r.appr.unshift({ at: now(), label: a.label, ok });
  audit(`${ok ? 'Approved' : 'Rejected'}: ${a.label}`);
  if (!ok) r.skipped[st.ap] = true;
  r.agent[st.a] = 'completed'; r.status = 'running'; r.idx++;
  advance(r.token, state.pid);
}
function retryAction(i) {
  const a = P().actions[i], r = run();
  a.retried = true; r.res[i] = { s: 'verified', actual: a.expected };
  audit(`Retry succeeded for ${a.tool} (same idempotency key)`); toast('Retry succeeded'); refresh();
}
function searchKnowledge(q) {
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  return P().docs.map(d => {
    const hay = (d.t + d.why + d.type + d.src).toLowerCase();
    const hit = terms.filter(t => hay.includes(t)).length;
    return { ...d, score: terms.length ? Math.min(.99, d.score * .6 + (hit / terms.length) * .4) : d.score, hit };
  }).filter(d => !terms.length || d.hit).sort((a, b) => b.score - a.score);
}

/* ============================ UI HELPERS ============================ */
const pill = (txt, k) => `<span class="pill p-${k}">${esc(txt)}</span>`;
const riskPill = r => pill(r + ' risk', { low: 'ok', medium: 'warn', high: 'bad' }[r]);
const stPill = s => ({ idle: pill('Idle', 'idle'), processing: pill('Processing', 'info'), completed: pill('Completed', 'ok'), failed: pill('Failed', 'bad'), waiting: pill('Waiting for approval', 'warn') }[s]);
const chips = a => `<div class="chips">${a.map(x => `<span class="chip">${esc(x)}</span>`).join('')}</div>`;
const head = (t, d, extra = '') => `<div class="head"><div><h1>${t}</h1><p>${d}</p></div>${extra}</div>`;
function toast(m) { const t = $('#toast'); t.textContent = m; t.classList.add('show'); clearTimeout(toast.h); toast.h = setTimeout(() => t.classList.remove('show'), 2200); }
function modal(html) { const m = $('#modal'); m.innerHTML = `<div class="modal" role="dialog" aria-modal="true">${html}</div>`; m.hidden = false; const f = m.querySelector('input,textarea,button'); f && f.focus(); }
function closeModal() { $('#modal').hidden = true; }
const toolsOf = () => state.tools[state.pid];

/* Relationship graph: entities on a ring, edges labelled */
function graph(entities, rels) {
  const cx = 190, cy = 120, R = 92, pos = {};
  entities.forEach((e, i) => { const a = (i / entities.length) * 6.283 - 1.57; pos[e] = [cx + R * 1.5 * Math.cos(a), cy + R * Math.sin(a)]; });
  const lines = rels.filter(r => pos[r[0]] && pos[r[1]]).map(([a, b, l]) => {
    const [x1, y1] = pos[a], [x2, y2] = pos[b];
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--edge)" stroke-width="1.5"/><text x="${(x1 + x2) / 2}" y="${(y1 + y2) / 2 - 3}" font-size="9" fill="var(--mut)" text-anchor="middle">${esc(l)}</text>`;
  }).join('');
  const nodes = entities.map(e => `<g><rect x="${pos[e][0] - 40}" y="${pos[e][1] - 12}" width="80" height="24" rx="12" fill="var(--acc-s)" stroke="var(--acc)"/><text x="${pos[e][0]}" y="${pos[e][1] + 4}" font-size="10.5" text-anchor="middle" fill="var(--ink)">${esc(e)}</text></g>`).join('');
  return `<svg viewBox="0 0 380 240" role="img" aria-label="Entity relationship graph" style="width:100%;height:auto">${lines}${nodes}</svg>`;
}

/* ============================ VIEWS ============================ */
const V = {};

V.req = () => {
  const p = P(), h = state.history[state.pid];
  const status = state.analyzing
    ? `<div class="card"><h3><span class="spinner"></span> ${esc(state.analyzing)}</h3></div>`
    : state.analyzed[state.pid]
      ? `<div class="card row sp"><div><h3>Project ready: ${esc(p.name)}</h3><p class="mut sm">Requirement analyzed. ${esc(p.impact)}</p></div><button class="btn pri" data-act="goto" data-v="request">Review request</button></div>`
      : `<div class="empty">No requirement submitted for this project yet.</div>`;
  return `<div class="hero"><p class="eyebrow">Loom</p><h1>What do you want to get done?</h1><p class="mut">Describe a system to build or a change to handle. Loom adapts its knowledge, tools, and agents to the domain.</p></div>
  <form class="composer" data-form="req"><label class="sr" for="reqText">Requirement</label>
    <textarea id="reqText" placeholder="Describe your requirement in plain language…">${esc(state.draft)}</textarea>
    <div class="row sp"><span class="mut sm">Simulated analysis. No model is called in this prototype.</span><button class="btn pri" ${state.analyzing ? 'disabled' : ''}>Analyze requirement</button></div></form>
  ${state.error ? `<div class="appr" style="max-width:820px;margin:0 auto 16px;background:var(--red-s);border-color:var(--red-line)"><b>Couldn’t map this to a domain.</b> Try naming modules or entities, for example “student management and fee tracking”, or pick an example below.</div>` : ''}
  <div style="max-width:820px;margin:0 auto" class="grid">
    <div><h3 style="margin-bottom:8px">Try an example</h3><div class="chips">${EXAMPLES.map((e, i) => `<button class="chip" data-act="example" data-i="${i}">${esc(e.length > 70 ? e.slice(0, 68) + '…' : e)}</button>`).join('')}</div></div>
    ${status}
    <div class="card"><h2>Previous requirements</h2>${h.length ? `<ul class="plain">${h.map(x => `<li><span>${esc(x.text)}</span><span class="mut sm">${x.at}</span></li>`).join('')}</ul>` : '<p class="mut sm">Nothing submitted yet.</p>'}</div></div>`;
};

V.request = () => {
  const p = P(), r = run();
  if (!state.analyzed[state.pid]) return emptyState('No requirement yet', 'Submit a requirement first to generate a request.', 'req', 'Go to Requirement');
  const pend = r.status === 'waiting' ? p.actions[r.steps[r.idx].ap] : null;
  const isRunning = r.status === 'running' || r.status === 'waiting';
  const isDone = r.status === 'done';

  const apprCards = r.appr.length ? r.appr.map(a => `
    <div class="card" style="border-left:4px solid ${a.ok ? 'var(--grn-line)' : 'var(--red-line)'}">
      <div class="row sp">
        <div><h3>${esc(a.label)}</h3><span class="mut sm">${a.at}</span></div>
        <span class="pill ${a.ok ? 'p-ok' : 'p-bad'}">${a.ok ? '&#10003; Approved' : '&#10007; Rejected'}</span>
      </div>
    </div>`).join('') : '';

  const pendBanner = pend ? `
    <div class="appr" style="margin-bottom:16px">
      <div class="row sp" style="flex-wrap:wrap;gap:12px">
        <div>
          <b style="font-size:15px">&#9203; Approval needed</b>
          <div style="margin:4px 0 2px">${esc(pend.label)}</div>
          <div class="sm mut">${esc(pend.why)} &middot; tool <code>${pend.tool}</code></div>
        </div>
        <div class="row" style="gap:8px">
          <button class="btn" data-act="reject" style="border-color:var(--red-line);color:var(--red)">Reject</button>
          <button class="btn pri" data-act="approve">Approve</button>
        </div>
      </div>
    </div>` : '';

  const changesList = p.actions.map((a, i) => {
    const res = r.res[i];
    const statusBadge = !res
      ? `<span class="pill p-idle">Pending</span>`
      : res.s === 'verified' ? `<span class="pill p-ok">&#10003; Done</span>`
      : res.s === 'failed' ? `<span class="pill p-bad">Failed</span>`
      : `<span class="pill p-idle">Skipped</span>`;
    return `<div class="card" style="margin-bottom:8px">
      <div class="row sp">
        <div style="flex:1">
          <div class="row" style="gap:8px;flex-wrap:wrap">
            <h3>${esc(a.label)}</h3>
            ${a.approval ? '<span class="pill p-warn">Needs approval</span>' : ''}
          </div>
          <div class="sm mut" style="margin-top:3px">Tool: <code>${a.tool}</code> &middot; Expected: ${esc(a.expected)}</div>
        </div>
        ${statusBadge}
      </div>
    </div>`;
  }).join('');

  return head('Request', 'Review the planned changes and approve or reject actions that require sign-off.',
    `<button class="btn pri" data-act="run" ${isRunning ? 'disabled' : ''}>${isDone ? 'Replay workflow' : 'Run workflow'}</button>`) +
    pendBanner +
    `<div class="grid g2">
      <div>
        <h2 style="margin-bottom:12px">Planned changes</h2>
        ${changesList}
      </div>
      <div>
        <div class="card" style="margin-bottom:14px">
          <h2 style="margin-bottom:10px">Approval queue</h2>
          ${r.status === 'idle'
            ? '<p class="mut sm">Run the workflow to begin processing approvals.</p>'
            : apprCards || (isDone ? '<p class="mut sm">All approvals processed.</p>' : '<p class="mut sm">No approvals recorded yet.</p>')}
        </div>
        <div class="card">
          <h2 style="margin-bottom:10px">Impact summary</h2>
          <p class="sm">${esc(p.impact)}</p>
          <div style="margin-top:12px">
            ${p.reqs.map(req => `<div style="padding:5px 0;border-top:1px solid var(--line);font-size:13px">${esc(req)}</div>`).join('')}
          </div>
        </div>
      </div>
    </div>`;
};

V.output = () => {
  const r = run(), p = P();
  if (r.status !== 'done') return emptyState('No output yet', r.status === 'idle' ? 'Run the workflow from the Request tab to generate output.' : 'The workflow is still running...', 'request', 'Go to Request');
  const ok = r.res.filter(x => x.s === 'verified').length, bad = r.res.filter(x => x.s === 'failed').length, skipped = r.res.filter(x => x.s === 'skipped').length;
  const rate = Math.round(ok / p.actions.length * 100);
  const final = bad ? pill('Needs attention', 'bad') : r.res.some(x => x.s === 'skipped') ? pill('Partially complete', 'warn') : pill('All verified', 'ok');
  return head('Output', 'Results of the executed workflow — expected vs actual state for each action.') +
    `<div class="grid g3" style="margin-bottom:16px">
      <div class="card"><span class="mut sm">Success rate</span><div class="stat">${rate}%</div></div>
      <div class="card"><span class="mut sm">Verified / Failed / Skipped</span><div class="stat">${ok} / ${bad} / ${skipped}</div></div>
      <div class="card"><span class="mut sm">Final status</span><div style="margin-top:8px">${final}</div></div>
    </div>
    <div class="grid" style="margin-bottom:16px">
      ${p.actions.map((a, i) => { const x = r.res[i]; return `<div class="card">
        <div class="row sp">
          <div><h3>${esc(a.label)}</h3><code class="mut">${a.tool}</code></div>
          ${x.s === 'verified' ? pill('Verified &#10003;', 'ok') : x.s === 'failed' ? pill('Failed', 'bad') : pill('Skipped', 'idle')}
        </div>
        <dl class="kv sm" style="margin:10px 0 0"><dt>Expected</dt><dd>${esc(a.expected)}</dd><dt>Actual</dt><dd>${esc(x.actual)}</dd></dl>
        ${x.s === 'failed' ? `<div class="appr" style="margin:10px 0 0"><b>Failure:</b> ${esc(x.actual)}. Retrying reuses the same idempotency key — nothing runs twice.<div style="margin-top:8px"><button class="btn pri" data-act="retry" data-i="${i}">Retry action</button></div></div>` : ''}
      </div>`; }).join('')}
    </div>
    <div class="grid g2">
      <div class="card"><h2>Approval history</h2>${r.appr.length ? `<ul class="plain">${r.appr.map(a => `<li><span>${esc(a.label)}</span>${pill(a.ok ? 'Approved' : 'Rejected', a.ok ? 'ok' : 'bad')}</li>`).join('')}</ul>` : '<p class="mut sm">No approvals were required.</p>'}</div>
      <div class="card"><h2>Audit log</h2><div class="log">${r.audit.map(a => `<div><time>${a.at}</time>${esc(a.t)}</div>`).join('')}</div></div>
    </div>`;
};


function emptyState(t, d, to, label) { return `<div class="empty" style="margin-top:40px"><h2>${t}</h2><p>${d}</p><button class="btn pri" data-act="goto" data-v="${to}">${label}</button></div>`; }

/* ============================ SHELL RENDER ============================ */
function renderShell() {
  const r = run(), done = { req: state.analyzed[state.pid], request: r.status === 'running' || r.status === 'waiting' || r.status === 'done', output: r.status === 'done' };
  $('#tabs').innerHTML = TABS.map(([k, l], i) => `<button class="tab ${state.tab === k ? 'on' : ''} ${done[k] ? 'done' : ''}" data-act="goto" data-v="${k}" ${state.tab === k ? 'aria-current="page"' : ''}><span class="n">${done[k] ? '✓' : i + 1}</span>${l}</button>`).join('');
  const p = P();
  $('#sideContent').innerHTML = `<h4>Project</h4><div class="side-item"><b>${esc(p.short)}</b><small>${esc(p.domain)}</small></div>
    <h4>Saved requirements</h4>${state.history[state.pid].map(h => `<button class="side-item" data-act="goto" data-v="req">${esc(h.text.slice(0, 44))}…</button>`).join('') || '<div class="side-item mut">None yet</div>'}
    <h4>Knowledge sources</h4>${p.docs.slice(0, 4).map(d => `<button class="side-item" data-act="goto" data-v="kn">${esc(d.src.split('/').pop())}</button>`).join('')}
    <h4>Recent executions</h4><div class="side-item">${r.status === 'done' ? `Last run ${r.audit[0].at}<small>${r.res.filter(x => x.s === 'verified').length}/${p.actions.length} verified</small>` : '<span class="mut">No runs yet</span>'}</div>`;
}
function renderView() { $('#view').innerHTML = V[state.tab](); }
function refresh() { renderShell(); renderView(); }
function go(tab) { state.tab = tab; refresh(); window.scrollTo(0, 0); }

/* ============================ ACTIONS & EVENTS ============================ */
function submitRequirement(text) {
  state.draft = text; state.error = '';
  const id = matchProject(text);
  if (!text.trim() || !id) { state.error = 'x'; refresh(); return; }
  state.pid = id; state.draft = '';
  const stages = ['Reading requirement…', 'Identifying domain…', 'Extracting entities and workflows…', 'Preparing knowledge and tools…'];
  stages.forEach((s, i) => setTimeout(() => { state.analyzing = s; refresh(); }, i * 700));
  setTimeout(() => {
    state.analyzing = null; state.analyzed[id] = true;
    if (!state.history[id].some(h => h.text === text)) state.history[id].unshift({ text, at: now() });
    toast('Requirement analyzed'); refresh();
  }, stages.length * 700);
}
function toolForm(t) {
  const x = t || { name: '', desc: '', risk: 'low', perm: 'write', handler: 'handlers/new_tool.js', params: S('input:string') };
  return `<h2>${t ? 'Edit tool' : 'Add tool'}</h2><form data-form="tool" data-orig="${t ? t.name : ''}">
  <label for="f-name">Name</label><input type="text" id="f-name" value="${esc(x.name)}" ${t ? 'readonly' : ''} placeholder="snake_case_name">
  <label for="f-desc">Description</label><input type="text" id="f-desc" value="${esc(x.desc)}">
  <div class="row"><div style="flex:1"><label for="f-risk">Risk</label><select class="f" id="f-risk">${['low', 'medium', 'high'].map(r => `<option ${x.risk === r ? 'selected' : ''}>${r}</option>`).join('')}</select></div>
  <div style="flex:1"><label for="f-perm">Permission</label><select class="f" id="f-perm">${['read', 'write', 'draft'].map(r => `<option ${x.perm === r ? 'selected' : ''}>${r}</option>`).join('')}</select></div></div>
  <label for="f-handler">Handler</label><input type="text" id="f-handler" value="${esc(x.handler)}">
  <label for="f-schema">JSON parameter schema</label><textarea id="f-schema" style="font-family:ui-monospace,monospace;font-size:12px;min-height:120px">${esc(JSON.stringify(x.params, null, 2))}</textarea>
  <p class="sm" id="f-err" style="color:var(--red);min-height:20px"></p>
  <div class="row" style="justify-content:flex-end"><button type="button" class="btn" data-act="close">Cancel</button><button class="btn pri">Save tool</button></div></form>`;
}
const findTool = n => toolsOf().find(t => t.name === n);

const shell = $('.shell'), sidebarToggle = $('#sidebarToggle'), sideBackdrop = $('#sideBackdrop');
let mobileSidebar = window.matchMedia('(max-width:900px)').matches;
let sidebarExpanded = !mobileSidebar;
function syncSidebar() {
  const mobile = window.matchMedia('(max-width:900px)').matches;
  if (mobile !== mobileSidebar) { mobileSidebar = mobile; sidebarExpanded = !mobile; }
  shell.classList.toggle('sidebar-open', mobileSidebar && sidebarExpanded);
  shell.classList.toggle('sidebar-collapsed', !mobileSidebar && !sidebarExpanded);
  sideBackdrop.hidden = !(mobileSidebar && sidebarExpanded);
  sidebarToggle.setAttribute('aria-expanded', String(sidebarExpanded));
  sidebarToggle.setAttribute('aria-label', `${mobileSidebar ? (sidebarExpanded ? 'Close' : 'Open') : (sidebarExpanded ? 'Collapse' : 'Expand')} sidebar`);
}
function setSidebarExpanded(expanded) { sidebarExpanded = expanded; syncSidebar(); }
sidebarToggle.addEventListener('click', () => setSidebarExpanded(!sidebarExpanded));
sideBackdrop.addEventListener('click', () => setSidebarExpanded(false));
window.addEventListener('resize', syncSidebar);
syncSidebar();

document.addEventListener('click', e => {
  if (e.target.id === 'modal') return closeModal();
  const b = e.target.closest('[data-act]'); if (!b) return;
  if (mobileSidebar && b.closest('#sideContent')) setSidebarExpanded(false);
  const d = b.dataset, t = d.n && findTool(d.n);
  switch (d.act) {
    case 'goto': go(d.v); break;
    case 'close': closeModal(); break;
    case 'example': state.draft = EXAMPLES[d.i]; state.error = ''; refresh(); $('#reqText').focus(); break;
    case 'dfilter': state.dfilter = d.v; refresh(); break;
    case 'register': t.registered = t.enabled = true; toast(`${t.name} registered`); refresh(); break;
    case 'request': toast(`Capability request for ${t.name} logged`); break;
    case 'toggle': t.enabled = !t.enabled; toast(`${t.name} ${t.enabled ? 'enabled' : 'disabled'}`); refresh(); break;
    case 'inspect': modal(`<div class="row sp"><h2><code>${t.name}</code></h2>${riskPill(t.risk)}</div><p class="mut" style="margin:6px 0 12px">${esc(t.desc)}</p>
      <dl class="kv sm"><dt>Category</dt><dd>${t.cat}</dd><dt>Scope</dt><dd>${t.scope}</dd><dt>Availability</dt><dd>${t.status}</dd><dt>Permission</dt><dd>${t.perm}</dd><dt>Handler</dt><dd><code>${t.handler}</code></dd></dl>
      <h3 style="margin:14px 0 6px">Input parameters</h3><pre>${esc(JSON.stringify(t.params, null, 2))}</pre><div class="row" style="justify-content:flex-end;margin-top:14px"><button class="btn" data-act="close">Close</button></div>`); break;
    case 'addTool': modal(toolForm()); break;
    case 'editTool': modal(toolForm(t)); break;
    case 'editReqs': modal(`<h2>Edit functional requirements</h2><form data-form="reqs"><label for="rt">One requirement per line</label><textarea id="rt" style="min-height:180px">${esc(state.editedReqs[state.pid].join('\n'))}</textarea><div class="row" style="justify-content:flex-end;margin-top:12px"><button type="button" class="btn" data-act="close">Cancel</button><button class="btn pri">Save changes</button></div></form>`); break;
    case 'agent': state.selAgent = d.k; renderView(); break;
    case 'run': startRun(); break;
    case 'approve': decide(true); break;
    case 'reject': decide(false); break;
    case 'retry': retryAction(+d.i); break;
  }
});
document.addEventListener('submit', e => {
  const f = e.target.closest('[data-form]'); if (!f) return; e.preventDefault();
  const k = f.dataset.form;
  if (k === 'req') submitRequirement($('#reqText').value);
  if (k === 'kq') return;
  if (k === 'reqs') { state.editedReqs[state.pid] = $('#rt').value.split('\n').map(s => s.trim()).filter(Boolean); closeModal(); toast('Requirements updated'); refresh(); }
  if (k === 'tool') {
    let schema; const name = $('#f-name').value.trim(), err = $('#f-err');
    try { schema = JSON.parse($('#f-schema').value); } catch { err.textContent = 'The parameter schema isn’t valid JSON. Check commas and quotes.'; return; }
    if (!/^[a-z][a-z0-9_]*$/.test(name)) { err.textContent = 'Use a snake_case name, for example “create_invoice”.'; return; }
    const orig = f.dataset.orig, ex = findTool(name);
    if (!orig && ex) { err.textContent = `A tool named ${name} already exists.`; return; }
    const vals = { desc: $('#f-desc').value, risk: $('#f-risk').value, perm: $('#f-perm').value, handler: $('#f-handler').value, params: schema };
    if (orig) Object.assign(ex, vals); else toolsOf().push({ name, cat: 'Custom', scope: 'domain', status: 'available', registered: true, enabled: true, ...vals });
    closeModal(); toast(orig ? 'Tool updated' : 'Tool added'); refresh();
  }
});
document.addEventListener('input', e => {
  if (e.target.id === 'kq') { state.kq = e.target.value; const p = $('#view .split'); renderView(); const i = $('#kq'); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }
  if (e.target.id === 'rq') { state.rq = e.target.value; renderView(); const i = $('#rq'); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }
  if (e.target.id === 'reqText') state.draft = e.target.value;
});
document.addEventListener('change', e => {
  if (e.target.id === 'rrisk') { state.rrisk = e.target.value; renderView(); }
  if (e.target.id === 'upload' && e.target.files[0]) {
    const f = e.target.files[0]; P().docs.unshift({ t: f.name, src: `uploads/${f.name}`, type: 'Document', score: .7, why: 'Uploaded just now. Indexing is simulated; no embeddings were created.' });
    toast('Document added (simulated indexing)'); refresh();
  }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeModal();
    if (mobileSidebar && sidebarExpanded) setSidebarExpanded(false);
  }
});

$('#themeToggle').addEventListener('click', e => {
  const dark = document.documentElement.dataset.theme !== 'dark';
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  e.currentTarget.setAttribute('aria-pressed', String(dark));
  e.currentTarget.setAttribute('aria-label', `Switch to ${dark ? 'light' : 'dark'} mode`);
  e.currentTarget.title = `Switch to ${dark ? 'light' : 'dark'} mode`;
  e.currentTarget.querySelector('.theme-icon').textContent = dark ? '☾︎' : '☀︎';
});

refresh();
