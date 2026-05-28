"use strict";

let currentStep = 1;

const interests = [
  "Curriculum design","Research & publication","Academic leadership",
  "EdTech & innovation","Policy & governance","Industry collaboration",
  "International partnerships","Student mentorship","Assessment reform",
  "Interdisciplinary studies","Faculty development","Grant writing",
  "Online & hybrid learning","Accreditation & QA","Entrepreneurship & incubation",
  "Diversity & inclusion","Corporate training","Doctoral supervision"
];

// Build chips
const grid = document.getElementById('chips-grid');
interests.forEach(opt => {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'chip';
  btn.dataset.value = opt;
  btn.innerHTML = `<svg class="chip-check" viewBox="0 0 14 14" fill="none"><path d="M2.5 7L5.5 10L11.5 4" stroke="#b8922a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>${opt}`;
  btn.addEventListener('click', () => toggleChip(btn));
  grid.appendChild(btn);
});

function toggleChip(btn) {
  const selected = document.querySelectorAll('.chip.selected');
  if (btn.classList.contains('selected')) {
    btn.classList.remove('selected');
  } else {
    if (selected.length >= 3) return;
    btn.classList.add('selected');
  }
  updateChipState();
}

function updateChipState() {
  const selected = document.querySelectorAll('.chip.selected');
  const count = selected.length;
  document.getElementById('chips-count').textContent = `${count} of 3 selected`;
  document.querySelectorAll('.chip').forEach(c => {
    if (!c.classList.contains('selected')) {
      c.classList.toggle('disabled', count >= 3);
    }
  });
}

// Word counter
document.getElementById('profile').addEventListener('input', function() {
  const words = this.value.trim() === '' ? 0 : this.value.trim().split(/\s+/).length;
  const el = document.getElementById('word-count');
  el.textContent = `${words} / 300 words`;
  el.className = 'count' + (words > 300 ? ' over' : words >= 250 ? ' near' : '');
  if (words > 300) {
    this.value = this.value.trim().split(/\s+/).slice(0, 300).join(' ');
    el.textContent = '300 / 300 words';
  }
});

function validateStep(step) {
  let ok = true;
  const clear = (id, eid) => { document.getElementById(id).classList.remove('error'); document.getElementById(eid).classList.remove('show'); };
  const err   = (id, eid) => { document.getElementById(id).classList.add('error'); document.getElementById(eid).classList.add('show'); ok = false; };

  if (step === 1) {
    clear('name','err-name'); clear('email','err-email');
    if (!document.getElementById('name').value.trim()) err('name','err-name');
    const em = document.getElementById('email').value.trim();
    if (!em || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) err('email','err-email');
  }
  if (step === 2) {
    clear('subject','err-subject'); clear('experience','err-experience');
    if (!document.getElementById('subject').value.trim()) err('subject','err-subject');
    if (!document.getElementById('experience').value) err('experience','err-experience');
  }
  if (step === 3) {
    const e = document.getElementById('err-interests');
    e.classList.remove('show');
    if (document.querySelectorAll('.chip.selected').length === 0) { e.classList.add('show'); ok = false; }
  }
  if (step === 4) {
    clear('profile','err-profile');
    const words = document.getElementById('profile').value.trim().split(/\s+/).filter(Boolean).length;
    if (words < 20) err('profile','err-profile');
  }
  return ok;
}

function goTo(step) {
  if (step > currentStep && !validateStep(currentStep)) return;
  document.getElementById(`step-${currentStep}`).classList.remove('active');
  currentStep = step;
  document.getElementById(`step-${step}`).classList.add('active');
  updateProgress();
  if (step === 5) populateReview();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateProgress() {
  for (let i = 1; i <= 5; i++) {
    const dot = document.getElementById(`dot-${i}`);
    const lbl = document.getElementById(`lbl-${i}`);
    dot.className = 'step-dot' + (i === currentStep ? ' active' : i < currentStep ? ' done' : '');
    lbl.className = 'step-label' + (i === currentStep ? ' active' : i < currentStep ? ' done' : '');
    if (i < 5) {
      document.getElementById(`line-${i}`).className = 'step-line' + (i < currentStep ? ' done' : '');
    }
  }
}

function populateReview() {
  const v = id => document.getElementById(id).value.trim() || '<span style="color:var(--ink-faint)">Not provided</span>';
  document.getElementById('rv-name').innerHTML       = v('name');
  document.getElementById('rv-email').innerHTML      = v('email');
  document.getElementById('rv-phone').innerHTML      = v('phone');
  document.getElementById('rv-subject').innerHTML    = v('subject');
  document.getElementById('rv-experience').innerHTML = v('experience');
  document.getElementById('rv-institution').innerHTML= v('institution');
  document.getElementById('rv-qualification').innerHTML = v('qualification');
  document.getElementById('rv-linkedin').innerHTML   = v('linkedin');
  document.getElementById('rv-profile').innerHTML    = document.getElementById('profile').value.trim() || '<span style="color:var(--ink-faint)">Not provided</span>';
  const chips = document.querySelectorAll('.chip.selected');
  document.getElementById('rv-interests').innerHTML = chips.length
    ? Array.from(chips).map(c => `<span class="review-chip">${c.dataset.value}</span>`).join('')
    : '<span style="color:var(--ink-faint)">None selected</span>';
}

// ── SUBMIT TO FLASK /submit → MONGODB ─────────────────────────────────────────
async function submitForm() {
  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  btn.textContent = 'Saving…';

  const payload = {
    name:          document.getElementById('name').value.trim(),
    email:         document.getElementById('email').value.trim(),
    phone:         document.getElementById('phone').value.trim(),
    subject:       document.getElementById('subject').value.trim(),
    experience:    document.getElementById('experience').value,
    institution:   document.getElementById('institution').value.trim(),
    qualification: document.getElementById('qualification').value,
    interests:     Array.from(document.querySelectorAll('.chip.selected')).map(c => c.dataset.value).join(', '),
    profile:       document.getElementById('profile').value.trim(),
    linkedin:      document.getElementById('linkedin').value.trim(),
  };

  try {
    const res  = await fetch('/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.success) {
      showSuccess(payload);
    } else {
      showToast('Error saving: ' + json.error, true);
      btn.disabled = false;
      btn.textContent = 'Submit Profile ✓';
    }
  } catch (e) {
    showToast('Network error — please try again', true);
    btn.disabled = false;
    btn.textContent = 'Submit Profile ✓';
  }
}

function showSuccess(payload) {
  document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));
  document.getElementById('success-screen').style.display = 'block';
  document.getElementById('success-msg').textContent = `Thank you, ${payload.name}! Your member profile has been received. We'll review it and reach out when relevant opportunities arise.`;
  document.getElementById('success-detail').innerHTML =
    `<strong>Submitted as:</strong> ${payload.name}<br>
     <strong>Email:</strong> ${payload.email}<br>
     <strong>Subject:</strong> ${payload.subject}<br>
     <strong>Interests:</strong> ${payload.interests || '—'}`;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showToast(msg, isError = false) {
  let t = document.getElementById('toast-el');
  if (!t) {
    t = document.createElement('div');
    t.id = 'toast-el';
    t.className = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => { t.className = 'toast'; }, 4000);
}

function resetForm() {
  document.querySelectorAll('input[type=text], input[type=email], input[type=tel], textarea').forEach(el => el.value = '');
  document.querySelectorAll('select').forEach(el => el.selectedIndex = 0);
  document.querySelectorAll('.chip.selected').forEach(c => c.classList.remove('selected'));
  document.querySelectorAll('.chip.disabled').forEach(c => c.classList.remove('disabled'));
  document.getElementById('chips-count').textContent = '0 of 3 selected';
  document.getElementById('word-count').textContent  = '0 / 300 words';
  document.getElementById('success-screen').style.display = 'none';
  currentStep = 1;
  document.getElementById('step-1').classList.add('active');
  updateProgress();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
