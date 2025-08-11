/* ========= Références ========= */
const aesKeyLengthBox = document.getElementById('aesKeyLength');
const aesKeyLengthVal = document.getElementById('aesKeyLengthVal');
const box = document.getElementById('box');
const toggle = document.getElementById('toggle');
const leds = [document.getElementById('ledR'), document.getElementById('ledG')];
let power = true;

/* ========= Popup Reboot ========= */
const rebootBackdrop = document.getElementById('rebootBackdrop');
const rebootCount = document.getElementById('rebootCount');
const rebootNote = document.getElementById('rebootNote');

let rebootTimer = null;
let rebootSeconds = 10;
let rebootActive = false;

function showRebootPopup(){
  if (!rebootBackdrop) return;
  if (rebootActive) return;
  rebootActive = true;
  rebootSeconds = 10;
  rebootCount.textContent = `Rebooting (${rebootSeconds}s)`;
  rebootNote.textContent = 'All controls are temporarily disabled.';
  rebootBackdrop.setAttribute('aria-hidden','false');

  rebootTimer = setInterval(async ()=>{
    rebootSeconds -= 1;
    if (rebootSeconds > 0) {
      rebootCount.textContent = `Rebooting (${rebootSeconds}s)`;
      return;
    }
    clearInterval(rebootTimer);
    rebootTimer = null;
    try { await fetch('/reboot', { method:'GET', cache:'no-store' }); } catch(_) {}
    rebootCount.textContent = 'Reboot command sent';
    rebootNote.textContent = 'Power-cycle required — Unplug the BiduleBox, wait 2 seconds, then plug it back in.';
  }, 1000);
}
function hideRebootPopup(){
  if (!rebootBackdrop) return;
  if (rebootTimer) { clearInterval(rebootTimer); rebootTimer = null; }
  rebootActive = false;
  rebootBackdrop.setAttribute('aria-hidden','true');
}

/* ========= ON / OFF ========= */
function setPower(on){
  const wasOn = !!power;
  power = !!on;

  toggle.classList.toggle('on', power);
  toggle.classList.toggle('off', !power);
  toggle.setAttribute('aria-checked', power ? 'true' : 'false');
  box.classList.toggle('off-state', !power);
  leds[0].classList.toggle('on', !power); // rouge = veille
  leds[1].classList.toggle('on', power);  // verte = marche

  if (wasOn && !power) showRebootPopup();
  if (!wasOn && power) hideRebootPopup();
}
setPower(true);

toggle.addEventListener('click', ()=> setPower(!power));
toggle.addEventListener('keydown', e=>{
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setPower(!power); }
});
leds.forEach(led=>{
  led.addEventListener('click', ()=>{
    if(!power) return;
    led.classList.toggle('on');
  });
});

/* Boutons - visuel press */
document.querySelectorAll('.btn').forEach(b=>{
  b.addEventListener('mousedown', ()=> power && b.classList.add('pressed'));
  ['mouseup','mouseleave','touchend','touchcancel']
    .forEach(ev=> b.addEventListener(ev, ()=> b.classList.remove('pressed')));
});

/* ========= Données boutons ========= */
const DEFAULT_BUTTON = id => ({ id, color:"", pin:"", macro:"", command:"", pass_key:"", winsearch:false, delay_ms:0 });
let buttons = [];
let byId = new Map();

async function loadCommands(){
  try{
    const res = await fetch('/config', {cache:'no-store'});
    const data = await res.json();
    const arr = Array.isArray(data.buttons) ? data.buttons : [];
    buttons = structuredClone(arr);
    rebuildIndex();
  }catch(e){
    console.warn('Config introuvable/invalid → états vides.', e);
    buttons = [];
    rebuildIndex();
  }
}
function rebuildIndex(){
  byId = new Map(buttons.map(b => [Number(b.id), b]));
}

/* ========= POPIN configuration bouton ========= */
const popinBackdrop = document.getElementById('popinBackdrop');
const popinClose = document.getElementById('popinClose');
const popinCancel = document.getElementById('popinCancel');
const popinSave = document.getElementById('popinSave');
const popinBtnId = document.getElementById('popinBtnId');
const form = document.getElementById('btnForm');

let lastFocused = null;

function openPopin(forBtn){
  if(!power) return;
  lastFocused = forBtn;
  const id = Number(forBtn.dataset.btId);
  const rec = byId.get(id) ? structuredClone(byId.get(id)) : DEFAULT_BUTTON(id);
  const color = rec.color ?? "";

  document.getElementById('popinTitle').textContent = `Configuration bouton ${id} — ${color}`;

  form.f_id.value = rec.id;
  popinBtnId.textContent = rec.id;
  form.f_color.value = rec.color ?? "";
  form.f_pin.value = rec.pin ?? "";
  form.f_macro.value = rec.macro ?? "";
  form.f_command.value = rec.command ?? "";
  form.f_pass_key.value = rec.pass_key ?? "";
  form.f_winsearch.checked = !!rec.winsearch;
  form.f_delay_ms.value = rec.delay_ms ?? 0;

  popinBackdrop.setAttribute('aria-hidden','false');
  setTimeout(()=> popinClose.focus(), 0);

  form.dataset.currentId = String(id);
}
function closePopin(){
  popinBackdrop.setAttribute('aria-hidden','true');
  if(lastFocused) lastFocused.focus();
}
function onEsc(e){ if(e.key === 'Escape') closePopin(); }

/* ========= Bind normal/capture ========= */
const btnEls = Array.from(document.querySelectorAll('.btn'));
const normalHandlers = new Map();
const captureHandlers = new Map();

function bindNormal(){
  btnEls.forEach(b=>{
    if (normalHandlers.has(b)) return;
    const fn = ()=> openPopin(b);
    normalHandlers.set(b, fn);
    b.addEventListener('click', fn);
  });
}
function unbindNormal(){
  btnEls.forEach(b=>{
    const fn = normalHandlers.get(b);
    if (fn){ b.removeEventListener('click', fn); normalHandlers.delete(b); }
  });
}
bindNormal();

[popinClose, popinCancel].forEach(el=> el.addEventListener('click', closePopin));
popinBackdrop.addEventListener('click', e=>{ if(e.target===popinBackdrop) closePopin(); });
document.addEventListener('keydown', onEsc);

/* Save (dans le tableau en mémoire) */
popinSave.addEventListener('click', ()=>{
  const id = Number(form.dataset.currentId);
  const payload = {
    id,
    color: (form.f_color.value || "").trim(),
    pin: (form.f_pin.value || "").trim(),
    macro: (form.f_macro.value || "").trim(),
    command: form.f_command.value || "",
    pass_key: (form.f_pass_key.value || "").trim(),
    winsearch: !!form.f_winsearch.checked,
    delay_ms: Number(form.f_delay_ms.value || 0)
  };
  const existing = byId.get(id);
  if(existing){
    const idx = buttons.findIndex(b => Number(b.id) === id);
    if(idx > -1) buttons[idx] = payload;
  }else{
    buttons.push(payload);
  }
  rebuildIndex();
  closePopin();
});

/* ========= API util ========= */
window.getButtonsJSON = () => JSON.stringify({ buttons }, null, 2);
window.setButtonsFromJSON = (jsonStr) => {
  try{
    const obj = JSON.parse(jsonStr);
    if(Array.isArray(obj.buttons)){ buttons = obj.buttons; rebuildIndex(); return true; }
  }catch(e){ console.error(e); }
  return false;
};

/* ========= POST /config ========= */
document.querySelector('.save-config').addEventListener('click', async ()=>{
  try{
    const payload = { buttons };
    const res = await fetch('/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if(data.ok){
      alert('Configuration enregistrée');
    }else{
      alert('Erreur: ' + (data.error || 'inconnue'));
    }
  }catch(e){
    alert('Erreur réseau : ' + e);
  }
});

/* ========= Save Key ========= */
const btnSaveKey   = document.querySelector('.save-key');
const btnSendKey   = document.querySelector('.send-key'); // Done
const btnSaveConfig= document.querySelector('.save-config');

let keyBackdrop, keyNameEl, keyValueEl, keyCancelEl, keyContinueEl;
let pendingKeyName = '', pendingKeyValue = '';

function ensureKeyPopin(){
  if (document.getElementById('keyBackdrop')) {
    // déjà créé → recâble les refs (au cas où)
    keyBackdrop  = document.getElementById('keyBackdrop');
    keyNameEl    = document.getElementById('keyName');
    keyValueEl   = document.getElementById('keyValue');
    keyCancelEl  = document.getElementById('keyCancel');
    keyContinueEl= document.getElementById('keyContinue');
    return;
  }

  const wrap = document.createElement('div');
  wrap.className = 'popin-backdrop';
  wrap.id = 'keyBackdrop';
  wrap.setAttribute('role','dialog');
  wrap.setAttribute('aria-modal','true');
  wrap.setAttribute('aria-hidden','true');
  wrap.setAttribute('aria-labelledby','keyTitle');

  wrap.innerHTML = `
    <div class="popin" role="document">
      <button class="btn-close" id="keyClose" aria-label="Fermer">✕</button>
      <header class="popin-header">
        <span class="chip" aria-hidden="true"></span>
        <h2 class="popin-title" id="keyTitle">Save a key</h2>
        <div class="popin-meta">Secrets</div>
      </header>
      <div class="popin-body">
        <div class="f">
          <label>Key name</label>
          <input type="text" id="keyName" placeholder="e.g., rpi" autocomplete="off">
        </div>
        <div class="f">
          <label>Key value</label>
          <input type="text" id="keyValue" placeholder="password or token" autocomplete="off">
        </div>
      </div>
      <div class="popin-actions">
        <button class="btn-hud secondary" id="keyCancel" type="button">Cancel</button>
        <button class="btn-hud" id="keyContinue" type="button">Continue</button>
      </div>
    </div>
  `;
  document.body.appendChild(wrap);

  keyBackdrop  = document.getElementById('keyBackdrop');
  keyNameEl    = document.getElementById('keyName');
  keyValueEl   = document.getElementById('keyValue');
  keyCancelEl  = document.getElementById('keyCancel');
  keyContinueEl= document.getElementById('keyContinue');

  const keyClose = document.getElementById('keyClose');
  keyClose.addEventListener('click', closeKeyPopin);
  keyCancelEl.addEventListener('click', closeKeyPopin);
  keyBackdrop.addEventListener('click', e=>{ if(e.target===keyBackdrop) closeKeyPopin(); });
  keyContinueEl.addEventListener('click', onKeyContinue); // <-- handler câblé ici
}

function openKeyPopin(){
  ensureKeyPopin();
  keyBackdrop.setAttribute('aria-hidden','false');
  setTimeout(()=> keyNameEl && keyNameEl.focus(), 0);
}
function closeKeyPopin(){
  if (!keyBackdrop) return;
  keyBackdrop.setAttribute('aria-hidden','true');
}

function onKeyContinue(){
  pendingKeyName  = (keyNameEl?.value || '').trim();
  pendingKeyValue = (keyValueEl?.value || '').trim();
  if (!pendingKeyName){ alert('Key name is required.'); return; }

  closeKeyPopin();

  // UI : toggle boutons
   if (btnSaveKey)    btnSaveKey.hidden = true;
  if (btnSaveConfig) btnSaveConfig.hidden = true;
  if (btnSendKey)    btnSendKey.hidden = false;

  bindCapture();
}

/* ========= Mode capture AES key ========= */
let captureSequence = [];        // ordre des clics (ids)
let captureCounts = new Map();   // id -> count
let capturing = false;

function resetCaptureState(){
  captureSequence = [];
  captureCounts = new Map();
  btnEls.forEach(b=>{
    const id = Number(b.dataset.btId);
    captureCounts.set(id, 0);
  });
}
function recordPress(btn){
  if (!capturing) return;
  const id = Number(btn.dataset.btId);
  captureSequence.push(id);
  captureCounts.set(id, (captureCounts.get(id) || 0) + 1);
  // maj longueur
  const len = buildAesKeyFromCapture().length;
  if (aesKeyLengthVal) aesKeyLengthVal.textContent = len;
}
function bindCapture(){
  if (capturing) return;
  unbindNormal();
  resetCaptureState();
  if (aesKeyLengthBox) { aesKeyLengthBox.style.display = ''; aesKeyLengthVal.textContent = '0'; }

  btnEls.forEach(b=>{
    if (captureHandlers.has(b)) return;
    const fn = ()=> recordPress(b);
    captureHandlers.set(b, fn);
    b.addEventListener('click', fn);
  });
  capturing = true;
}
function unbindCapture(){
  btnEls.forEach(b=>{
    const fn = captureHandlers.get(b);
    if (fn){ b.removeEventListener('click', fn); captureHandlers.delete(b); }
  });
  capturing = false;
  resetCaptureState();
  if (aesKeyLengthBox) { aesKeyLengthBox.style.display = 'none'; aesKeyLengthVal.textContent = '0'; }
}

/* construit la clé comme dans code.py */
function buildAesKeyFromCapture(){
  const seqStr = captureSequence.map(n=> String(n)).join('');
  const ids = Array.from(captureCounts.keys()).sort((a,b)=>a-b);
  const countsPart = ids.filter(id => (captureCounts.get(id) || 0) > 0)
                        .map(id => `${id}${captureCounts.get(id)}`).join('');
  return `${seqStr}X${countsPart}`;
}

/* Boutons Save Key / Done */
btnSaveKey?.addEventListener('click', openKeyPopin);

btnSendKey?.addEventListener('click', async ()=>{
  const aes_key = buildAesKeyFromCapture();
  if (aes_key.length !== 24){
    alert(`The derived AES key must be exactly 24 characters.\nCurrent length: ${aes_key.length}\nKeep clicking buttons to reach 24, then press Done again.`);
    return;
  }
  try{
    const res = await fetch('/savekey', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ aes_key, "key_name": pendingKeyName, "key_value": pendingKeyValue })
    });
    const data = await res.json();
    if (!data.ok){ throw new Error(data.error || 'Unknown error'); }
    alert(`Key saved: ${pendingKeyName}`);
  }catch(e){
    alert('Save failed: ' + e.message);
  }finally{
    unbindCapture();
    bindNormal();
	
	        // cacher
      // montrer
	
	
      if (btnSendKey)    btnSendKey.hidden = true;   // cacher Done
  if (btnSaveKey)    btnSaveKey.hidden = false;  // réafficher Save a key
  if (btnSaveConfig) btnSaveConfig.hidden = false;
    pendingKeyName = ''; pendingKeyValue = '';
  }
});

/* ========= Boot ========= */
loadCommands();