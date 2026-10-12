// 본 사이트와 에디터가 주고받는 메시지 규약 (기획서 4장).
// 실제 기준은 에디터 저장소의 protocol.ts이고, 이 파일은 같은 정의를 따른다.

export const SOURCE = 'scratch-studio';
export const VERSION = 1;

export const TIMEOUT_MS = {
  loadProject: 15000,
  exportProject: 15000,
  captureStage: 15000,
  gradeMargin: 5000,
  dynamicCheckDefault: 5000,
};

export function makeMessage(type, payload, requestId) {
  return { source: SOURCE, version: VERSION, type, requestId, payload };
}

export function isProtocolMessage(data) {
  return !!data && typeof data === 'object' && data.source === SOURCE && typeof data.type === 'string';
}

// grade 요청의 제한 시간: 동적 검사마다 timeoutMs × runs를 모두 더하고 5초를 더한다.
export function gradeTimeoutMs(checks) {
  let total = 0;
  const walk = (list) => {
    for (const c of list || []) {
      if (c.type === 'anyOf') walk(c.checks);
      else if (c.type === 'dynamic') total += (c.timeoutMs || TIMEOUT_MS.dynamicCheckDefault) * (c.runs || 1);
    }
  };
  walk(checks);
  return total + TIMEOUT_MS.gradeMargin;
}
