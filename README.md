# scratch-studio

## 폴더

| 폴더 | 내용 |
| --- | --- |
| `docs/` | 커리큘럼 구성안(`scratch-curriculum-outline.md`), 기획서(`scratch-studio-spec.md`), 교안 틀(`scratch-lesson-template.md`), 본 사이트 기획서(`spec.md`), 강사용 안내서(`teacher-guides/`) |
| `styles/` | hi-fi 목업 |
| `project/` | 단원 교안. 단원 폴더에는 `unit.json`, `starter.sb3`, `media/`만 둔다 |
| `tools/` | 단원별 미리보기 GIF 생성 스크립트 (보물 지도 탐험은 시작 프로젝트와 그림도 함께 만들고, `verify/`에 엔진 검증 도구가 있다) |
| `app/` | 스크래치 전용 학습 화면 (목업 화면 15) |

## 문서 내려받기

본 사이트(`dlab-coding-track`)에 옮겨 쓸 문서다. 링크를 열고 GitHub 파일 화면 오른쪽 위의 다운로드 버튼(Download raw file)을 누르면 받을 수 있다. 저장소가 공개라 로그인 없이 열린다.

| 문서 | 내려받기 | 최종 수정 | 이번에 바뀐 것 |
| --- | --- | --- | --- |
| 스크래치 학생용 교안 틀 | [scratch-lesson-template.md](docs/scratch-lesson-template.md) | 2026-10-16 | 단원 흐름(이야기 1~3스텝, 개념 묶음마다 확인 퀴즈, 탐색·꾸미기 스텝, 심화 도전, 목차), 퀴즈 동작(힌트와 해설), 탐색 스텝과 입력 표, 꾸미기 스텝, 소제목, 블록 이름 코드 표기, 마크다운 범위, 채점 규칙 쓰는 법, 예시, 체크리스트 |
| 스크래치 스튜디오 기획서 | [scratch-studio-spec.md](docs/scratch-studio-spec.md) | 2026-10-16 | 5장: 미니퀴즈 동작, 소제목 표시, 목차, 입력 표, 작품 제목 예시(단원 이름). 6장: 퀴즈 문항 필드(`hint`, `explain`, `blocks`, `title`), `record` 블록과 검사, `chapters`, 마크다운 범위. 8장: 입력 표 API |
| 본 사이트 기획서 | [spec.md](docs/spec.md) | 2026-10-16 | §3.3.1: 미니퀴즈 동작, 입력 표, 목차. §5: `UNIT.chapters`, `STEP_RECORD`, `QUIZ_QUESTION.content`. §8: 학생 상세의 입력 표 열람 |
| 커리큘럼 구성안 | [scratch-curriculum-outline.md](docs/scratch-curriculum-outline.md) | 2026-10-16 | Lv.1 표 아래: 보물 지도 탐험의 정해진 블록(`탐험가에 닿았는가? 까지 기다리기`)과 타이머 메모 |
| 강사용 안내서 (보물 지도 탐험) | [lv1-01-treasure-map.md](docs/teacher-guides/lv1-01-treasure-map.md) | 2026-10-16 | 새로 만듦. 단계 구성과 120분 배분, 정답 코드, 채점 경로, 퀴즈 정답·힌트·해설, 엔진 검증 기록(7장), 실제 그림 출처(8장) |
| 강사용 안내서 (해적선 대포) | [lv1-04-pirate-cannon.md](docs/teacher-guides/lv1-04-pirate-cannon.md) | 2026-10-16 | 단계 구성, 퀴즈 정답·힌트·해설 |
| 보물 지도 탐험 교안 | [unit.json](project/lv1/01-treasure-map/unit.json) · [starter.sb3](project/lv1/01-treasure-map/starter.sb3) · [media/](project/lv1/01-treasure-map/media) | 2026-10-16 | 새로 만듦. Lv.1 첫 단원, 26스텝(2시간 기준). 실제 그림 3장(퍼블릭 도메인), 채점 규칙은 엔진에서 검증 |
| 해적선 대포 교안 | [unit.json](project/lv1/04-pirate-cannon/unit.json) · [starter.sb3](project/lv1/04-pirate-cannon/starter.sb3) · [media/](project/lv1/04-pirate-cannon/media) | 2026-10-16 | 교안 틀 개정의 기준이 된 교안 |

### 교안 틀 변경 (2026-10-16 반영)

해적선 대포 교안(Lv.1-4)을 기준으로 교안 틀을 아래처럼 고쳤다. 기획서 5장·6장·8장과 `spec.md` §3.3.1·§5도 함께 고쳤다(위 표 참고).

| 규칙 | 이전 교안 틀 | 바뀐 교안 틀 |
| --- | --- | --- |
| 이야기 | 1스텝, 4문장, 그림 1장 | 1~3스텝. 실제 사진은 스텝 끝에 출처 한 줄 |
| 퀴즈 개수 | 이야기 퀴즈 1개, 코드 퀴즈 1개 | 개념 묶음이 끝날 때마다 확인 퀴즈 + 마무리 퀴즈 (스텝마다 2~3문항) |
| 퀴즈 동작 | 틀려도 해설이나 틀린 문항을 보여 주지 않음 | **틀린 문항 아래에 힌트**(틀린 문항을 따로 표시하지는 않음), **통과하면 해설** |
| 스텝 종류 | 이야기, 만들기, 퀴즈 등 9종 | "탐색"(입력 표가 있으면 해 보니 칸 채점), "꾸미기"(채점), "심화 도전" 추가. 탐색·꾸미기는 `kind: lesson`이고 제목 앞의 "탐색:", "꾸미기:"로 구분 |
| 채점 규칙 | 정적, 동적, `anyOf` | 입력 표 채점 `{ "type": "record" }` 추가. 사이트가 채점한다(에디터 아님) |
| 확장 미션 | 미션마다 이름과 할 일만 | 블록 그림 단서 허용, 뒤에 심화 도전 1스텝 허용 |
| 마크다운 | 굵게와 목록만 | 표 허용, `##` 제목은 이야기와 확장 미션에만 |
| 콘텐츠 블록 | `text`, `image`, `video`, `blocks` | 입력 표 `record` 추가 (열마다 고정 글자 또는 입력 칸: 보기, 숫자, 글, 해 보니) |
| 퀴즈 문항 필드 | `key`, `question`, `options`, `answer` | `hint`, `explain` 추가. 코드 문항은 `blocks`, 그림 문항은 `image`. 퀴즈 스텝에 선택 필드 `title` |
| 스프라이트 지정 | `@first`, `@any` | 여러 스프라이트를 구분해야 하면 시작 프로젝트의 이름 |
| 정적 검사 | 블록을 꼭 써야 하는 스텝에만 | 새 블록이 나오는 스텝에만. 동적 검사로 구분되지 않을 때(시작 상태가 이미 목표와 같음, 소리처럼 동작으로 볼 수 없음)만 예외 |
| 블록 이름 | [대괄호] | 코드 표기 |
| 문장 수 | `text` 하나에 3문장 이내 | `text` 하나에 한 가지 일 |
| 소제목 | 정해진 형식 없음 | 문단 맨 앞에 `**확인**: …`처럼 "굵은 소제목 + 쌍점". 목표는 `**목표**` 다음 줄에 목록. 화면이 칩과 색 상자로 그린다 |
| 단원 목차 | 없음 | `unit.json`에 `chapters`(목차 이름과 스텝 키 목록) 추가. 화면은 목차가 있으면 목차 방식으로, 없으면 전체 점으로 보여 준다 |
| 블록 그림 | 8개 이내 | Lv.1은 전체 스크립트 그림 예외 |
| 시간 | 만들기 합계 약 75분 | 개념 묶음 전체 75분 안팎. 넘치면 탐색과 꾸미기부터 줄임 |

**탐색 스텝**: 작품에 남길 것을 만들지 않고, 블록을 눌러 보거나 숫자를 바꿔 보며 결과를 관찰하는 스텝이다. 예상하고 → 해 보고 → 결과를 비교하는 활동이 중심이고, 끝나면 꺼낸 블록을 지우거나 숫자를 원래대로 돌린다. 이전 교안 틀은 이런 활동을 만들기 스텝 안의 "해 보기" 칸에 넣게 했는데, 바뀐 교안 틀은 따로 스텝으로 세운다.

**입력 표(`record`)**: 이 저장소의 학습 화면은 학생이 적은 값을 브라우저에 저장한다. 실제 사이트에서는 학생 × 스텝마다 `STEP_RECORD`에 저장하고(`spec.md` §5), 교사가 학생 상세 화면에서 읽는다(기획서 8장).

## 학습 화면 실행

빌드 과정이 없는 정적 페이지다. 저장소 루트에서 다음을 실행하고 <http://localhost:8000/app/home/> (레벨 고르기 화면) 또는 <http://localhost:8000/app/> 을 연다.

```
python app/serve.py
```

| 주소 옵션 | 뜻 | 기본값 |
| --- | --- | --- |
| `unit` | 단원 폴더 경로 | `../project/lv1/04-pirate-cannon` |
| `editor` | 에디터 iframe 주소 | `./editor-stub/index.html` |
| `exit` | "종료"와 "단원 목록으로"가 이동할 주소 | 레벨 고르기 화면의 그 레벨 목록 (`./home/#lv1` 등, 임시) |
| `saveFail=1` | 첫 저장을 실패시켜 "저장 실패"와 "다시 시도"를 확인 | 끔 |

다른 단원 폴더를 열 때는 `unit`에 `unit.json`이 들어 있는 폴더를 준다. 진도는 폴더별로 따로 저장된다.

```
http://localhost:8000/app/?unit=../project/lv1/<단원 폴더>
```

보물 지도 탐험: <http://localhost:8000/app/?unit=../project/lv1/01-treasure-map> (배포 주소에서는 `/app/?unit=../project/lv1/01-treasure-map`)

## 배포 (Vercel)

교안을 보기 위한 배포다. 실제 수업용이 아니다.

주소: <https://scratch-studio-gray.vercel.app/> (레벨 고르기 화면 `/app/home/`으로 연결된다)

- `main`에 푸시하면 Vercel이 자동으로 배포한다. 빌드 과정은 없다.
- `.vercelignore`로 `app/`과 `project/`만 올린다. `docs/`(강사용 안내서, 기획서), `tools/`, `styles/`는 올라가지 않는다.
- `vercel.json`: 첫 주소 `/`를 `/app/home/`으로 보내고, 모든 응답에 `noindex`를 붙인다.
- 배포 주소는 링크를 아는 누구나 볼 수 있다. 퀴즈 정답과 채점 규칙도 `unit.json`에 들어 있어 브라우저에서 보인다.
- 진도는 보는 사람의 브라우저에 저장된다. 서버가 없으므로 사람마다, 브라우저마다 따로 쌓인다.

**배포 확인 (2026-10-16, 커밋 `8733afb`)**

| 확인한 것 | 결과 |
| --- | --- |
| `/`, `/app` | `/app/`으로 연결됨 |
| 학습 화면, 에디터 자리, 교안(`unit.json`, `starter.sb3`, 이미지, GIF) | 열림 |
| `docs/`, `tools/`, `styles/`, `README.md`, `app/serve.py`, `vercel.json` | 404 (배포되지 않음) |
| `X-Robots-Tag: noindex, nofollow` 헤더 | 모든 응답에 붙음 |

## 아직 실제가 아닌 부분

- **에디터**: `app/editor-stub/`은 메시지 규약(기획서 4장)만 흉내 내는 자리다. 채점은 하지 않고 화면에서 고른 결과(통과, 실패, 오류, 응답 없음)를 돌려준다. 실제 에디터가 준비되면 `editor` 주소만 바꾼다.
- **서버**: `app/store.js`가 본 사이트의 API(기획서 8장)를 대신해 진도와 제출을 브라우저에 저장한다. 채점 규칙(`checks`)도 브라우저로 내려오므로 실제 사이트에서는 이 파일을 서버 호출로 바꿔야 한다.
- **미니퀴즈**: `unit.json`의 퀴즈 스텝을 그린다. 기획서 형식(`"kind": "quiz"`)과 이전 형식(`"type": "quiz"`)을 모두 읽는다. 모든 문항이 정답이어야 통과이고 다시 풀 수 있다. 정답이 브라우저로 내려오므로 실제 사이트에서는 서버가 판정해야 한다.
- **건너뛰기 (교안 확인용, 임시)**: 채점이 있는 스텝 아래에 "건너뛰기 (교안 확인용)"이 있다. 누르면 채점 없이 통과 처리하고 다음 스텝으로 간다. 실제 수업용으로 쓸 때는 `app/dev-skip.js`, `app/main.js`에서 `dev-skip`으로 검색되는 줄, `app/store.js`의 `devPass`, `app/styles.css`의 `.ss-dev-skip` 스타일을 지운다.
- **레벨 고르기 화면 (교안 확인용, 임시)**: `app/home/`이 Lv.1~3과 단원 목록을 보여 준다. 교안이 있는 단원만 열리고 나머지는 "준비 중"으로 막혀 있다. 교안을 새로 만들면 `app/home/index.html`의 `LEVELS`에서 그 단원 줄에 `unit`(폴더 이름)을 적는다. 학습 화면의 "종료"는 이 화면의 그 레벨 목록으로 돌아온다. 실제 수업용으로 쓸 때는 `app/home/`을 지우고, `vercel.json`의 `/` 이동 주소를 `/app/`으로 되돌리고, `app/main.js`에서 `[임시] home`으로 검색되는 줄의 종료 기본 주소를 `''`로 되돌린다(실제 사이트에서는 본 사이트의 단원 목록이 이 역할을 한다).
- **프로젝트 제출**: 사이트가 배치하는 기능이라 단원 끝에 제출 스텝을 붙인다.
- **채점 규칙**: 채점 엔진이 아직 없다. 보물 지도 탐험은 `tools/01-treasure-map/verify/`의 도구로 정답·오답 sb3(`tests/`)를 만들어 TurboWarp 실행기에서 `checks`를 돌려 확인했다(정답은 모두 통과, 오개념 작품을 포함한 틀린 작품 12개는 실수하는 스텝에서 떨어짐, 결과는 `report.txt`·`scenarios.txt`와 강사용 안내서 7장). 실행: `python tools/01-treasure-map/verify/build_tests.py` → `run_checks.py` → `scenarios.py` (Playwright와 Chromium 필요). 해적선 대포는 규칙을 좌표와 시간으로 계산해 맞췄을 뿐 채점기처럼 돌려 보지 않았다.
- **교안 위치**: 기획서는 `scratch-content/scratch-lv1/<단원>/`과 `tests/`, 이 저장소는 `project/lv1/<단원>/`. 어느 쪽으로 맞출지 아직 정하지 않았다.
