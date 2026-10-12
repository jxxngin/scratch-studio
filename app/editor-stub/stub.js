// 에디터 자리(stub). 기획서 4장의 메시지 규약에서 에디터 쪽 절반을 흉내 낸다.
// 채점은 실제로 하지 않고, 화면에서 고른 결과를 그대로 돌려준다.

import { VERSION, makeMessage, isProtocolMessage } from '../protocol.js';

// 실제 에디터에서는 빌드 설정으로 허용 출처를 지정한다.
const ALLOWED_ORIGINS = [new URLSearchParams(location.search).get('parent') || location.origin];
const parentOrigin = ALLOWED_ORIGINS[0];

const LABELS = {
  ko: { file: '파일', edit: '편집', code: '코드', costumes: '모양', sounds: '소리', sprite: '스프라이트', stage: '무대', cats: ['동작', '형태', '소리', '이벤트', '제어', '감지', '연산', '변수'] },
  en: { file: 'File', edit: 'Edit', code: 'Code', costumes: 'Costumes', sounds: 'Sounds', sprite: 'Sprite', stage: 'Stage', cats: ['Motion', 'Looks', 'Sound', 'Events', 'Control', 'Sensing', 'Operators', 'Variables'] },
};
const CAT_COLORS = ['#4C97FF', '#9966FF', '#CF63CF', '#FFBF00', '#FFAB19', '#5CB1D6', '#59C059', '#FF8C1A'];
const SAVE_LABELS = { saved: '저장됨', saving: '저장 중', failed: '저장 실패' };

const $ = (id) => document.getElementById(id);
let locale = 'ko';
let project = new ArrayBuffer(0);
let edits = 0;

function post(type, payload, requestId, transfer) {
  window.parent.postMessage(makeMessage(type, payload, requestId), parentOrigin, transfer || []);
}

function applyLocale() {
  const L = LABELS[locale];
  for (const node of document.querySelectorAll('[data-i18n]')) node.textContent = L[node.dataset.i18n];
  $('cats').replaceChildren(...L.cats.map((name, i) => {
    const d = document.createElement('div');
    d.className = 'cat';
    const dot = document.createElement('span');
    dot.style.background = CAT_COLORS[i];
    d.append(dot, name);
    return d;
  }));
}

function drawStage() {
  const c = $('stage'), g = c.getContext('2d');
  const sky = g.createLinearGradient(0, 0, 0, 280);
  sky.addColorStop(0, '#6fb7e8');
  sky.addColorStop(1, '#cfeaf8');
  g.fillStyle = sky;
  g.fillRect(0, 0, 480, 280);
  g.fillStyle = '#2f7fb8';
  g.fillRect(0, 280, 480, 80);
  g.fillStyle = 'rgba(30,41,59,.55)';
  g.font = '12px ui-monospace, Menlo, monospace';
  g.fillText(`무대 화면 (stub) · 변경 ${edits}회`, 12, 24);
}

function showProjectInfo() {
  $('projectInfo').textContent = `열린 작품: ${project.byteLength ? `${project.byteLength.toLocaleString()} bytes` : '빈 프로젝트'} · 변경 ${edits}회`;
}

function setSaveStatus(status) {
  $('saveStatus').dataset.status = status;
  $('saveLabel').textContent = SAVE_LABELS[status] || '';
  $('saveBtn').disabled = status === 'saving';
  $('retryBtn').hidden = status !== 'failed';
}

const handlers = {
  init({ locale: l, mode }) {
    locale = l === 'en' ? 'en' : 'ko';
    document.body.dataset.mode = mode || 'edit';
    applyLocale();
  },
  setMode({ mode }) { document.body.dataset.mode = mode; },
  setSaveStatus({ status }) { setSaveStatus(status); },
  loadProject({ sb3 }, requestId) {
    project = sb3 || new ArrayBuffer(0);
    edits = 0;
    showProjectInfo();
    drawStage();
    post('loadProject', {}, requestId);
  },
  exportProject(_, requestId) {
    const sb3 = project.slice(0);
    post('exportProject', { sb3 }, requestId, [sb3]);
  },
  captureStage(_, requestId) {
    $('stage').toBlob(async (blob) => {
      const png = await blob.arrayBuffer();
      post('captureStage', { png }, requestId, [png]);
    }, 'image/png');
  },
  grade({ checks }, requestId) {
    const choice = $('gradeResult').value;
    if (choice === 'timeout') return;
    setTimeout(() => {
      const sb3 = project.slice(0);
      const checkResults = (checks || []).map((c) => ({ type: c.type, rule: c.rule, pass: choice === 'pass' }));
      post('grade', { result: choice, checkResults, sb3 }, requestId, [sb3]);
    }, 1200);
  },
};

window.addEventListener('message', (e) => {
  if (!ALLOWED_ORIGINS.includes(e.origin) || e.source !== window.parent) return;
  const msg = e.data;
  if (!isProtocolMessage(msg)) return;
  if (msg.version !== VERSION) return post('error', { code: 'unsupported_version', message: `version ${msg.version}` }, msg.requestId);
  const handler = handlers[msg.type];
  if (!handler) return post('error', { code: 'unknown_type', message: msg.type }, msg.requestId);
  try { handler(msg.payload || {}, msg.requestId); }
  catch (err) { post('error', { code: 'failed', message: String(err && err.message) }, msg.requestId); }
});

$('langBtn').addEventListener('click', () => { $('langMenu').hidden = !$('langMenu').hidden; });
$('langMenu').addEventListener('click', (e) => {
  const l = e.target.dataset.locale;
  if (!l) return;
  $('langMenu').hidden = true;
  locale = l;
  applyLocale();
  post('localeChanged', { locale });
});
$('saveBtn').addEventListener('click', () => post('saveRequested'));
$('retryBtn').addEventListener('click', () => post('saveRequested'));
$('changeBtn').addEventListener('click', () => {
  edits++;
  showProjectInfo();
  drawStage();
  if (document.body.dataset.mode === 'edit') post('projectChanged');
});

applyLocale();
drawStage();
showProjectInfo();
post('ready');
