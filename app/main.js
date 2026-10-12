// 스크래치 전용 학습 화면 (기획서 5장, hi-fi 목업 화면 15).
// 교안 패널과 버튼은 이 화면이 그리고, 에디터는 iframe으로 띄워 메시지로만 통신한다.

import { renderMarkdown } from './markdown.js';
import { ScratchStudioFrame } from './studio-frame.js';
import { createStore, isYoutubeUrl, youtubeId } from './store.js';

const params = new URLSearchParams(location.search);
const config = {
  unitBase: (params.get('unit') || '../project/lv1/04-pirate-cannon').replace(/\/$/, ''),
  editorUrl: params.get('editor') || './editor-stub/index.html',
  exitUrl: params.get('exit') || '',
  failFirstSave: params.get('saveFail') === '1',
};
const editorUrl = new URL(config.editorUrl, location.href);

const AUTOSAVE_MS = 30000;
const PANEL_MIN = 300, PANEL_MAX = 560;
const LOCALE_KEY = 'ss:locale';
const SUBMIT_KEY = '__submit';

const BANDS = {
  pass: { cls: 'is-pass', icon: '✓', text: '통과했어요' },
  fail: { cls: 'is-fail', icon: '!', text: '아직이에요. 다시 해 보세요' },
  error: { cls: 'is-error', icon: '↻', text: '확인하지 못했어요. 다시 눌러 주세요' },
  resubmitted: { cls: 'is-pass', icon: '✓', text: '다시 제출했어요.' },
  submitError: { cls: 'is-error', icon: '↻', text: '제출하지 못했어요. 다시 눌러 주세요' },
};

const $ = (id) => document.getElementById(id);
const el = {
  app: $('app'), strip: $('strip'), panel: $('panel'), resizer: $('resizer'),
  unitTitle: $('unitTitle'), stepLabel: $('stepLabel'), stepShort: $('stepShort'),
  body: $('body'), band: $('band'), bandIcon: $('bandIcon'), bandText: $('bandText'),
  prev: $('prevBtn'), primary: $('primaryBtn'),
  loading: $('editorLoading'), iframe: $('editor'),
};

const state = {
  unit: null, steps: [], step: 0,
  locale: readLocale(),
  result: null,        // null | grading | pass | fail | error | resubmitted | submitError
  panelOpen: true, panelW: 360,
  editorReady: false,
  dirty: false, saving: false,
  submission: null, editing: false, submitting: false,
  form: { title: '', note: '', note2: '', yt: '' },
};
let store, frame;

function readLocale() {
  try { return localStorage.getItem(LOCALE_KEY) === 'en' ? 'en' : 'ko'; } catch (e) { return 'ko'; }
}
// 영어 값이 없으면 한국어로 대체한다.
const t = (v) => (v && typeof v === 'object' ? v[state.locale] || v.ko || '' : v || '');
const escapeHtml = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const passedKeys = () => store.getProgress().passed;
const isPassed = (i) => (state.steps[i].type === 'submit' ? !!state.submission : passedKeys().includes(state.steps[i].key));
const current = () => state.steps[state.step];

// ---- 교안 본문 ----

function renderBlocksCode(code) {
  const box = document.createElement('div');
  box.className = 'ss-blocks';
  const sb = window.scratchblocks;
  try {
    if (!sb) throw new Error('scratchblocks not loaded');
    const options = { style: 'scratch3', languages: ['en', 'ko'], scale: 0.675 };
    box.appendChild(sb.render(sb.parse(code, options), options));
  } catch (e) {
    const pre = document.createElement('pre');
    pre.textContent = code;
    box.appendChild(pre);
  }
  return box;
}

function renderContentBlock(b) {
  if (b.type === 'text') {
    const d = document.createElement('div');
    d.className = 'md';
    d.innerHTML = renderMarkdown(t(b.value));
    return d;
  }
  if (b.type === 'image') {
    const img = document.createElement('img');
    img.className = 'ss-image';
    img.src = `${config.unitBase}/${b.src}`;
    img.alt = t(b.alt);
    return img;
  }
  if (b.type === 'video') {
    const id = youtubeId(b.youtube);
    const f = document.createElement('iframe');
    f.className = 'ss-video';
    f.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id || '')}`;
    f.allow = 'encrypted-media; picture-in-picture';
    f.allowFullscreen = true;
    return f;
  }
  if (b.type === 'blocks') return renderBlocksCode(t(b.value));
  return document.createComment(`unknown block: ${b.type}`);
}

function renderSubmitForm() {
  const f = state.form;
  const intro = state.editing
    ? '지난번에 쓴 내용이 들어 있어요. 고칠 곳만 고쳐서 다시 제출하세요. 지금 무대 화면이 새로 제출되고, 이전 작품도 그대로 남아요.'
    : '만든 작품을 선생님과 친구들에게 보여 주세요. 지금 무대 화면도 함께 제출돼요.';
  const wrap = document.createElement('div');
  wrap.style.display = 'contents';
  wrap.innerHTML = `
    <div class="md"><p>${intro}</p></div>
    <div class="ss-field">
      <label class="ss-label" for="f-title">작품 제목</label>
      <input class="ss-input" id="f-title" data-field="title" placeholder="예) 해적선 대포" value="${escapeHtml(f.title)}">
    </div>
    <div class="ss-field-group">
      <div class="ss-label-lg">배움 노트</div>
      <div class="ss-field">
        <label class="ss-label-sub" for="f-note">오늘 배운 내용과 재밌었던 점을 적어주세요.</label>
        <textarea class="ss-textarea" id="f-note" data-field="note" placeholder="예) 오늘은 ~을 배웠어요. ~부분이 재밌었어요">${escapeHtml(f.note)}</textarea>
      </div>
      <div class="ss-field">
        <label class="ss-label-sub" for="f-note2">무엇이 어려웠고 어떻게 해결했나요?</label>
        <textarea class="ss-textarea" id="f-note2" data-field="note2" placeholder="예) ~부분이 어려웠는데, ~하게 해결했어요">${escapeHtml(f.note2)}</textarea>
      </div>
    </div>
    <div class="ss-field">
      <label class="ss-label" for="f-yt">영상 링크 <span class="ss-optional">(선택)</span></label>
      <input class="ss-input" id="f-yt" data-field="yt" placeholder="https://youtube.com/..." value="${escapeHtml(f.yt)}">
      <div class="ss-field-error" id="f-yt-error" hidden>유튜브 주소만 넣을 수 있어요.</div>
    </div>`;
  wrap.addEventListener('input', (e) => {
    const field = e.target.dataset.field;
    if (!field) return;
    state.form[field] = e.target.value;
    renderChrome();
  });
  return wrap;
}

function formatSubmittedAt(ms) {
  return new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true }).format(new Date(ms));
}

function renderSubmitDone() {
  const s = state.submission;
  const wrap = document.createElement('div');
  wrap.style.display = 'contents';
  wrap.innerHTML = `
    <img class="ss-thumb" alt="제출한 무대 화면" src="${escapeHtml(s.thumbDataUrl || '')}">
    <div class="ss-done">
      <div class="ss-done-title">${escapeHtml(s.title)}</div>
      <div class="ss-done-status"><span>✓</span>제출했어요</div>
      <div class="ss-done-meta">${s.count}번째 제출 · ${formatSubmittedAt(s.at)}</div>
    </div>
    <div class="ss-resubmit">
      작품을 업데이트했다면 다시 제출할 수 있어요.
      <button type="button" id="resubmitBtn">다시 제출하기</button>
    </div>`;
  wrap.querySelector('#resubmitBtn').addEventListener('click', startResubmit);
  return wrap;
}

function renderBody() {
  const step = current();
  el.body.replaceChildren();
  const h = document.createElement('h1');
  h.className = 'ss-step-title';
  h.textContent = step.type === 'submit' ? (state.editing ? '다시 제출하기' : '프로젝트 제출') : t(step.title);
  el.body.appendChild(h);

  if (step.type === 'submit') el.body.appendChild(state.submission && !state.editing ? renderSubmitDone() : renderSubmitForm());
  else for (const b of step.content || []) el.body.appendChild(renderContentBlock(b));
  el.body.scrollTop = 0;
}

// ---- 진행 점, 결과 띠, 버튼 ----

function formState() {
  const f = state.form;
  const ytOk = !f.yt.trim() || isYoutubeUrl(f.yt.trim());
  return { ytOk, ok: !!(f.title.trim() && f.note.trim() && f.note2.trim()) && ytOk };
}

function primaryAction() {
  const step = current();
  if (step.type === 'submit') {
    if (state.submitting) return { label: '제출 중', disabled: true, spin: true };
    if (state.editing) return { label: '다시 제출', disabled: !formState().ok, on: submit };
    if (state.submission) return { label: '단원 목록으로', on: exit };
    return { label: '제출', disabled: !formState().ok, on: submit };
  }
  if (isPassed(state.step) || !step.hasChecks) return { label: '다음 ›', on: next };
  if (state.result === 'grading') return { label: '확인 중', disabled: true, spin: true };
  return { label: '확인', disabled: !state.editorReady, on: check };
}

function renderChrome() {
  const n = state.steps.length;
  for (const box of document.querySelectorAll('[data-dots]')) {
    box.classList.toggle('is-dense', n > 10);
    box.replaceChildren(...state.steps.map((_, i) => {
      const d = document.createElement('div');
      d.className = 'ss-dot' + (isPassed(i) ? ' is-passed' : '') + (i === state.step ? ' is-current' : '');
      return d;
    }));
  }
  el.stepLabel.textContent = `${state.step + 1} / ${n}`;
  el.stepShort.textContent = `${state.step + 1}/${n}`;
  el.unitTitle.textContent = t(state.unit.title);

  const band = BANDS[state.result];
  el.band.hidden = !band;
  if (band) {
    el.band.className = `ss-band ${band.cls}`;
    el.bandIcon.dataset.icon = band.icon;
    el.bandText.textContent = band.text;
  }

  el.prev.textContent = state.editing ? '취소' : '‹ 이전';
  el.prev.disabled = state.submitting || (!state.editing && state.step === 0);

  const prim = primaryAction();
  el.primary.disabled = !!prim.disabled;
  el.primary.replaceChildren();
  if (prim.spin) {
    const sp = document.createElement('span');
    sp.className = 'ss-spinner';
    el.primary.appendChild(sp);
  }
  el.primary.append(prim.label);
  el.primary.onclick = prim.on || null;

  const ytInput = el.body.querySelector('#f-yt');
  if (ytInput) {
    const { ytOk } = formState();
    ytInput.classList.toggle('is-invalid', !ytOk);
    el.body.querySelector('#f-yt-error').hidden = ytOk;
  }
}

function renderLayout() {
  el.strip.hidden = state.panelOpen;
  el.panel.hidden = !state.panelOpen;
  el.resizer.hidden = !state.panelOpen;
  el.app.style.setProperty('--panel-w', `${state.panelW}px`);
}

function goTo(i) {
  state.step = Math.max(0, Math.min(state.steps.length - 1, i));
  state.result = null;
  renderBody();
  renderChrome();
}

// ---- 스텝 진행 ----

async function next() {
  const step = current();
  if (!isPassed(state.step) && !step.hasChecks) await store.completeStep(step.key);
  goTo(state.step + 1);
}

function prev() {
  if (state.editing) return cancelResubmit();
  goTo(state.step - 1);
}

async function check() {
  const step = current();
  state.result = 'grading';
  renderChrome();
  let result = 'error', sb3 = null;
  try {
    const checks = await store.getChecks(step.key);
    const res = await frame.grade(checks);
    result = ['pass', 'fail'].includes(res.result) ? res.result : 'error';
    sb3 = res.sb3 || null;
  } catch (e) {
    console.warn('[scratch-studio] grade failed', e);
  }
  if (result !== 'error') {
    setSaveStatus('saving');
    try {
      await store.recordGrade(step.key, result, sb3);
      state.dirty = false;
      setSaveStatus('saved');
    } catch (e) {
      console.warn('[scratch-studio] record failed', e);
      setSaveStatus('failed');
      result = 'error';
    }
  }
  if (current() !== step) return;
  state.result = result;
  renderChrome();
}

// ---- 저장 ----

function setSaveStatus(status) {
  if (state.editorReady) frame.setSaveStatus(status);
}

async function save(force) {
  if (state.saving || !state.editorReady || (!state.dirty && !force)) return;
  state.saving = true;
  setSaveStatus('saving');
  try {
    const { sb3 } = await frame.exportProject();
    state.dirty = false;
    try { await store.saveProject(sb3); } catch (e) { state.dirty = true; throw e; }
    setSaveStatus('saved');
  } catch (e) {
    console.warn('[scratch-studio] save failed', e);
    setSaveStatus('failed');
  } finally {
    state.saving = false;
  }
}

// ---- 프로젝트 제출 ----

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = () => reject(r.error);
    r.readAsDataURL(blob);
  });
}

async function submit() {
  const wasEditing = state.editing;
  state.submitting = true;
  state.result = null;
  renderChrome();
  try {
    const { sb3 } = await frame.exportProject();
    const { png } = await frame.captureStage();
    const thumbDataUrl = await blobToDataUrl(new Blob([png], { type: 'image/png' }));
    const f = state.form;
    state.submission = await store.submit({ title: f.title.trim(), note: f.note.trim(), note2: f.note2.trim(), yt: f.yt.trim(), sb3, thumbDataUrl });
    state.editing = false;
    state.result = wasEditing ? 'resubmitted' : null;
  } catch (e) {
    console.warn('[scratch-studio] submit failed', e);
    state.result = 'submitError';
  }
  state.submitting = false;
  renderBody();
  renderChrome();
}

function fillFormFromSubmission() {
  const s = state.submission;
  state.form = s ? { title: s.title, note: s.note, note2: s.note2, yt: s.yt || '' } : { title: '', note: '', note2: '', yt: '' };
}

function startResubmit() {
  fillFormFromSubmission();
  state.editing = true;
  state.result = null;
  renderBody();
  renderChrome();
}

function cancelResubmit() {
  fillFormFromSubmission();
  state.editing = false;
  state.result = null;
  renderBody();
  renderChrome();
}

function exit() {
  if (config.exitUrl) location.href = config.exitUrl;
  else history.back();
}

// ---- 패널 접기와 너비 조절 ----

function bindLayout() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    if (btn.dataset.action === 'exit') exit();
    if (btn.dataset.action === 'open') { state.panelOpen = true; renderLayout(); }
    if (btn.dataset.action === 'close') { state.panelOpen = false; renderLayout(); }
  });
  el.prev.addEventListener('click', prev);

  el.resizer.addEventListener('mousedown', (e) => {
    e.preventDefault();
    const x0 = e.clientX, w0 = state.panelW;
    const move = (ev) => {
      state.panelW = Math.max(PANEL_MIN, Math.min(PANEL_MAX, w0 + ev.clientX - x0));
      renderLayout();
    };
    const up = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
      el.app.classList.remove('is-dragging');
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
    el.app.classList.add('is-dragging');
  });

  window.addEventListener('beforeunload', (e) => {
    if (!state.dirty) return;
    e.preventDefault();
    e.returnValue = '';
  });
}

// ---- 에디터 연결 ----

function bindEditor() {
  frame = new ScratchStudioFrame(el.iframe, { origin: editorUrl.origin });
  frame.addEventListener('projectChanged', () => { state.dirty = true; });
  frame.addEventListener('saveRequested', () => save(true));
  frame.addEventListener('localeChanged', (e) => {
    const locale = e.detail.locale === 'en' ? 'en' : 'ko';
    if (locale === state.locale) return;
    state.locale = locale;
    try { localStorage.setItem(LOCALE_KEY, locale); } catch (err) { /* 저장하지 못해도 화면은 바꾼다 */ }
    renderBody();
    renderChrome();
  });
  frame.addEventListener('error', (e) => console.warn('[scratch-studio] editor error', e.detail));
  el.iframe.src = editorUrl.href;
  setInterval(() => save(false), AUTOSAVE_MS);
}

async function start() {
  bindLayout();
  renderLayout();

  const res = await fetch(`${config.unitBase}/unit.json`);
  if (!res.ok) throw new Error(`unit.json을 불러오지 못했어요 (${res.status})`);
  const unit = await res.json();
  state.unit = unit;
  store = createStore(unit, { failFirstSave: config.failFirstSave });

  // 미니퀴즈와 프로젝트 제출은 unit.json이 아니라 사이트가 단원에 배치한다. 여기서는 제출 스텝만 끝에 붙인다.
  state.steps = unit.steps.map((s) => ({ type: 'lesson', key: s.key, title: s.title, content: s.content, hasChecks: (s.checks || []).length > 0 }));
  state.steps.push({ type: 'submit', key: SUBMIT_KEY });

  state.submission = store.getProgress().submission;
  fillFormFromSubmission();

  // 완료되지 않은 첫 스텝에서 이어서 한다.
  const firstOpen = state.steps.findIndex((_, i) => !isPassed(i));
  state.step = firstOpen < 0 ? state.steps.length - 1 : firstOpen;
  renderBody();
  renderChrome();

  bindEditor();
  await frame.ready;
  frame.init(state.locale, 'edit');
  await frame.loadProject(await store.loadProject(config.unitBase));
  state.editorReady = true;
  el.loading.hidden = true;
  frame.setSaveStatus('saved');
  renderChrome();
}

start().catch((e) => {
  console.error(e);
  el.loading.hidden = false;
  el.loading.classList.add('is-error');
  el.loading.querySelector('.ss-loading-title').textContent = '화면을 불러오지 못했어요';
  el.loading.querySelector('.ss-loading-sub').textContent = '새로 고침해 주세요';
});
