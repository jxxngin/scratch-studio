# scratch-studio

## 폴더

| 폴더 | 내용 |
| --- | --- |
| `docs/` | 커리큘럼 구성안(`scratch-curriculum-outline.md`), 기획서(`scratch-studio-spec.md`), 교안 틀(`scratch-lesson-template.md`), 본 사이트 기획서(`spec.md`), 강사용 안내서(`teacher-guides/`) |
| `styles/` | hi-fi 목업 |
| `project/` | 단원 교안. 단원 폴더에는 `unit.json`, `starter.sb3`, `media/`만 둔다 |
| `tools/` | 단원별 교안 생성 스크립트 |
| `app/` | 스크래치 전용 학습 화면 (목업 화면 15) |

## 학습 화면 실행

빌드 과정이 없는 정적 페이지다. 저장소 루트에서 다음을 실행하고 <http://localhost:8000/app/> 을 연다.

```
python app/serve.py
```

| 주소 옵션 | 뜻 | 기본값 |
| --- | --- | --- |
| `unit` | 단원 폴더 경로 | `../project/lv1/04-pirate-cannon` |
| `editor` | 에디터 iframe 주소 | `./editor-stub/index.html` |
| `exit` | "종료"와 "단원 목록으로"가 이동할 주소 | 이전 페이지 |
| `saveFail=1` | 첫 저장을 실패시켜 "저장 실패"와 "다시 시도"를 확인 | 끔 |

다른 단원 폴더를 열 때는 `unit`에 `unit.json`이 들어 있는 폴더를 준다. 진도는 폴더별로 따로 저장된다.

```
http://localhost:8000/app/?unit=../project/lv1/<단원 폴더>
```

## 배포 (Vercel)

교안을 보기 위한 배포다. 실제 수업용이 아니다.

주소: <https://scratch-studio-gray.vercel.app/> (`/app/`으로 연결된다)

- `main`에 푸시하면 Vercel이 자동으로 배포한다. 빌드 과정은 없다.
- `.vercelignore`로 `app/`과 `project/`만 올린다. `docs/`(강사용 안내서, 기획서), `tools/`, `styles/`는 올라가지 않는다.
- `vercel.json`: 첫 주소 `/`를 `/app/`으로 보내고, 모든 응답에 `noindex`를 붙인다.
- 배포 주소는 링크를 아는 누구나 볼 수 있다. 퀴즈 정답과 채점 규칙도 `unit.json`에 들어 있어 브라우저에서 보인다.
- 진도는 보는 사람의 브라우저에 저장된다. 서버가 없으므로 사람마다, 브라우저마다 따로 쌓인다.

**배포 확인 (2026-10-16, 커밋 `8733afb`)**

| 확인한 것 | 결과 |
| --- | --- |
| `/`, `/app` | `/app/`으로 연결됨 |
| 학습 화면, 에디터 자리, 교안(`unit.json`, `starter.sb3`, 이미지, GIF) | 열림 |
| `docs/`, `tools/`, `styles/`, `README.md`, `app/serve.py`, `vercel.json` | 404 (배포되지 않음) |
| `X-Robots-Tag: noindex, nofollow` 헤더 | 모든 응답에 붙음 |
| 버전 1 (32스텝 + 제출) | 처음부터 끝까지 넘김. 블록 그림, 이미지, 퀴즈 정상 |
| 버전 2 (18스텝 + 제출) | 처음부터 끝까지 넘김. 블록 그림, 이미지, GIF, 퀴즈 정상 |

## 해적선 대포 버전 1, 2 보기 (임시)

> 비교가 끝나면 지울 절이다.

같은 단원(Lv.1 4번 해적선 대포)을 두 폴더에 나눠 두었다. 진도는 폴더별로 따로 저장된다.

| 버전 | 폴더 | 주소 |
| --- | --- | --- |
| 1 | `project/lv1/04-pirate-cannon` | <https://scratch-studio-gray.vercel.app/app/> |
| 2 | `project/lv1/04-pirate-cannon-v2` | <https://scratch-studio-gray.vercel.app/app/?unit=../project/lv1/04-pirate-cannon-v2> |

| 항목 | 버전 1 | 버전 2 |
| --- | --- | --- |
| 기준 | 교안 틀 이전에 쓴 교안 | 「스크래치 학생용 교안 틀」(`docs/scratch-lesson-template.md`) |
| 스텝 수 | 32 | 18 (이야기 1, 이야기 퀴즈 1, 오늘 만들 것 1, 만들기 12, 코드 퀴즈 1, 완성 확인 1, 확장 미션 1) |
| 퀴즈 | 퀴즈 스텝 4개, 16문항. 힌트와 해설 있음 | 이야기 퀴즈 2문항, 코드 퀴즈 5문항. 힌트와 해설 없음 |
| 퀴즈 형식 | `"type": "quiz"`, 문항에 `id`, `prompt`, `hint`, `explain` | 기획서 6장의 `"kind": "quiz"`, 문항에 `key`, `question` (코드 퀴즈만 `blocks` 추가) |
| 만들기 스텝 | 스텝마다 구성이 다름 | 제목 → 목표 → 미리보기 GIF → 안내 → 해 보기 |
| 교안 문장 | 표와 `##` 제목 사용. 이야기에 사진과 출처 | 굵게와 목록만. 이야기는 4문장과 그림 1장 |
| 미리보기 | 없음 | 만들기 스텝마다 GIF (`tools/04-pirate-cannon-v2/build_media.py`로 생성) |
| 실험, 포수 시험 | 따로 스텝 | 작품에 남지 않는 활동이라 "해 보기"에 넣음 |
| 소리, 불꽃, 펑, 포탄 수 | 만들기 스텝 | 확장 미션 |
| 채점 | 동적 검사 우선. 정적 검사는 새 블록이 나오는 스텝에만 (s18만 예외) | 동적 검사 우선. 정적 검사는 새 블록이 나오는 스텝에만 (s10만 예외) |
| 시작 프로젝트 | 같음. 과녁 스프라이트 이름은 `과녁`, 포탄은 대포 위 레이어 | 같음 |
| 강사용 안내서 | `docs/teacher-guides/lv1-04-pirate-cannon.md` | 없음 |

## 아직 실제가 아닌 부분

- **에디터**: `app/editor-stub/`은 메시지 규약(기획서 4장)만 흉내 내는 자리다. 채점은 하지 않고 화면에서 고른 결과(통과, 실패, 오류, 응답 없음)를 돌려준다. 실제 에디터가 준비되면 `editor` 주소만 바꾼다.
- **서버**: `app/store.js`가 본 사이트의 API(기획서 8장)를 대신해 진도와 제출을 브라우저에 저장한다. 채점 규칙(`checks`)도 브라우저로 내려오므로 실제 사이트에서는 이 파일을 서버 호출로 바꿔야 한다.
- **미니퀴즈**: `unit.json`의 퀴즈 스텝을 그린다. 기획서 형식(`"kind": "quiz"`)과 이전 형식(`"type": "quiz"`)을 모두 읽는다. 모든 문항이 정답이어야 통과이고 다시 풀 수 있다. 정답이 브라우저로 내려오므로 실제 사이트에서는 서버가 판정해야 한다.
- **프로젝트 제출**: 사이트가 배치하는 기능이라 단원 끝에 제출 스텝을 붙인다.
