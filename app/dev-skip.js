// [임시] 교안 확인용 건너뛰기.
// 채점이 있는 스텝(만들기, 탐색, 꾸미기, 퀴즈)을 채점 없이 통과 처리하고 다음 스텝으로 넘어간다.
// 실제 수업에 쓸 때는 이 파일과, 이 파일을 쓰는 main.js에서 "dev-skip"으로 검색되는 줄과 store.js의 devPass를 지운다.

export function installDevSkip({ panel, actions, onSkip }) {
  const row = document.createElement('div');
  row.className = 'ss-dev-skip';
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.textContent = '건너뛰기 (교안 확인용)';
  btn.title = '채점 없이 이 스텝을 통과 처리하고 다음으로 넘어가요. 실제 수업용에서는 지울 임시 기능이에요.';
  btn.addEventListener('click', onSkip);
  row.appendChild(btn);
  panel.insertBefore(row, actions);
  return {
    update(visible) { row.hidden = !visible; },
  };
}
