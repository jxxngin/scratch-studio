// 본 사이트 서버(API, DB, 파일 저장소)를 대신하는 브라우저 저장소.
// 함수 하나가 기획서 8장의 API 동작 하나에 대응한다. 실제 사이트에서는 이 파일만 서버 호출로 바꾼다.
// 진도와 제출 정보는 localStorage, sb3 파일은 IndexedDB에 둔다.

const MAX_VERSIONS = 10;
const MAX_SB3_BYTES = 20 * 1024 * 1024;

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('scratch-studio', 1);
    req.onupgradeneeded = () => req.result.createObjectStore('files');
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
async function idb(mode, fn) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('files', mode);
    const req = fn(tx.objectStore('files'));
    tx.oncomplete = () => resolve(req && req.result);
    tx.onerror = () => reject(tx.error);
  });
}

// namespace: 같은 단원의 다른 판(폴더)을 나란히 열어 볼 때 진도가 섞이지 않게 하는 개발용 구분값.
export function createStore(unit, { failFirstSave = false, namespace = '' } = {}) {
  const id = `${unit.subject}/${unit.unitKey}${namespace ? `@${namespace}` : ''}`;
  const key = `ss:${id}`;
  let failNext = failFirstSave;

  const read = () => {
    try { return Object.assign({ passed: [], attempts: {}, submission: null, versions: [] }, JSON.parse(localStorage.getItem(key) || '{}')); }
    catch (e) { return { passed: [], attempts: {}, submission: null, versions: [] }; }
  };
  const write = (s) => localStorage.setItem(key, JSON.stringify(s));

  const stepIndex = (stepKey) => unit.steps.findIndex((s) => s.key === stepKey);
  const previousAllPassed = (state, stepKey) => unit.steps.slice(0, stepIndex(stepKey)).every((s) => state.passed.includes(s.key));

  async function putWork(sb3) {
    if (failNext) { failNext = false; throw new Error('save failed (simulated)'); }
    if (sb3.byteLength > MAX_SB3_BYTES) throw new Error('sb3 too large');
    await idb('readwrite', (os) => os.put(sb3, `${id}:work`));
  }

  return {
    getProgress() {
      const s = read();
      return { passed: s.passed, submission: s.submission };
    },

    // 작품 불러오기: 저장본 → 시작 프로젝트 → 빈 프로젝트
    async loadProject(unitBase) {
      const saved = await idb('readonly', (os) => os.get(`${id}:work`));
      if (saved) return saved;
      if (!unit.starterProject) return null;
      const res = await fetch(`${unitBase}/${unit.starterProject}`);
      if (!res.ok) throw new Error('starter project not found');
      return res.arrayBuffer();
    },

    saveProject: putWork,

    // 채점 규칙 받기: 이전 스텝을 모두 통과한 학생에게 현재 스텝 것만 준다.
    async getChecks(stepKey) {
      if (!previousAllPassed(read(), stepKey)) throw new Error('step locked');
      return unit.steps[stepIndex(stepKey)].checks || [];
    },

    // 채점 결과 기록: 시도 횟수 증가, 통과 시 스텝 완료, 작품 저장. error는 시도 횟수에 넣지 않는다.
    async recordGrade(stepKey, result, sb3) {
      const s = read();
      if (!previousAllPassed(s, stepKey)) throw new Error('step locked');
      if (result === 'error') return;
      s.attempts[stepKey] = (s.attempts[stepKey] || 0) + 1;
      if (result === 'pass' && !s.passed.includes(stepKey)) s.passed.push(stepKey);
      write(s);
      if (sb3) await putWork(sb3);
    },

    // 채점 규칙이 없는 스텝은 읽고 넘어가면 완료다.
    async completeStep(stepKey) {
      const s = read();
      if (!previousAllPassed(s, stepKey)) throw new Error('step locked');
      const step = unit.steps[stepIndex(stepKey)];
      if ((step.checks || []).length || step.type === 'quiz') throw new Error('step needs grading');
      if (!s.passed.includes(stepKey)) { s.passed.push(stepKey); write(s); }
    },

    // 미니퀴즈 채점: 모든 문항이 정답이어야 통과. 다시 풀 수 있다.
    // 통과/실패만 돌려준다. 어느 문항이 틀렸는지는 알려 주지 않는다.
    async gradeQuiz(stepKey, answers) {
      const s = read();
      if (!previousAllPassed(s, stepKey)) throw new Error('step locked');
      const step = unit.steps[stepIndex(stepKey)];
      const pass = step.questions.every((q) => answers[q.id] === q.answer);
      s.attempts[stepKey] = (s.attempts[stepKey] || 0) + 1;
      if (pass && !s.passed.includes(stepKey)) s.passed.push(stepKey);
      write(s);
      return pass ? 'pass' : 'fail';
    },

    // 프로젝트 제출: 새 버전과 썸네일 저장. 작품당 최근 10개 버전만 보관한다.
    async submit({ title, note, note2, yt, sb3, thumbDataUrl }) {
      const s = read();
      if (!unit.steps.every((st) => s.passed.includes(st.key))) throw new Error('steps not finished');
      if (yt && !isYoutubeUrl(yt)) throw new Error('invalid video url');
      const count = ((s.submission && s.submission.count) || 0) + 1;
      await idb('readwrite', (os) => os.put(sb3, `${id}:v${count}`));
      s.versions.push(count);
      while (s.versions.length > MAX_VERSIONS) {
        const old = s.versions.shift();
        await idb('readwrite', (os) => os.delete(`${id}:v${old}`));
      }
      s.submission = { title, note, note2, yt, count, at: Date.now(), thumbDataUrl };
      write(s);
      return s.submission;
    },
  };
}

export function isYoutubeUrl(url) {
  try {
    const host = new URL(url).hostname.replace(/^www\.|^m\./, '');
    return host === 'youtube.com' || host === 'youtu.be';
  } catch (e) { return false; }
}

export function youtubeId(url) {
  try {
    const u = new URL(url);
    if (u.hostname.replace(/^www\./, '') === 'youtu.be') return u.pathname.slice(1);
    return u.searchParams.get('v') || (u.pathname.match(/\/(embed|shorts)\/([^/?]+)/) || [])[2] || null;
  } catch (e) { return null; }
}
