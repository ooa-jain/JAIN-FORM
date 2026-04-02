/* ===== STATE ===== */
let curPage=0,selId=null,dragSrcId=null;
const TLABELS={short_text:'Short Text',long_text:'Paragraph',number:'Number',email:'Email',phone:'Phone',radio:'Multiple Choice',checkbox:'Checkboxes',dropdown:'Dropdown',date:'Date',time:'Time',rating:'Rating',scale:'Linear Scale',file:'File Upload',divider:'Divider',header:'Section Header'};
const DEFS={short_text:{label:'Short Answer',placeholder:'Type here...'},long_text:{label:'Long Answer',placeholder:'Type here...'},number:{label:'Number',placeholder:'0'},email:{label:'Email Address',placeholder:'email@example.com',required:true},phone:{label:'Phone Number',placeholder:'+91 XXXXX XXXXX'},radio:{label:'Multiple Choice',options:['Option 1','Option 2','Option 3']},checkbox:{label:'Checkboxes',options:['Option 1','Option 2','Option 3']},dropdown:{label:'Dropdown',options:['Option 1','Option 2','Option 3']},date:{label:'Date'},time:{label:'Time'},rating:{label:'Rating',max_rating:5},scale:{label:'Linear Scale',scale_max:10},file:{label:'File Upload'},divider:{label:'Divider'},header:{label:'Section Title',help:'Optional subtitle'}};

/* ===== INIT ===== */
document.addEventListener('DOMContentLoaded',()=>{
  ['theme','settings','preview'].forEach(t=>{const el=document.getElementById('tab-'+t);if(el)el.style.display='none';});
  document.getElementById('tab-build').style.display='grid';
  renderAll(); refreshCanvas(); setupInlineEdit();
});

function setupInlineEdit(){
  const ti=document.getElementById('formTitle');
  ti.addEventListener('input',()=>{formState.title=ti.value;document.getElementById('cvTitle').textContent=ti.value||'Untitled';});
  ti.addEventListener('blur',autoSave);
  document.getElementById('cvTitle').addEventListener('input',e=>{formState.title=e.target.textContent;ti.value=e.target.textContent;});
  document.getElementById('cvTitle').addEventListener('blur',autoSave);
  document.getElementById('cvDesc').addEventListener('input',e=>{formState.description=e.target.textContent;});
  document.getElementById('cvDesc').addEventListener('blur',autoSave);
}

/* ===== MOBILE ===== */
function toggleMobLeft(){document.getElementById('bleft').classList.toggle('mob-open');}

/* ===== TABS ===== */
function showTab(name,btn){
  ['build','theme','settings','preview'].forEach(t=>{const el=document.getElementById('tab-'+t);if(el)el.style.display='none';});
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  const el=document.getElementById('tab-'+name);
  if(el)el.style.display=(name==='build')?'grid':'flex';
  if(btn)btn.classList.add('active');
}

/* ===== PAGES ===== */
function renderAll(){renderPageList();renderPageTabs();renderFields();}

function renderPageList(){
  const list=document.getElementById('pageList');
  list.innerHTML='';
  formState.pages.forEach((p,i)=>{
    const d=document.createElement('div');
    d.className='pgitem'+(i===curPage?' active':'');
    d.innerHTML=`<span class="pg-num">${i+1}</span><span style="flex:1;font-size:.84rem">${p.title||'Page '+(i+1)}</span>${formState.pages.length>1?`<button class="pg-del" onclick="event.stopPropagation();delPage(${i})">×</button>`:''}`;
    d.onclick=()=>switchPage(i);
    list.appendChild(d);
  });
  const badge=document.getElementById('cvBadge');
  if(badge)badge.textContent=formState.pages.length>1?`Page ${curPage+1} of ${formState.pages.length}`:'';
}

function renderPageTabs(){
  const tabs=document.getElementById('cvPageTabs');
  tabs.innerHTML='';
  if(formState.pages.length<=1){tabs.style.display='none';return;}
  tabs.style.display='flex';
  formState.pages.forEach((p,i)=>{
    const b=document.createElement('button');
    b.className='cvtab'+(i===curPage?' active':'');
    b.textContent=p.title||`Page ${i+1}`;
    b.onclick=()=>switchPage(i);
    tabs.appendChild(b);
  });
}

function switchPage(i){curPage=i;selId=null;renderAll();hideEditor();}
function addPage(){formState.pages.push({id:'p_'+Date.now(),title:'Page '+(formState.pages.length+1),fields:[]});switchPage(formState.pages.length-1);autoSave();}
function delPage(i){if(!confirm('Delete this page?'))return;formState.pages.splice(i,1);curPage=Math.min(curPage,formState.pages.length-1);renderAll();autoSave();}

/* ===== FIELDS ===== */
function addField(type){
  const def=DEFS[type]||{};
  const f={id:'f_'+Date.now(),type,label:def.label||'New Field',help:def.help||'',required:!!def.required,placeholder:def.placeholder||'',options:def.options?[...def.options]:undefined,max_rating:def.max_rating,scale_max:def.scale_max};
  formState.pages[curPage].fields.push(f);
  renderFields();selectField(f.id);autoSave();
  document.getElementById('bleft').classList.remove('mob-open');
}

function renderFields(){
  const area=document.getElementById('cvFields'),empty=document.getElementById('cvEmpty');
  area.querySelectorAll('.fcard').forEach(c=>c.remove());
  const fields=formState.pages[curPage]?.fields||[];
  empty.style.display=fields.length?'none':'block';
  fields.forEach(f=>area.appendChild(makeCard(f)));
}

function makeCard(f){
  const c=document.createElement('div');
  c.className='fcard'+(f.id===selId?' sel':'');
  c.dataset.id=f.id;
  c.draggable=true;

  // Click to select (only if not dragging)
  c.addEventListener('click',e=>{if(!e.target.classList.contains('fc-drag-handle'))selectField(f.id);});

  // Drag-and-drop
  c.addEventListener('dragstart',e=>{dragSrcId=f.id;c.classList.add('dragging');e.dataTransfer.effectAllowed='move';});
  c.addEventListener('dragend',()=>{dragSrcId=null;c.classList.remove('dragging');document.querySelectorAll('.fcard.drag-over').forEach(x=>x.classList.remove('drag-over'));});
  c.addEventListener('dragover',e=>{e.preventDefault();c.classList.add('drag-over');});
  c.addEventListener('dragleave',()=>c.classList.remove('drag-over'));
  c.addEventListener('drop',e=>{e.preventDefault();c.classList.remove('drag-over');if(dragSrcId&&dragSrcId!==f.id)swapFields(dragSrcId,f.id);});

  let preview='';
  if(['short_text','email','phone','number'].includes(f.type))preview=`<div class="fc-prev">${f.placeholder||'Text input'}</div>`;
  else if(f.type==='long_text')preview=`<div class="fc-prev" style="min-height:30px">${f.placeholder||'Long text'}</div>`;
  else if(['radio','checkbox','dropdown'].includes(f.type))preview=(f.options||[]).slice(0,3).map(o=>`<div style="font-size:.77rem;color:#ccc;padding:2px 0">○ ${o}</div>`).join('');
  else if(f.type==='rating')preview=`<div style="font-size:1.05rem;color:#FFB347">${'★'.repeat(f.max_rating||5)}</div>`;
  else if(f.type==='scale')preview=Array.from({length:Math.min(f.scale_max||10,10)},(_,i)=>`<span class="sc-pip">${i+1}</span>`).join('');
  else if(f.type==='date')preview=`<div class="fc-prev">📅 Date</div>`;
  else if(f.type==='time')preview=`<div class="fc-prev">⏰ Time</div>`;
  else if(f.type==='file')preview=`<div class="fc-prev">📎 File upload</div>`;
  else if(f.type==='divider')preview=`<hr style="border:none;border-top:2px solid #E8E0D5;margin:4px 0">`;
  else if(f.type==='header'&&f.help)preview=`<div style="font-size:.79rem;color:#aaa;margin-top:3px">${f.help}</div>`;

  c.innerHTML=`<div class="fc-drag-handle" title="Drag to reorder">⠿</div><div class="fc-main"><div class="fc-head"><span class="fc-label">${f.type==='divider'?'— Divider':f.label}${f.required?'<span class="fc-req"> *</span>':''}</span><span class="fc-type">${TLABELS[f.type]||f.type}</span></div><div class="fc-body">${preview}</div></div>`;
  return c;
}

function swapFields(srcId,tgtId){
  const fields=formState.pages[curPage].fields;
  const si=fields.findIndex(f=>f.id===srcId),ti=fields.findIndex(f=>f.id===tgtId);
  if(si<0||ti<0)return;
  [fields[si],fields[ti]]=[fields[ti],fields[si]];
  renderFields();
  document.querySelectorAll('.fcard').forEach(c=>c.classList.toggle('sel',c.dataset.id===selId));
  autoSave();
}

function onDragOver(e){e.preventDefault();}
function onDrop(e){
  e.preventDefault();
  if(dragSrcId){
    const fields=formState.pages[curPage].fields;
    const si=fields.findIndex(f=>f.id===dragSrcId);
    if(si>=0){const[f]=fields.splice(si,1);fields.push(f);}
    renderFields();autoSave();
  }
}

function selectField(id){
  selId=id;
  document.querySelectorAll('.fcard').forEach(c=>c.classList.toggle('sel',c.dataset.id===id));
  const f=getField(id);if(f)showEditor(f);
  document.getElementById('bright').classList.add('mob-open');
}

function getField(id){for(const p of formState.pages){const f=p.fields.find(x=>x.id===id);if(f)return f;}return null;}

function upd(key,val){
  const f=getField(selId);if(!f)return;
  f[key]=val;renderFields();
  document.querySelectorAll('.fcard').forEach(c=>c.classList.toggle('sel',c.dataset.id===selId));
  autoSave();
}

function deleteField(){if(!selId||!confirm('Delete this field?'))return;formState.pages[curPage].fields=formState.pages[curPage].fields.filter(f=>f.id!==selId);selId=null;renderFields();hideEditor();autoSave();}

function moveField(dir){
  const fields=formState.pages[curPage].fields;
  const i=fields.findIndex(f=>f.id===selId),ni=i+dir;
  if(i<0||ni<0||ni>=fields.length)return;
  [fields[i],fields[ni]]=[fields[ni],fields[i]];
  renderFields();
  document.querySelectorAll('.fcard').forEach(c=>c.classList.toggle('sel',c.dataset.id===selId));
  autoSave();
}

/* ===== EDITOR ===== */
function showEditor(f){
  document.getElementById('feEmpty').style.display='none';
  document.getElementById('fePanel').style.display='block';
  document.getElementById('feBadge').textContent=TLABELS[f.type]||f.type;
  document.getElementById('feLabel').value=f.label||'';
  document.getElementById('feHelp').value=f.help||'';
  document.getElementById('feRequired').checked=!!f.required;
  const hp=['short_text','long_text','email','phone','number'].includes(f.type);
  document.getElementById('wPlaceholder').style.display=hp?'block':'none';
  if(hp)document.getElementById('fePlaceholder').value=f.placeholder||'';
  const ho=['radio','checkbox','dropdown'].includes(f.type);
  document.getElementById('wOptions').style.display=ho?'block':'none';
  if(ho)renderOpts(f.options||[]);
  document.getElementById('wRating').style.display=f.type==='rating'?'block':'none';
  if(f.type==='rating')document.getElementById('feMaxRating').value=f.max_rating||5;
  document.getElementById('wScale').style.display=f.type==='scale'?'block':'none';
  if(f.type==='scale')document.getElementById('feScaleMax').value=f.scale_max||10;
}

function hideEditor(){document.getElementById('feEmpty').style.display='block';document.getElementById('fePanel').style.display='none';document.getElementById('bright').classList.remove('mob-open');}
function renderOpts(opts){const list=document.getElementById('optList');list.innerHTML='';opts.forEach((o,i)=>{const row=document.createElement('div');row.style.cssText='display:flex;gap:6px;margin-bottom:6px';row.innerHTML=`<input type="text" value="${o.replace(/"/g,'&quot;')}" placeholder="Option ${i+1}" style="flex:1;padding:7px 10px;border:1.5px solid #E0E0E0;border-radius:8px;font-family:inherit;font-size:.84rem" onchange="updOpt(${i},this.value)" oninput="updOpt(${i},this.value)"><button onclick="delOpt(${i})" style="background:none;border:none;cursor:pointer;color:#ccc;font-size:1.1rem;padding:3px;border-radius:5px">×</button>`;list.appendChild(row);});}
function addOpt(){const f=getField(selId);if(!f)return;f.options=f.options||[];f.options.push('Option '+(f.options.length+1));renderOpts(f.options);renderFields();autoSave();}
function updOpt(i,v){const f=getField(selId);if(!f||!f.options)return;f.options[i]=v;renderFields();autoSave();}
function delOpt(i){const f=getField(selId);if(!f||!f.options)return;f.options.splice(i,1);renderOpts(f.options);renderFields();autoSave();}

/* ===== CANVAS ===== */
function refreshCanvas(){
  const cover=document.getElementById('cvCover');if(!cover)return;
  const img=formState.theme.cover_image,hdr=formState.theme.header_color||'#1A1A2E';
  if(img&&img.startsWith('http'))cover.style.background=`linear-gradient(rgba(0,0,0,0.42),rgba(0,0,0,0.58)),url('${img}') center/cover`;
  else if(img&&img.startsWith('linear'))cover.style.background=img;
  else cover.style.background=hdr;
}
function liveCanvas(){formState.theme.header_color=document.getElementById('th_hdr').value;refreshCanvas();}

/* ===== COVER TABS ===== */
function switchCoverTab(name,btn){
  document.querySelectorAll('.ctab').forEach(b=>b.classList.remove('active'));btn.classList.add('active');
  ['url','unsplash','solid'].forEach(t=>{const el=document.getElementById('ctab-'+t);if(el)el.style.display='none';});
  document.getElementById('ctab-'+name).style.display='block';
}

function previewCover(){
  const val=document.getElementById('th_cover').value.trim();
  const box=document.getElementById('coverPreviewBox');
  if(val){box.style.backgroundImage=`url('${val}')`;box.innerHTML='';box.classList.add('has-img');}
  else{box.style.backgroundImage='';box.innerHTML='<span>No cover image</span>';box.classList.remove('has-img');}
  formState.theme.cover_image=val;refreshCanvas();
}

function searchUnsplash(){
  const q=document.getElementById('unsplashQ').value.trim();if(!q)return;
  const res=document.getElementById('unsplashResults');
  res.innerHTML='<div style="color:#aaa;padding:16px;text-align:center;grid-column:1/-1">Loading images...</div>';
  const keywords=q.replace(/\s+/g,',');
  const imgs=Array.from({length:9},(_,i)=>`https://source.unsplash.com/400x250/?${encodeURIComponent(keywords)}&random=${Date.now()}_${i}`);
  res.innerHTML=imgs.map(src=>`<div class="unsplash-item" onclick="selectUnsplash('${src}')"><img src="${src}" alt="" loading="lazy" onerror="this.parentElement.style.display='none'"><div class="unsplash-overlay">✓ Use</div></div>`).join('');
}

function selectUnsplash(url){
  formState.theme.cover_image=url;
  document.getElementById('th_cover').value=url;
  const box=document.getElementById('coverPreviewBox');
  box.style.backgroundImage=`url('${url}')`;box.innerHTML='';box.classList.add('has-img');
  refreshCanvas();showToast('Cover image set! Click Save Theme.','success');
}

function setSolidCover(gradient){
  formState.theme.cover_image=gradient;
  document.getElementById('th_cover').value='';
  const box=document.getElementById('coverPreviewBox');
  box.style.backgroundImage='';box.style.background=gradient;box.innerHTML='';
  refreshCanvas();showToast('Header style applied!','success');
}

/* ===== PRESETS ===== */
const PRESETS={mango:{bg_color:'#FFF8F0',header_color:'#1A1A2E',accent_color:'#FF8C00',text_color:'#1A1A2E',card_color:'#FFFFFF',font:'DM Sans'},ocean:{bg_color:'#E8F4FD',header_color:'#0F2027',accent_color:'#2980B9',text_color:'#1A2A3A',card_color:'#FFFFFF',font:'Inter'},forest:{bg_color:'#F0F7F4',header_color:'#134E5E',accent_color:'#2D6A4F',text_color:'#1A2E24',card_color:'#FFFFFF',font:'Lato'},rose:{bg_color:'#FFF0F3',header_color:'#6D213C',accent_color:'#C94B4B',text_color:'#2D1A1E',card_color:'#FFFFFF',font:'Poppins'},midnight:{bg_color:'#1a1a2e',header_color:'#0d0d0d',accent_color:'#7B2FBE',text_color:'#E0E0E0',card_color:'#2D2D4E',font:'DM Sans'},jain:{bg_color:'#EEF4FF',header_color:'#003366',accent_color:'#0066CC',text_color:'#1A2A3A',card_color:'#FFFFFF',font:'Inter'},minimal:{bg_color:'#FFFFFF',header_color:'#343A40',accent_color:'#495057',text_color:'#212529',card_color:'#F8F9FA',font:'Inter'},purple:{bg_color:'#F3F0FF',header_color:'#4a00e0',accent_color:'#8e2de2',text_color:'#1A1A2E',card_color:'#FFFFFF',font:'Poppins'}};

function applyPreset(name){const p=PRESETS[name];if(!p)return;Object.assign(formState.theme,p);document.getElementById('th_bg').value=p.bg_color;document.getElementById('th_hdr').value=p.header_color;document.getElementById('th_acc').value=p.accent_color;document.getElementById('th_txt').value=p.text_color;document.getElementById('th_card').value=p.card_color;document.getElementById('th_font').value=p.font;refreshCanvas();autoSave();showToast('Theme applied!','success');}

function saveTheme(){formState.theme.bg_color=document.getElementById('th_bg').value;formState.theme.header_color=document.getElementById('th_hdr').value;formState.theme.accent_color=document.getElementById('th_acc').value;formState.theme.text_color=document.getElementById('th_txt').value;formState.theme.card_color=document.getElementById('th_card').value;formState.theme.font=document.getElementById('th_font').value;formState.theme.cover_image=document.getElementById('th_cover').value;formState.theme.button_text=document.getElementById('th_btn').value;refreshCanvas();autoSave();showToast('Theme saved!','success');}

function saveSettings(){formState.settings.show_progress=document.getElementById('st_prog').checked;formState.settings.confirmation_message=document.getElementById('st_confirm').value;formState.settings.redirect_url=document.getElementById('st_redir').value;formState.settings.notify_on_submit=document.getElementById('st_notify').checked;formState.settings.notify_email=document.getElementById('st_notify_email').value;autoSave();showToast('Settings saved!','success');}

function setPrevSize(size,btn){document.querySelectorAll('.prev-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');const f=document.getElementById('prevFrame');const w={desktop:'100%',tablet:'768px',mobile:'390px'};f.style.maxWidth=w[size]||'100%';}

let saveTimer=null;
function autoSave(){
  clearTimeout(saveTimer);
  document.getElementById('saveStatus').textContent='Saving...';
  saveTimer=setTimeout(async()=>{
    formState.title=document.getElementById('formTitle').value;
    try{const r=await fetch(SAVE_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(formState)});const d=await r.json();document.getElementById('saveStatus').textContent=d.success?'Saved ✓':'Save failed';}
    catch(e){document.getElementById('saveStatus').textContent='Save failed';}
  },900);
}

async function togglePublish(){
  try{const r=await fetch(PUB_URL,{method:'POST'});const d=await r.json();formState.settings.is_published=d.is_published;const btn=document.getElementById('pubBtn');btn.textContent=d.is_published?'🔴 Unpublish':'🚀 Publish';btn.className='btn-pub'+(d.is_published?' is-live':'');showToast(d.is_published?'🚀 Form is live!':'Form unpublished',d.is_published?'success':'info');}
  catch(e){showToast('Failed','info');}
}

function showToast(msg,type='info'){const t=document.getElementById('toast');if(!t)return;t.textContent=msg;t.className='toast '+type+' show';clearTimeout(t._t);t._t=setTimeout(()=>t.classList.remove('show'),2800);}
function copyLink(url){navigator.clipboard.writeText(url).then(()=>showToast('Link copied!','success'));}

/* ===== AI IMPROVE ===== */
function openAIImprove(){
  document.getElementById('aiModal').style.display='flex';
  document.getElementById('aiImprovePrompt').focus();
  document.getElementById('aiImproveError').style.display='none';
  // Allow Ctrl+Enter
  document.getElementById('aiImprovePrompt').onkeydown = e=>{
    if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)) runAIImprove();
  };
}

function useAIChip(btn){
  document.getElementById('aiImprovePrompt').value = btn.textContent;
}

async function runAIImprove(){
  const prompt = document.getElementById('aiImprovePrompt').value.trim();
  if(!prompt){ alert('Please describe what you want to change.'); return; }
  const btn = document.getElementById('aiImproveBtn');
  const errEl = document.getElementById('aiImproveError');
  errEl.style.display='none';
  btn.textContent='⏳ Improving...'; btn.disabled=true;

  try {
    const res = await fetch('/ai/improve', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ prompt, current_form: formState })
    });
    const data = await res.json();
    if(!data.success) throw new Error(data.error||'Failed');

    // Apply the improved form state
    Object.assign(formState, data.form);
    document.getElementById('formTitle').value = formState.title || '';
    document.getElementById('cvTitle').textContent = formState.title || '';
    document.getElementById('cvDesc').textContent = formState.description || '';
    curPage = 0; selId = null;
    renderAll(); refreshCanvas(); autoSave();
    document.getElementById('aiModal').style.display='none';
    document.getElementById('aiImprovePrompt').value='';
    showToast('✦ Form improved by AI!','success');
  } catch(e) {
    errEl.textContent='⚠ '+e.message; errEl.style.display='block';
  }
  btn.textContent='✦ Improve Form'; btn.disabled=false;
}
