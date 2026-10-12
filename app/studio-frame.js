// 에디터 iframe과 통신하는 얇은 클라이언트 (기획서 3장의 ScratchStudioFrame).
// 에디터나 채점 엔진의 코드는 여기에 들어오지 않는다. 메시지만 주고받는다.

import { VERSION, TIMEOUT_MS, makeMessage, isProtocolMessage, gradeTimeoutMs } from './protocol.js';

export class ScratchStudioFrame extends EventTarget {
  constructor(iframe, { origin }) {
    super();
    this.iframe = iframe;
    this.origin = origin;
    this.pending = new Map();
    this.seq = 0;
    this.ready = new Promise((resolve) => { this._resolveReady = resolve; });
    this._onMessage = this._onMessage.bind(this);
    window.addEventListener('message', this._onMessage);
  }

  destroy() {
    window.removeEventListener('message', this._onMessage);
    for (const p of this.pending.values()) {
      clearTimeout(p.timer);
      p.reject(new Error('frame destroyed'));
    }
    this.pending.clear();
  }

  _onMessage(e) {
    if (e.origin !== this.origin || e.source !== this.iframe.contentWindow) return;
    const msg = e.data;
    if (!isProtocolMessage(msg) || msg.version !== VERSION) return;

    const p = msg.requestId && this.pending.get(msg.requestId);
    if (p) {
      this.pending.delete(msg.requestId);
      clearTimeout(p.timer);
      if (msg.type === 'error') p.reject(Object.assign(new Error(msg.payload && msg.payload.message), { code: msg.payload && msg.payload.code }));
      else p.resolve(msg.payload || {});
      return;
    }
    if (msg.type === 'ready') this._resolveReady();
    this.dispatchEvent(new CustomEvent(msg.type, { detail: msg.payload || {} }));
  }

  send(type, payload, transfer) {
    this.iframe.contentWindow.postMessage(makeMessage(type, payload), this.origin, transfer || []);
  }

  request(type, payload, { timeoutMs, transfer } = {}) {
    const requestId = `r${++this.seq}`;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(requestId);
        reject(Object.assign(new Error(`${type} timed out`), { code: 'timeout' }));
      }, timeoutMs);
      this.pending.set(requestId, { resolve, reject, timer });
      this.iframe.contentWindow.postMessage(makeMessage(type, payload, requestId), this.origin, transfer || []);
    });
  }

  init(locale, mode) { this.send('init', { locale, mode }); }
  setMode(mode) { this.send('setMode', { mode }); }
  setSaveStatus(status) { this.send('setSaveStatus', { status }); }

  // sb3는 넘기면 이쪽 버퍼가 비워지므로 복사본을 넘긴다.
  loadProject(sb3) {
    const buf = sb3 ? sb3.slice(0) : null;
    return this.request('loadProject', { sb3: buf }, { timeoutMs: TIMEOUT_MS.loadProject, transfer: buf ? [buf] : [] });
  }
  exportProject() { return this.request('exportProject', undefined, { timeoutMs: TIMEOUT_MS.exportProject }); }
  captureStage() { return this.request('captureStage', undefined, { timeoutMs: TIMEOUT_MS.captureStage }); }
  grade(checks) { return this.request('grade', { checks }, { timeoutMs: gradeTimeoutMs(checks) }); }
}
