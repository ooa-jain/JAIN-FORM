function showToast(msg, type='info'){
  const t=document.getElementById('toast');
  if(!t)return;
  t.textContent=msg; t.className='toast '+type+' show';
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove('show'),3000);
}
function copyLink(url){
  navigator.clipboard.writeText(url).then(()=>showToast('Link copied!','success'));
}
function toggleDrop(btn){
  const m=btn.nextElementSibling;
  document.querySelectorAll('.drop-menu.open').forEach(d=>{if(d!==m)d.classList.remove('open')});
  m.classList.toggle('open');
}
document.addEventListener('click',e=>{
  if(!e.target.closest('.fcard-more'))
    document.querySelectorAll('.drop-menu.open').forEach(d=>d.classList.remove('open'));
  if(e.target.classList.contains('modal-overlay'))
    e.target.style.display='none';
});
