# scratch-studio

## 폴더

| 폴더 | 내용 |
| --- | --- |
| `docs/` | 커리큘럼 구성안(`scratch-curriculum-outline.md`), 기획서(`scratch-studio-spec.md`), 강사용 안내서(`teacher-guides/`) |
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
http://localhost:8000/app/?unit=../project/lv1/04-pirate-cannon_1
```

## 아직 실제가 아닌 부분

- **에디터**: `app/editor-stub/`은 메시지 규약(기획서 4장)만 흉내 내는 자리다. 채점은 하지 않고 화면에서 고른 결과(통과, 실패, 오류, 응답 없음)를 돌려준다. 실제 에디터가 준비되면 `editor` 주소만 바꾼다.
- **서버**: `app/store.js`가 본 사이트의 API(기획서 8장)를 대신해 진도와 제출을 브라우저에 저장한다. 채점 규칙(`checks`)도 브라우저로 내려오므로 실제 사이트에서는 이 파일을 서버 호출로 바꿔야 한다.
- **미니퀴즈**: `unit.json`의 `"type": "quiz"` 스텝을 그린다. 모든 문항이 정답이어야 통과이고 다시 풀 수 있다. 정답이 브라우저로 내려오므로 실제 사이트에서는 서버가 판정해야 한다.
- **프로젝트 제출**: 사이트가 배치하는 기능이라 단원 끝에 제출 스텝을 붙인다.
