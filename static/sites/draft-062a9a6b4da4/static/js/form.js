"use strict";

const CHAPTERS = [
  {color:'#FFE066',sfx:'KAPOW!',avatar:'🦸',title:'Hero Profile',sub:'Your origin story starts here',fields:[
    {type:'two-col',fields:[{type:'text',key:'name',label:'Your Name',hint:'e.g. Alex Chen'},{type:'text',key:'sid',label:'Student ID',hint:'e.g. S12345678'}]},
    {type:'two-col',fields:[{type:'text',key:'prog',label:'Programme',hint:'e.g. Computer Science'},{type:'text',key:'dur',label:'Duration',hint:'e.g. Jan-May 2025'}]},
    {type:'text',key:'company',label:'Department / Company',hint:'e.g. Stark Industries'},
    {type:'textarea',key:'origin',label:'The Origin Story',hint:'When I first walked through those doors...',rows:4},
    {type:'textarea',key:'superpower',label:'Superpower I Wanted',hint:'The skill I was most determined to build...',rows:3}
  ]},
  {color:'#C8F7C5',sfx:'ZAP!',avatar:'🧠',title:'Learn to Learn',sub:'Level up! What new powers did you gain?',fields:[
    {type:'textarea',key:'skill',label:'Skill Acquired',hint:'e.g. I had no idea what React was...',rows:3},
    {type:'checkboxes',key:'strategy',label:'Learning Strategy',options:['Self-study','Ask mentor','AI tools','Trial & error','Peer learning','Video courses','Documentation','Workshops']},
    {type:'rating',key:'conf_b',label:'Confidence BEFORE (1-5)'},
    {type:'rating',key:'conf_a',label:'Confidence AFTER (1-5)'}
  ]},
  {color:'#FFCFDF',sfx:'POW!',avatar:'💡',title:'Learn to Think',sub:'How did you crack the case?',fields:[
    {type:'textarea',key:'problem',label:'The Problem',hint:'e.g. The production DB was slow...',rows:3},
    {type:'textarea',key:'thinking',label:'My Detective Process',hint:'e.g. I broke it into smaller parts...',rows:3},
    {type:'textarea',key:'outcome',label:'The Outcome',hint:'e.g. Reduced query time by 70%...',rows:2},
    {type:'checkboxes',key:'think_mode',label:'Thinking Mode',options:['Analytical','Creative','Systems thinking','Critical thinking','Design thinking','First principles']}
  ]},
  {color:'#D0E8FF',sfx:'WHAM!',avatar:'🤝',title:'Learn to Collaborate',sub:'Every hero needs a sidekick',fields:[
    {type:'two-col',fields:[{type:'text',key:'team',label:'The Squad',hint:'e.g. 3 engineers, 1 PM'},{type:'text',key:'team_role',label:'My Role',hint:'e.g. Frontend Dev'}]},
    {type:'textarea',key:'collab_win',label:'Squad Win',hint:'e.g. Organised a whiteboard session...',rows:3},
    {type:'textarea',key:'collab_fail',label:'Squad Challenge',hint:'e.g. Differing opinions...',rows:3},
    {type:'checkboxes',key:'role_style',label:'My Role Style',options:['Contributor','Coordinator','Bridge builder','Communicator','Documenter','Leader']}
  ]},
  {color:'#FFF0CC',sfx:'BOOM!',avatar:'⚖️',title:'Learn to Regulate',sub:'Heroes manage their emotions too',fields:[
    {type:'textarea',key:'setback',label:'Biggest Setback & Comeback',hint:'e.g. My first demo crashed...',rows:3},
    {type:'textarea',key:'time_mgmt',label:'Time Management Powers',hint:'e.g. Weekly task board...',rows:3},
    {type:'checkboxes',key:'wellbeing',label:'Wellbeing Toolkit',options:['Mindfulness','Exercise','Journaling','Talking to friends','Hobbies','Rest']},
    {type:'checkboxes',key:'stress',label:'Stress Level',options:['High','Medium-high','Medium','Low-medium','Chill']}
  ]},
  {color:'#E8D5FF',sfx:'BLAM!',avatar:'🛠️',title:'The Arsenal',sub:'Every hero has gadgets',fields:[
    {type:'checkboxes',key:'t_ai',label:'AI Tools',options:['ChatGPT','Claude','Gemini','Copilot','Other']},
    {type:'checkboxes',key:'t_collab',label:'Work Tools',options:['Excel','Word','Power BI','Notion','Figma','Slack','Jira','Other']},
    {type:'textarea',key:'best_tool',label:'Tool I Am Most Proud Of',hint:"What can you do now that you couldn't before?",rows:3}
  ]},
  {color:'#C5F7EB',sfx:'ZING!',avatar:'📅',title:'Journey Timeline',sub:'3 legendary moments',fields:[
    {type:'text',key:'m1t',label:'Mission 1 - Start',hint:'e.g. The Great Code Review'},
    {type:'textarea',key:'m1b',label:'What went down',hint:'',rows:2},
    {type:'text',key:'m2t',label:'Mission 2 - Mid',hint:'e.g. The Grand Presentation'},
    {type:'textarea',key:'m2b',label:'What went down',hint:'',rows:2},
    {type:'text',key:'m3t',label:'Mission 3 - End',hint:'e.g. Feature Ship Day'},
    {type:'textarea',key:'m3b',label:'What went down',hint:'',rows:2}
  ]},
  {color:'#FFE4CC',sfx:'CRASH!',avatar:'💥',title:'The Impact',sub:'How did you move the needle?',fields:[
    {type:'textarea',key:'contribution',label:'What I Delivered',hint:'Features, reports, campaigns...',rows:3},
    {type:'textarea',key:'value',label:'Value Created',hint:'Saved X hours, improved Y by Z%...',rows:3},
    {type:'textarea',key:'school_back',label:'Knowledge to Share',hint:'How will you share this with peers?',rows:3}
  ]},
  {color:'#FFD6D6',sfx:'WHOOSH!',avatar:'🌟',title:'Mentor Spotlight',sub:'Shoutout to your Yoda',fields:[
    {type:'two-col',fields:[{type:'text',key:'mentor_name',label:'Mentor Name',hint:'e.g. Dr Jane Wong'},{type:'text',key:'mentor_role',label:'Their Role',hint:'e.g. Senior Engineer'}]},
    {type:'textarea',key:'mentor_lesson',label:'Wisdom That Hit Different',hint:'e.g. Always read the docs first...',rows:3},
    {type:'rating',key:'mentor_rating',label:'Mentor Power Level (1-5)'}
  ]},
  {color:'#D5F0FF',sfx:'NEXT!',avatar:'🚀',title:"What's Next",sub:'The sequel is already written',fields:[
    {type:'textarea',key:'takeaways',label:'Top 3 Power-ups Unlocked',hint:'1.\n2.\n3.',rows:4},
    {type:'textarea',key:'goals',label:'Next Arc Goals',hint:'What will you do differently?',rows:3},
    {type:'textarea',key:'advice',label:'Message to the Next Hero',hint:'What would you tell the next intern?',rows:3}
  ]}
];

let cur=0;
const D={},C={},R={};
function sv(k,v){D[k]=v;}
function gc(k){return C[k]||[];}
function tc(k,v){if(!C[k])C[k]=[];const i=C[k].indexOf(v);i>-1?C[k].splice(i,1):C[k].push(v);}

function renderField(f){
  if(f.type==='two-col')return `<div class="two-col">${f.fields.map(renderField).join('')}</div>`;
  if(f.type==='text')return `<div class="field-block"><div class="field-label">${f.label}</div><input type="text" data-key="${f.key}" value="${(D[f.key]||'').replace(/"/g,'&quot;')}" placeholder="${f.hint||''}"></div>`;
  if(f.type==='textarea')return `<div class="field-block"><div class="field-label">${f.label}</div>${f.hint?`<div class="field-hint">${f.hint}</div>`:''}<textarea data-key="${f.key}" rows="${f.rows||3}">${D[f.key]||''}</textarea></div>`;
  if(f.type==='checkboxes'){
    const sel=gc(f.key);
    return `<div class="field-block"><div class="field-label">${f.label}</div><div class="cb-group">${f.options.map(o=>`<span class="cb-pill${sel.includes(o)?' on':''}" data-grp="${f.key}" data-val="${o}"><span class="cb-check">${sel.includes(o)?'<svg width="9" height="9" viewBox="0 0 9 9"><path d="M1.5 4.5l2 2L7.5 2" stroke="#fffef7" stroke-width="1.8" stroke-linecap="round" fill="none"/></svg>':''}</span>${o}</span>`).join('')}</div></div>`;
  }
  if(f.type==='rating'){
    const v=R[f.key]||0;
    return `<div class="field-block"><div class="field-label">${f.label}</div><div class="star-row">${[1,2,3,4,5].map(i=>`<span class="star${i<=v?' lit':''}" data-rk="${f.key}" data-rv="${i}">★</span>`).join('')}</div></div>`;
  }
  return '';
}

function dots(){return CHAPTERS.map((_,i)=>`<div class="cdot${i<cur?' done':i===cur?' active':''}">${i<cur?'✓':i+1}</div>`).join('');}

function render(){
  const ch=CHAPTERS[cur];
  const pct=Math.round(cur/CHAPTERS.length*100);
  const isLast=cur===CHAPTERS.length-1;
  document.getElementById('app').innerHTML=`
    <div class="comic-header" style="background:${ch.color}">
      <div class="logo-group">
        <img src="/static/images/logo.png" alt="Logo" class="logo-img" onerror="this.style.display='none'">
        <div class="comic-logo">INTERN STAR<p>Office of Academics</p></div>
      </div>
      <div class="issue-badge">ISSUE #${String(cur+1).padStart(3,'0')}</div>
    </div>
    <div class="progress-section">
      <div class="progress-label"><span>MISSION PROGRESS</span><span>${cur+1} / ${CHAPTERS.length} chapters</span></div>
      <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div><div class="progress-pct">${pct}%</div></div>
      <div class="chapter-dots">${dots()}</div>
    </div>
    <div class="panel-body">
      <div class="bubble">
        <div class="hero-avatar">${ch.avatar}</div>
        <div class="bubble-text">
          <div class="chapter-num">CHAPTER ${cur+1} — <span class="sfx">${ch.sfx}</span></div>
          <div class="chapter-title-big">${ch.title}</div>
          <div class="chapter-sub">${ch.sub}</div>
        </div>
      </div>
      ${ch.fields.map(renderField).join('')}
      <div class="nav-row">
        <button class="nav-btn ghost" id="btn-back" ${cur===0?'style="visibility:hidden"':''}>← BACK</button>
        <button class="nav-btn ${isLast?'final':'primary'}" id="btn-next">${isLast?'MISSION COMPLETE! →':'NEXT CHAPTER →'}</button>
      </div>
    </div>`;
  bind();
}

function bind(){
  document.querySelectorAll('input[type=text]').forEach(el=>el.addEventListener('input',e=>sv(e.target.dataset.key,e.target.value)));
  document.querySelectorAll('textarea').forEach(el=>el.addEventListener('input',e=>sv(e.target.dataset.key,e.target.value)));
  document.querySelectorAll('[data-grp]').forEach(el=>el.addEventListener('click',()=>{tc(el.dataset.grp,el.dataset.val);render();}));
  document.querySelectorAll('[data-rk]').forEach(el=>el.addEventListener('click',()=>{R[el.dataset.rk]=parseInt(el.dataset.rv);render();}));
  document.getElementById('btn-back').addEventListener('click',()=>{cur--;render();});
  document.getElementById('btn-next').addEventListener('click',()=>{
    if(cur<CHAPTERS.length-1){cur++;render();}
    else submitForm();
  });
}

// ── SUBMIT TO FLASK /submit → MONGODB ────────────────────────────────────────
async function submitForm(){
  const payload={
    submitted_at: new Date().toISOString(),
    ...D,
    ...Object.fromEntries(Object.entries(C).map(([k,v])=>[k,v.join(', ')])),
    ...Object.fromEntries(Object.entries(R).map(([k,v])=>[k,String(v)]))
  };

  showOverlay(true);

  try {
    const res = await fetch('/submit',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    showOverlay(false);
    if(json.success){
      showToast('✅ Saved successfully!',false);
    } else {
      showToast('⚠️ Error: '+json.error,true);
    }
  } catch(err){
    showOverlay(false);
    showToast('⚠️ Network error',true);
  }
  renderSummary();
}

function showOverlay(show){
  let el=document.getElementById('saving-overlay');
  if(show){
    if(!el){
      el=document.createElement('div');
      el.id='saving-overlay';el.className='saving-overlay';
      el.innerHTML='<div class="saving-box"><span>⚡</span>SAVING...</div>';
      document.body.appendChild(el);
    }
  } else { if(el)el.remove(); }
}

function showToast(msg,isError=false){
  const t=document.getElementById('toast');
  t.textContent=msg;t.className='toast show'+(isError?' error':'');
  setTimeout(()=>{t.className='toast';},4000);
}

const CH_COLORS=['#FFE066','#C8F7C5','#FFCFDF','#D0E8FF','#FFF0CC','#E8D5FF','#C5F7EB','#FFE4CC','#FFD6D6','#D5F0FF'];
function v(k){return D[k]||'—';}
function cc(k){return(C[k]||[]).join(', ')||'—';}
function st(k){return'★'.repeat(R[k]||0)+'☆'.repeat(5-(R[k]||0));}
function sr(label,val){return `<div class="sum-row"><span class="sum-key">${label}</span><span class="sum-val">${val}</span></div>`;}

const SUMMARIES=[
  ()=>sr('Name',v('name'))+sr('Student ID',v('sid'))+sr('Programme',v('prog'))+sr('Duration',v('dur'))+sr('Department',v('company'))+sr('Origin Story',v('origin'))+sr('Superpower Goal',v('superpower')),
  ()=>sr('Skill Acquired',v('skill'))+sr('Strategies',cc('strategy'))+sr('Confidence Before',st('conf_b'))+sr('Confidence After',st('conf_a')),
  ()=>sr('Problem',v('problem'))+sr('Thinking Process',v('thinking'))+sr('Outcome',v('outcome'))+sr('Thinking Mode',cc('think_mode')),
  ()=>sr('Team',v('team'))+sr('My Role',v('team_role'))+sr('Collab Win',v('collab_win'))+sr('Collab Challenge',v('collab_fail'))+sr('Role Style',cc('role_style')),
  ()=>sr('Setback',v('setback'))+sr('Time Management',v('time_mgmt'))+sr('Wellbeing',cc('wellbeing'))+sr('Stress Level',cc('stress')),
  ()=>sr('AI Tools',cc('t_ai'))+sr('Work Tools',cc('t_collab'))+sr('Best Tool',v('best_tool')),
  ()=>sr('Mission 1',v('m1t'))+sr('',v('m1b'))+sr('Mission 2',v('m2t'))+sr('',v('m2b'))+sr('Mission 3',v('m3t'))+sr('',v('m3b')),
  ()=>sr('Delivered',v('contribution'))+sr('Value Created',v('value'))+sr('Knowledge',v('school_back')),
  ()=>sr('Mentor',v('mentor_name'))+sr('Their Role',v('mentor_role'))+sr('Lesson',v('mentor_lesson'))+sr('Rating',st('mentor_rating')),
  ()=>sr('Top 3 Power-ups',v('takeaways'))+sr('Goals',v('goals'))+sr('Advice',v('advice'))
];

function renderSummary(){
  const name=(D.name||'Hero').toUpperCase().split(' ')[0];
  const chapters=CHAPTERS.map((ch,i)=>`
    <div class="sum-chapter">
      <div class="sum-ch-header" style="background:${CH_COLORS[i]}">
        <span>${ch.avatar}</span><span>CH.${i+1} — ${ch.title.toUpperCase()}</span>
      </div>
      <div class="sum-ch-body">${SUMMARIES[i]()}</div>
    </div>`).join('');

  document.getElementById('app').innerHTML=`
    <div class="comic-header" style="background:var(--green)">
      <div class="logo-group">
        <img src="/static/images/logo.png" alt="Logo" class="logo-img" onerror="this.style.display='none'">
        <div class="comic-logo">INTERN STAR<p>Office of Academics</p></div>
      </div>
      <div class="issue-badge">COMPLETE!</div>
    </div>
    <div class="summary-header">
      <div class="summary-title">MISSION COMPLETE, ${name}!</div>
      <div style="font-size:14px;color:#1a1a2e;margin-top:4px;font-style:italic">All 10 chapters saved!</div>
    </div>
    <div class="summary-panel">
      ${chapters}
      <button class="dl-btn" id="dl-btn">⬇ DOWNLOAD SUMMARY (.TXT)</button>
      <button class="restart-btn" id="restart-btn">Start a new mission ↺</button>
    </div>`;

  document.getElementById('dl-btn').addEventListener('click',download);
  document.getElementById('restart-btn').addEventListener('click',()=>{
    cur=0;
    Object.keys(D).forEach(k=>delete D[k]);
    Object.keys(C).forEach(k=>delete C[k]);
    Object.keys(R).forEach(k=>delete R[k]);
    render();
  });
}

function download(){
  const lines=[
    'INTERN STAR — MISSION SUMMARY','='.repeat(50),
    `Generated: ${new Date().toLocaleDateString()}`,'',
    'HERO PROFILE','-'.repeat(40),
    `Name: ${v('name')}`,`Student ID: ${v('sid')}`,`Programme: ${v('prog')}`,
    `Duration: ${v('dur')}`,`Department: ${v('company')}`,
    `Origin Story:\n${v('origin')}`,`Superpower Goal:\n${v('superpower')}`,'',
    'LEARN TO LEARN','-'.repeat(40),
    `Skill:\n${v('skill')}`,`Strategies: ${cc('strategy')}`,
    `Confidence Before: ${st('conf_b')}`,`Confidence After: ${st('conf_a')}`,'',
    'LEARN TO THINK','-'.repeat(40),
    `Problem:\n${v('problem')}`,`Process:\n${v('thinking')}`,
    `Outcome:\n${v('outcome')}`,`Thinking Mode: ${cc('think_mode')}`,'',
    'LEARN TO COLLABORATE','-'.repeat(40),
    `Team: ${v('team')}`,`My Role: ${v('team_role')}`,
    `Win:\n${v('collab_win')}`,`Challenge:\n${v('collab_fail')}`,`Role Style: ${cc('role_style')}`,'',
    'LEARN TO REGULATE','-'.repeat(40),
    `Setback:\n${v('setback')}`,`Time Mgmt:\n${v('time_mgmt')}`,
    `Wellbeing: ${cc('wellbeing')}`,`Stress: ${cc('stress')}`,'',
    'THE ARSENAL','-'.repeat(40),
    `AI Tools: ${cc('t_ai')}`,`Work Tools: ${cc('t_collab')}`,`Best Tool:\n${v('best_tool')}`,'',
    'JOURNEY TIMELINE','-'.repeat(40),
    `Mission 1: ${v('m1t')}\n${v('m1b')}`,
    `Mission 2: ${v('m2t')}\n${v('m2b')}`,
    `Mission 3: ${v('m3t')}\n${v('m3b')}`,'',
    'THE IMPACT','-'.repeat(40),
    `Delivered:\n${v('contribution')}`,`Value:\n${v('value')}`,`Knowledge:\n${v('school_back')}`,'',
    'MENTOR SPOTLIGHT','-'.repeat(40),
    `Mentor: ${v('mentor_name')} (${v('mentor_role')})`,
    `Lesson:\n${v('mentor_lesson')}`,`Rating: ${st('mentor_rating')}`,'',"WHAT'S NEXT",'-'.repeat(40),
    `Power-ups:\n${v('takeaways')}`,`Goals:\n${v('goals')}`,`Advice:\n${v('advice')}`,'',
    '='.repeat(50),'INTERN STAR © JAIN UNIVERSITY 2026','='.repeat(50)
  ];
  const blob=new Blob([lines.join('\n')],{type:'text/plain'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=`intern-star-${(D.name||'summary').toLowerCase().replace(/\s+/g,'-')}.txt`;
  a.click();
}

render();
