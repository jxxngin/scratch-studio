// 스크래치 전용 학습 화면 (기획서 5장, hi-fi 목업 화면 15).
// 교안 패널과 버튼은 이 화면이 그리고, 에디터는 iframe으로 띄워 메시지로만 통신한다.

import { renderMarkdown, renderInline } from './markdown.js';
import { ScratchStudioFrame } from './studio-frame.js';
import { createStore, isYoutubeUrl, youtubeId } from './store.js';
import { installDevSkip } from './dev-skip.js'; // [임시] dev-skip

const params = new URLSearchParams(location.search);
const unitBase = (params.get('unit') || '../project/lv1/04-pirate-cannon').replace(/\/$/, '');
// [임시] home: exit가 없으면 "종료"는 교안 확인용 홈 화면의 그 레벨 목록으로 간다. 홈 화면을 없앨 때 이 줄도 ''로 되돌린다.
const homeExit = `./home/#lv${(unitBase.match(/\/lv(\d)\//) || [])[1] || 1}`;
const config = {
  unitBase,
  editorUrl: params.get('editor') || './editor-stub/index.html',
  exitUrl: params.get('exit') || homeExit,
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
  progress: $('progress'), tocBtn: $('tocBtn'), toc: $('toc'), chapterName: $('chapterName'),
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
  quiz: {},            // 현재 퀴즈 스텝에서 고른 보기: { 문항 id: 보기 번호 }
  chapters: null,      // 목차 (unit.json의 chapters가 있을 때)
  tocExpanded: null,   // 목차에서 펼친 목차
};
let store, frame;
let devSkip = null; // [임시] dev-skip

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

// 입력 표: 학생이 예상과 결과를 직접 적는 표. 적은 값은 저장한다.
// 열: { label, input?, kind?, options?, requires?, of? }
//   kind: 'text'(기본), 'number', 'select'(options 중 하나를 고르고 보기 번호를 저장),
//         'verify'(해 보니: [맞았어요] [달랐어요]. 달랐으면 of 열과 같은 종류의 칸에 실제 값을 적는다)
//   requires: 같은 줄에서 먼저 채워야 하는 열 번호 (예상을 적어야 결과 칸이 열림)
//   of: verify 열이 확인하는 예상 열 번호. 저장 값은 'same' 또는 'diff:<실제 값>'
// 줄: 칸 배열. 고정 열은 글자, 입력 열은 null 또는 { placeholder?, answer? }
//   answer가 있는 칸은 스텝의 { "type": "record" } 검사가 채점한다 (store.checkRecords)
const GUESS_FIRST = { ko: '예상 먼저', en: 'Guess first' };
const CHOOSE = { ko: '고르기', en: 'Choose' };

function renderRecordInput(col, cell) {
  if (col.kind === 'select') {
    const sel = document.createElement('select');
    sel.className = 'ss-record-input';
    sel.add(new Option(t(CHOOSE), ''));
    col.options.forEach((o, oi) => sel.add(new Option(t(o), String(oi))));
    return sel;
  }
  const input = document.createElement('input');
  input.className = 'ss-record-input';
  if (col.kind === 'number') input.inputMode = 'decimal';
  input.dataset.placeholder = cell && cell.placeholder ? t(cell.placeholder) : '';
  return input;
}

function setLocked(input, locked) {
  input.disabled = locked;
  if (input.tagName === 'SELECT') input.options[0].text = t(locked ? GUESS_FIRST : CHOOSE);
  else input.placeholder = locked ? t(GUESS_FIRST) : input.dataset.placeholder;
}

// 해 보니 칸: [맞았어요] [달랐어요], 달랐으면 실제 값 칸
function renderVerify(guessCol, value, onChange) {
  const box = document.createElement('div');
  box.className = 'ss-verify';
  const same = document.createElement('button');
  const diff = document.createElement('button');
  same.type = diff.type = 'button';
  same.className = 'ss-verify-btn is-same';
  diff.className = 'ss-verify-btn is-diff';
  same.textContent = t({ ko: '맞았어요', en: 'Same' });
  diff.textContent = t({ ko: '달랐어요', en: 'Different' });
  const actual = renderRecordInput(guessCol, null);
  actual.classList.add('ss-verify-actual');
  const v = { current: value };
  const paint = () => {
    const isSame = v.current === 'same';
    const isDiff = v.current.startsWith('diff:');
    same.classList.toggle('is-on', isSame);
    diff.classList.toggle('is-on', isDiff);
    actual.hidden = !isDiff;
    if (isDiff) actual.value = v.current.slice(5);
  };
  same.addEventListener('click', () => { v.current = 'same'; paint(); onChange(v.current); });
  diff.addEventListener('click', () => { v.current = 'diff:' + (v.current.startsWith('diff:') ? v.current.slice(5) : ''); paint(); onChange(v.current); actual.focus(); });
  actual.addEventListener(actual.tagName === 'SELECT' ? 'change' : 'input', () => { v.current = 'diff:' + actual.value; onChange(v.current); });
  const buttons = document.createElement('div');
  buttons.className = 'ss-verify-buttons';
  buttons.append(same, diff);
  box.append(buttons, actual);
  paint();
  return {
    el: box,
    lock(locked) {
      same.disabled = diff.disabled = actual.disabled = locked;
      box.classList.toggle('is-locked', locked);
      box.title = locked ? t(GUESS_FIRST) : '';
    },
  };
}

function renderRecord(b, stepKey) {
  const saved = store.getRecord(stepKey, b.key) || [];
  const values = b.rows.map((row, ri) => row.map((_, ci) => (saved[ri] && saved[ri][ci]) || ''));
  const wrap = document.createElement('div');
  wrap.className = 'md md-table ss-record';
  const table = document.createElement('table');
  const head = table.createTHead().insertRow();
  for (const col of b.columns) {
    const th = document.createElement('th');
    th.textContent = t(col.label);
    head.appendChild(th);
  }
  const body = table.createTBody();
  const parts = [];
  const update = () => {
    for (const { lock, ri, col } of parts) {
      const need = col.kind === 'verify' ? col.of : col.requires;
      lock(need != null && !values[ri][need].trim());
    }
  };
  const save = (ri, ci, v) => {
    if (state.result === 'fail') { state.result = null; renderChrome(); }
    values[ri][ci] = v;
    store.saveRecord(stepKey, b.key, values);
    update();
  };
  b.rows.forEach((row, ri) => {
    const tr = body.insertRow();
    row.forEach((cell, ci) => {
      const col = b.columns[ci];
      const td = tr.insertCell();
      if (!col.input) { td.innerHTML = renderInline(t(cell)); return; }
      if (col.kind === 'verify') {
        const vf = renderVerify(b.columns[col.of], values[ri][ci], (v) => save(ri, ci, v));
        parts.push({ lock: vf.lock, ri, col });
        td.appendChild(vf.el);
        return;
      }
      const input = renderRecordInput(col, cell);
      input.value = values[ri][ci];
      input.setAttribute('aria-label', `${t(b.columns[0].label)} ${t(row[0])} · ${t(col.label)}`);
      input.addEventListener(input.tagName === 'SELECT' ? 'change' : 'input', () => save(ri, ci, input.value));
      parts.push({ lock: (locked) => setLocked(input, locked), ri, col });
      td.appendChild(input);
    });
  });
  update();
  wrap.appendChild(table);
  return wrap;
}

// 문단 맨 앞의 굵은 소제목("**확인**: …")을 칩과 색 상자로 그린다. 교안 글은 그대로 두고 화면에서만 꾸민다.
const LABEL_KINDS = {
  goal: ['목표', 'Goal'],
  check: ['확인', 'Check'],
  challenge: ['도전', 'Challenge'],
  try: ['해 보기', 'Try'],
  tidy: ['정리', '먼저 정리', '되돌리기', 'Clean up', 'Clean up first', 'Undo'],
  think: ['어림해 보기', '그림 보기', '생각해 보기', 'Estimate', 'Look', 'Think about it'],
};
const LABEL_OF = Object.fromEntries(Object.entries(LABEL_KINDS).flatMap(([kind, names]) => names.map((n) => [n, kind])));

// 소제목 칩의 아이콘 (색을 구분하기 어려워도 모양으로 알아볼 수 있게)
const LABEL_ICONS = {
  goal: '<circle cx="8" cy="8" r="6.25"/><circle cx="8" cy="8" r="3"/><circle cx="8" cy="8" r=".9" fill="currentColor"/>',
  check: '<path d="M3 8.5l3.2 3L13 4.5"/>',
  challenge: '<path d="M8 1.8l1.9 3.9 4.2.6-3 3 .7 4.2L8 11.5l-3.8 2 .7-4.2-3-3 4.2-.6z" fill="currentColor" stroke-linejoin="round"/>',
  try: '<path d="M4.5 2.8v10.4L13 8z" fill="currentColor" stroke-linejoin="round"/>',
  tidy: '<path d="M3 4v3.5h3.5"/><path d="M3.4 7.2A5 5 0 1 1 4.5 11.6"/>',
  think: '<circle cx="8" cy="8" r="6.25"/><path d="M6.2 6.3a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.1v.4"/><circle cx="8" cy="11.6" r=".6" fill="currentColor"/>',
};

function labelChip(kind, text) {
  const chip = document.createElement('span');
  chip.className = `ss-label ss-label-${kind}`;
  chip.innerHTML = `<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">${LABEL_ICONS[kind]}</svg>`;
  chip.append(text);
  return chip;
}

function decorateLabels(div) {
  // "**목표**" 한 줄 뒤에 목록이 오는 블록은 목표 카드로
  const first = div.firstElementChild;
  if (first && first.tagName === 'P' && first.childNodes.length === 1 && first.firstChild.tagName === 'STRONG'
      && LABEL_OF[first.textContent] === 'goal') {
    div.classList.add('ss-goal');
    first.replaceWith(labelChip('goal', first.textContent));
  }
  for (const p of [...div.children]) {
    const strong = p.firstChild;
    if (p.tagName !== 'P' || !strong || strong.tagName !== 'STRONG') continue;
    const kind = LABEL_OF[strong.textContent];
    const rest = strong.nextSibling;
    if (!kind || kind === 'goal' || !rest || rest.nodeType !== Node.TEXT_NODE || !rest.textContent.startsWith(':')) continue;
    rest.textContent = rest.textContent.replace(/^:\s*/, '');
    const box = document.createElement('div');
    box.className = `ss-callout ss-callout-${kind}`;
    p.replaceWith(box);
    strong.remove();
    box.append(labelChip(kind, strong.textContent), p);
  }
  return div;
}

function renderContentBlock(b, stepKey) {
  if (b.type === 'record') return renderRecord(b, stepKey);
  if (b.type === 'text') {
    const d = document.createElement('div');
    d.className = 'md';
    d.innerHTML = renderMarkdown(t(b.value));
    return decorateLabels(d);
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

function renderQuiz(step) {
  const passed = isPassed(state.step);
  const wrap = document.createElement('div');
  wrap.className = 'ss-quiz';
  step.questions.forEach((q, qi) => {
    const box = document.createElement('div');
    box.className = 'ss-question';
    box.dataset.qid = q.id;
    const no = document.createElement('div');
    no.className = 'ss-question-no';
    no.textContent = `문제 ${qi + 1} / ${step.questions.length}`;
    const prompt = document.createElement('div');
    prompt.className = 'md ss-question-prompt';
    prompt.innerHTML = renderMarkdown(t(q.prompt));
    box.append(no, prompt);
    if (q.image) box.appendChild(renderContentBlock({ type: 'image', src: q.image, alt: q.prompt }));
    if (q.blocks) box.appendChild(renderBlocksCode(t(q.blocks)));

    const options = document.createElement('div');
    options.className = 'ss-options';
    q.options.forEach((o, oi) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ss-option' + (state.quiz[q.id] === oi ? ' is-selected' : '');
      btn.disabled = passed;
      const radio = document.createElement('span');
      radio.className = 'ss-radio';
      btn.append(radio, t(o));
      btn.addEventListener('click', () => {
        if (state.result === 'grading') return;
        state.quiz[q.id] = oi;
        state.result = null;
        for (const b of options.children) b.classList.toggle('is-selected', b === btn);
        renderChrome();
      });
      options.appendChild(btn);
    });
    box.appendChild(options);
    // 틀린 문항은 따로 표시하지 않고, 그 문항 아래에 힌트만 보여 준다. 해설은 통과한 뒤에 모든 문항에 보여 준다.
    if (q.hint && !passed) {
      const hint = document.createElement('div');
      hint.className = 'ss-hint';
      hint.innerHTML = `<div class="ss-hint-label">${t({ ko: '힌트', en: 'Hint' })}</div>`;
      const body = document.createElement('div');
      body.className = 'md';
      body.innerHTML = renderMarkdown(t(q.hint));
      hint.appendChild(body);
      box.appendChild(hint);
    }
    if (passed && q.explain) {
      const ex = document.createElement('div');
      ex.className = 'ss-explain';
      ex.textContent = t(q.explain);
      box.appendChild(ex);
    }
    wrap.appendChild(box);
  });
  return wrap;
}

function renderSubmitForm() {
  const f = state.form;
  const intro = state.editing
    ? '지난번에 쓴 내용이 들어 있어요. 고칠 곳만 고쳐서 다시 제출하세요. 지금 무대 화면이 새로 제출되고, 이전 작품도 그대로 남아요.'
    : '만든 작품을 선생님과 친구들에게 보여 주세요. 지금 무대 화면도 함께 제출돼요.';
  // 작품 제목 예시는 그 단원의 원래 이름으로 보여 준다. 사이트 문구는 한국어만이라 ko 값을 쓴다.
  const titleExample = (state.unit && state.unit.title && state.unit.title.ko) || '';
  const wrap = document.createElement('div');
  wrap.style.display = 'contents';
  wrap.innerHTML = `
    <div class="md"><p>${intro}</p></div>
    <div class="ss-field">
      <label class="ss-label" for="f-title">작품 제목</label>
      <input class="ss-input" id="f-title" data-field="title" placeholder="${titleExample ? `예) ${escapeHtml(titleExample)}` : ''}" value="${escapeHtml(f.title)}">
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
  else if (step.type === 'quiz') el.body.appendChild(renderQuiz(step));
  else for (const b of step.content || []) el.body.appendChild(renderContentBlock(b, step.key));
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
  if (step.type === 'quiz') return { label: '확인', disabled: !step.questions.every((q) => state.quiz[q.id] != null), on: checkQuiz };
  return { label: '확인', disabled: !state.editorReady, on: check };
}

// ---- 목차 ----
// unit.json의 chapters가 있으면 패널 위쪽에 "지금 목차 이름 + 그 목차의 점"만 보여 주고, 목차 버튼으로 전체 목차를 펼친다.
// 제출 스텝은 사이트가 붙이므로 맨 끝에 따로 한 줄로 둔다. chapters가 없는 교안은 전체 점을 그대로 보여 준다.

function buildChapters(unit) {
  if (!unit.chapters) return null;
  const index = Object.fromEntries(state.steps.map((s, i) => [s.key, i]));
  const chapters = unit.chapters.map((c, ci) => ({ no: ci + 1, title: c.title, steps: c.steps.map((k) => index[k]) }));
  const covered = chapters.flatMap((c) => c.steps);
  const missing = state.steps.map((_, i) => i).filter((i) => !covered.includes(i) && state.steps[i].type !== 'submit');
  if (missing.length) console.warn('[scratch-studio] steps not in any chapter', missing.map((i) => state.steps[i].key));
  chapters.push({ no: null, title: { ko: '제출', en: 'Submit' }, steps: [state.steps.length - 1] });
  return chapters;
}

const chapterOf = (i) => state.chapters.find((c) => c.steps.includes(i));
const firstOpenStep = () => {
  const i = state.steps.findIndex((_, k) => !isPassed(k));
  return i < 0 ? state.steps.length - 1 : i;
};
const chapterTitle = (c) => (c.no ? `${c.no}. ${t(c.title)}` : t(c.title));

function dot(i) {
  const d = document.createElement('div');
  d.className = 'ss-dot' + (isPassed(i) ? ' is-passed' : '') + (i === state.step ? ' is-current' : '');
  return d;
}

function renderToc() {
  const open = firstOpenStep();
  const cur = chapterOf(state.step);
  el.toc.replaceChildren();
  for (const c of state.chapters) {
    const done = c.steps.filter(isPassed).length;
    const locked = c.steps[0] > open;
    const expanded = state.tocExpanded === c;
    const head = document.createElement('button');
    head.type = 'button';
    head.className = 'ss-toc-chapter' + (c === cur ? ' is-current' : '') + (locked ? ' is-locked' : '');
    const mark = done === c.steps.length ? '✓' : locked ? '' : '●';
    head.innerHTML = `<span class="ss-toc-mark${locked ? ' is-lock' : ''}">${mark}</span>`
      + `<span class="ss-toc-title"></span><span class="ss-toc-count">${c.no ? `${done}/${c.steps.length}` : ''}</span>`;
    head.querySelector('.ss-toc-title').textContent = chapterTitle(c);
    head.addEventListener('click', () => {
      if (c.steps.length === 1) { if (!locked) { goTo(c.steps[0]); closeToc(); } return; }
      state.tocExpanded = expanded ? null : c;
      renderToc();
    });
    el.toc.appendChild(head);
    if (!expanded || c.steps.length === 1) continue;
    const list = document.createElement('div');
    list.className = 'ss-toc-steps';
    for (const i of c.steps) {
      const item = document.createElement('button');
      item.type = 'button';
      const reachable = i <= open;
      item.disabled = !reachable;
      item.className = 'ss-toc-step' + (i === state.step ? ' is-current' : '');
      const m = isPassed(i) ? '✓' : i === state.step ? '●' : reachable ? '○' : '';
      item.innerHTML = `<span class="ss-toc-mark${reachable ? '' : ' is-lock'}">${m}</span><span class="ss-toc-title"></span>`;
      item.querySelector('.ss-toc-title').textContent = state.steps[i].type === 'submit' ? '프로젝트 제출' : t(state.steps[i].title);
      item.addEventListener('click', () => { goTo(i); closeToc(); });
      list.appendChild(item);
    }
    el.toc.appendChild(list);
  }
}

function openToc() {
  state.tocExpanded = chapterOf(state.step);
  renderToc();
  el.toc.style.top = `${el.progress.offsetTop + el.progress.offsetHeight}px`;
  el.toc.hidden = false;
  el.tocBtn.setAttribute('aria-expanded', 'true');
  const cur = el.toc.querySelector('.ss-toc-step.is-current');
  if (cur) cur.scrollIntoView({ block: 'center' });
}
function closeToc() {
  el.toc.hidden = true;
  el.tocBtn.setAttribute('aria-expanded', 'false');
}

function renderChrome() {
  const n = state.steps.length;
  const cur = state.chapters && chapterOf(state.step);
  for (const box of document.querySelectorAll('[data-dots]')) {
    const steps = box.dataset.dots === 'panel' && cur ? cur.steps : state.steps.map((_, i) => i);
    box.classList.toggle('is-dense', steps.length > 10);
    box.replaceChildren(...steps.map(dot));
  }
  el.tocBtn.hidden = !state.chapters;
  el.chapterName.hidden = !cur;
  if (cur) el.chapterName.textContent = chapterTitle(cur);
  if (!el.toc.hidden) renderToc();
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
  if (devSkip) devSkip.update(current().hasChecks && current().type !== 'submit' && !isPassed(state.step)); // [임시] dev-skip

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
  loadQuizAnswers();
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

// 이미 통과한 퀴즈로 돌아오면 정답이 골라진 상태로 보여준다.
function loadQuizAnswers() {
  const step = current();
  state.quiz = {};
  if (step.type === 'quiz' && isPassed(state.step)) for (const q of step.questions) state.quiz[q.id] = q.answer;
}

async function checkQuiz() {
  const step = current();
  state.result = 'grading';
  renderChrome();
  let wrong = [];
  try {
    const res = await store.gradeQuiz(step.key, state.quiz);
    state.result = res.result;
    wrong = res.wrong;
  } catch (e) { console.warn('[scratch-studio] quiz failed', e); state.result = 'error'; }
  if (state.result === 'pass') renderBody();
  else if (state.result === 'fail') showQuizHints(wrong);
  renderChrome();
}

// 마지막 확인에서 틀린 문항에만 힌트를 보여 준다. 다시 확인하면 그 결과로 바뀐다.
function showQuizHints(wrong) {
  for (const box of el.body.querySelectorAll('.ss-question')) box.classList.toggle('show-hint', wrong.includes(box.dataset.qid));
}

async function check() {
  const step = current();
  state.result = 'grading';
  renderChrome();
  let result = 'error', sb3 = null;
  try {
    // 입력 표 채점(record)은 사이트가 하고, 나머지는 에디터가 한다. 입력 표가 틀리면 에디터 채점은 하지 않는다.
    const checks = await store.getChecks(step.key);
    const recordChecks = checks.filter((c) => c.type === 'record');
    const editorChecks = checks.filter((c) => c.type !== 'record');
    if (recordChecks.length && !store.checkRecords(step.key, recordChecks)) result = 'fail';
    else if (!editorChecks.length) result = 'pass';
    else {
      const res = await frame.grade(editorChecks);
      result = ['pass', 'fail'].includes(res.result) ? res.result : 'error';
      sb3 = res.sb3 || null;
    }
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

  // 목차: 버튼으로 열고 닫는다. 바깥을 누르거나 Esc를 누르면 닫힌다.
  el.tocBtn.addEventListener('click', () => (el.toc.hidden ? openToc() : closeToc()));
  document.addEventListener('click', (e) => {
    const path = e.composedPath();
    if (!el.toc.hidden && !path.includes(el.toc) && !path.includes(el.tocBtn)) closeToc();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !el.toc.hidden) closeToc(); });

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

// 퀴즈 스텝은 두 형식을 받는다.
// 기획서 6장: { "kind": "quiz", "questions": [{ "key", "question", "options", "answer" }] }
// 이전 교안: { "type": "quiz", "title", "questions": [{ "id", "prompt", "options", "answer", "hint", "explain" }] }
function normalizeUnit(unit) {
  for (const s of unit.steps) {
    if (s.kind !== 'quiz' && s.type !== 'quiz') continue;
    s.type = 'quiz';
    if (!s.title) s.title = { ko: '퀴즈', en: 'Quiz' };
    for (const q of s.questions || []) {
      if (q.id == null) q.id = q.key;
      if (q.prompt == null) q.prompt = q.question;
    }
  }
  return unit;
}

async function start() {
  bindLayout();
  devSkip = installDevSkip({ panel: el.panel, actions: $('actions'), onSkip: () => { store.devPass(current().key); goTo(state.step + 1); } }); // [임시] dev-skip
  renderLayout();

  const res = await fetch(`${config.unitBase}/unit.json`);
  if (!res.ok) throw new Error(`unit.json을 불러오지 못했어요 (${res.status})`);
  const unit = normalizeUnit(await res.json());
  state.unit = unit;
  store = createStore(unit, { failFirstSave: config.failFirstSave, namespace: params.get('unit') ? config.unitBase : '' });

  // 프로젝트 제출은 사이트가 배치하므로 끝에 붙인다.
  state.steps = unit.steps.map((s) => (s.type === 'quiz'
    ? { type: 'quiz', key: s.key, title: s.title, questions: s.questions || [], hasChecks: true }
    : { type: 'lesson', key: s.key, title: s.title, content: s.content, hasChecks: (s.checks || []).length > 0 }));
  state.steps.push({ type: 'submit', key: SUBMIT_KEY });
  state.chapters = buildChapters(unit);

  state.submission = store.getProgress().submission;
  fillFormFromSubmission();

  // 완료되지 않은 첫 스텝에서 이어서 한다.
  const firstOpen = state.steps.findIndex((_, i) => !isPassed(i));
  state.step = firstOpen < 0 ? state.steps.length - 1 : firstOpen;
  loadQuizAnswers();
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
