# 디랩 코딩 트랙 — 학원 운영 웹사이트 MVP 기획 문서

작성일: 2026-07-17
최종 수정: 2026-10-15 — 스크래치 학생용 교안 틀에 맞춰 과목명(스크래치 Lv.1~3), 스크래치 미니퀴즈 예외(§3.3.1), Lv.3 설계하기(§3.3.1, §5 `DESIGN_NOTE`), 퀴즈 가져오기 키(§5 `QUIZ_QUESTION`)를 반영
개발 폴더명: `dlab-coding-track`

이 문서는 대화를 통해 도출된 요구사항, 역할별 권한, 데이터 모델(ERD)을 정리한 것입니다.
Claude Code에 이 문서를 전달하여 프로젝트 구조 및 DB 스키마 생성을 요청할 수 있습니다.

---

## 1. 프로젝트 개요

코딩 학원 운영을 위한 웹 플랫폼. 학생은 타자연습, 블록코딩(스크래치/엔트리 등), 파이썬 문제풀이를
수행하고, 관리자·교사는 콘텐츠와 학생을 관리하며, 학부모는 로그인 없이 월간 리포트를 확인한다.

## 2. 계정 구조

| 역할 | 설명 | 계정 생성 방식 |
|---|---|---|
| `admin` | 학원 운영자(원장). 계정/권한/운영 관리 | 최초 시스템 관리자 |
| `teacher` | 수업 담당 교사 | admin이 생성 |
| `student` | 학생 | admin 또는 teacher가 생성 (자가 가입 없음) |
| 학부모 | 별도 계정 없음 | `REPORT`의 공유 링크(`share_token`)로 로그인 없이 열람 |

- 교사-학생 관계는 **반(`CLASS`) 기반으로 자동 도출**된다 (직접 배정 아님):
  - `CLASS`는 시간표 단위의 반이며, 학생별 실제 수강 과목/단원 진행과는 무관하다(각자 다른 과목/단원을 진행 가능). 다만 반 상세 화면에 참고용으로 표시하기 위해 **대표 과목**을 선택적으로 지정할 수 있다 (`CLASS.subject_id`, nullable, 단일 값 — 필수 아님).
  - 반의 요일·시간은 `CLASS_SCHEDULE`로 구조화 관리 (반복 요일마다 별도 행, 예: 화목반은 2행). 관리자가 시간대별 전체 스케줄을 그리드로 조회.
  - 반마다 **담당 교사 1명**이 배정된다 (`CLASS.teacher_id`). 한 교사가 여러 반을 담당하는 것은 가능 (단, 계정/권한 관리 화면에선 우선 단일 반만 노출하는 것으로 확정 — 추후 다건 노출은 별도 검토).
  - 반의 담당교사·시간 등 핵심 필드가 변경되면 `CLASS_CHANGE_LOG`에 변경 이력을 남긴다 (필드명, 이전 값, 새 값, 변경 시각/변경자). 과거 출석/개입 기록을 조회할 때 그 시점 기준 담당교사가 누구였는지는 이 로그로 역추적한다.
  - 반이 완전히 폐강되는 경우 `CLASS.status`(`active` | `closed`)로 표시한다. 삭제하지 않으며, 소속 학생 이력(`CLASS_STUDENT`)은 그대로 보존한다 (재적/퇴원 처리와 동일한 원칙, 4.1절 참고).
  - 학생은 `CLASS_STUDENT`로 반에 소속된다.
  - "교사의 담당 학생" = 그 교사가 담당하는 반(`CLASS`)에 소속된 학생(`CLASS_STUDENT`)들, 조인으로 자동 계산.
- 학생의 수강 과목은 `ENROLLMENT`로 관리되며, admin/teacher가 언제든 추가·해제 가능.
- 타자연습은 `ENROLLMENT`와 무관하게 전 학생 공통 이용 기능.

## 3. 기능별 요구사항 요약

### 3.1 타자연습
- 전 학생 공통 기능 (수강 여부와 무관).
- 랭킹은 **전체 학원 통합**으로 집계하며, 세 가지 랭킹을 함께 제공한다:
  - **종합 랭킹 (공식/시상 기준)**: 매 판 `점수 = WPM × 정확도`로 계산해 누적한 포인트 기준. 시상 등 공식 순위 결정에 사용.
  - **실력 랭킹 (보조, 동기부여용)**: 개인 역대 최고 기록(WPM) 기준.
  - **노력 랭킹 (보조, 동기부여용)**: 누적 연습 횟수 기준.
  - 실력/노력 랭킹을 별도로 계속 보여주는 이유: 종합 랭킹만 노출하면 상위권 외 학생들이 동기를 잃기 쉬워, "나는 실력 랭킹에서 올랐다" 같은 다른 성취 경로를 열어두기 위함.
- 리포트에는 최근 추이를 그래프(시간순)로 보여준다.
- 종합/실력/노력 랭킹은 `TYPING_RECORD(wpm, accuracy)`만으로 쿼리 계산 가능
  (`SUM(wpm × accuracy)`, `MAX(wpm)`, `COUNT(*)`).
- 연습 유형(자리연습/낱말연습/단문연습/장문연습)과 판별 소요시간은 UI(와이어프레임 화면 2~4)에 노출되므로
  `TYPING_RECORD`에 `practice_type`, `duration` 필드를 추가한다. 단, 랭킹 집계는 유형과 무관하게 통합 계산한다.

### 3.2 트랙 & 과목 카탈로그 & 단원
- 트랙(`TRACK`)은 연령대/난이도 단계별 과목 묶음이다 (예: Rookies · Starter · Creator · Master).
  각 과목(`SUBJECT`)은 하나의 트랙에 속한다 (`SUBJECT.track_id`).
- 과목(`SUBJECT`)은 admin/teacher가 자유롭게 생성·수정하는 카탈로그.
  - 예: 레고코딩 Lv1~5, 스크래치 Lv.1~3, 엔트리 AI 기초/심화, 마이크로비트 기본/심화,
    마이크로비트 아케이드, 앱인벤터, 순서도로 배우는 파이썬, 파이썬 문제풀이 100, 알고리즘 Lv1
- 각 과목은 `category`로 콘텐츠 형태가 고정된다:
  - **튜토리얼형**: 단계별(step) 교안을 따라 진행 → `LESSON_STEP`
  - **문제풀이형**: 코드 작성 후 실행/자동채점 → `PROBLEM` + `TEST_CASE`
- 튜토리얼형 과목은 `editor_type`으로 실습 방식을 구분한다 (`SUBJECT.editor_type`, 기본값 `none`):
  - `scratch`: 사이트 안에 임베드한 스크래치 에디터에서 만들고 스텝마다 자동 채점 (§3.3.1). 스크래치 Lv.1~3이 해당.
  - `none`: 외부 사이트에서 만들고 공유 링크 제출 (§3.3.2). 엔트리, 레고코딩, 마이크로비트, 앱인벤터 등.
  - 튜토리얼형과 문제풀이형의 구분 기준은 채점 유무가 아니다. 튜토리얼형은 스텝이 이어지며 하나의 작품이 쌓이고, 문제풀이형은 문제마다 독립적으로 풀어 정답을 맞힌다.
- 단원(`UNIT`)은 과목에 속하며, 단원 내 콘텐츠는 `LESSON_STEP`(교안 스텝)과 `QUIZ`(퀴즈 블록)로 구성되고
  둘 다 `order_no` 순서를 가져 자유롭게 섞어 배치할 수 있다 (퀴즈가 꼭 마지막에 올 필요 없음).
  실습 결과물 제출이 필요한 단원은 `PROJECT` 제출도 콘텐츠 중 하나로 포함된다.
- 튜토리얼형 단원은 위 단원 콘텐츠 흐름 안에 **스텝(`LESSON_STEP`) 중간 미니 퀴즈**를 배치할 수 있다
  (`QUIZ_QUESTION.step_id`). 오답 시 즉시 해설을 보여주고, 단원 완료 여부와는 무관하다(형성평가 목적).
  스크래치 과목의 미니퀴즈는 동작이 다르다 (§3.3.1).
- **단원 완료 판정**: 그 단원의 모든 필수 콘텐츠(스텝, 미니퀴즈, 퀴즈, 프로젝트 제출 등)를 다 마치면
  시스템이 자동으로 완료 처리한다 (`UNIT_PROGRESS`). 어떤 콘텐츠로 "끝나는지" 구분하는 별도 필드는 두지 않는다.
  교사 수동 완료 처리도 가능하다 (`UNIT_PROGRESS.completed_by`).
  단, 스크래치 과목의 스텝 단위 수동 통과는 없다 (§3.3.1).
- **이어서 하기**: 문제풀이형은 `SUBMISSION` 이력에서 아직 정답 처리 안 된 첫 문제로 자동 이동한다 (별도 필드 불필요).
  튜토리얼형은 `STEP_PROGRESS`로 스텝별 완료 여부를 기록하며, 완료되지 않은 첫 스텝으로 이동한다.

### 3.3 블록코딩 (튜토리얼형 과목)

블록코딩 과목은 `SUBJECT.editor_type`에 따라 두 방식으로 나뉜다.

#### 3.3.1 스크래치 과목 — 스크래치 스튜디오 (`editor_type = scratch`)

스크래치 과목은 기존 튜토리얼 진행 화면을 쓰지 않고, 스텝 교안과 임베드한 스크래치 에디터를 함께 보여주며 스텝마다 학생의 작품을 자동 채점하는 **스크래치 전용 학습 화면**을 쓴다. 이 기능의 이름은 **스크래치 스튜디오**다.

학습 화면, 채점, 작품 저장과 제출 버전, 작품 페이지, 교안 작성과 가져오기, 에디터와의 통신, 다국어의 동작은 「스크래치 스튜디오 기획서」([scratch-studio/scratch-studio-spec.md](scratch-studio/scratch-studio-spec.md))가 기준이며, 이 문서에는 다시 적지 않는다. 여기에는 사이트의 다른 부분과 맞물리는 점만 둔다.

- **진입**: 단원 목록에서 `editor_type = scratch`인 과목의 단원을 열면 전용 화면으로, 그 외 튜토리얼형 과목은 기존 튜토리얼 진행 화면으로 들어간다. 기존 화면은 고치지 않는다.
- **데이터**: 진도·퀴즈·제출은 기존 테이블(`STEP_PROGRESS`, `UNIT_PROGRESS`, `QUIZ`, `PROJECT`)을 그대로 쓰고, 작품 파일과 제출 버전을 위한 테이블과 컬럼을 추가한다 (§5).
- **다른 튜토리얼형 과목과 다른 점**: 스텝 단위의 교사 수동 통과가 없다. 실시간 관찰·제어권 교환(§3.4)을 적용하지 않고, 대신 교사와 관리자가 저장된 작품을 열어볼 수 있다 (§4). PC와 크롬북만 지원한다.
- **미니퀴즈**: 한 퀴즈 스텝의 문항을 모두 맞혀야 통과하고, 통과해야 다음 스텝으로 넘어간다. 따라서 단원 완료 조건에 들어간다. 틀려도 해설이나 어느 문항이 틀렸는지는 보여주지 않는다. 문항은 교안과 함께 가져오기 스크립트로 등록하고, 화면에서는 고치지 않는다.
- **설계하기 (Lv.3)**: 만들기 전에 작품을 구상하는 글쓰기 스텝이다. 학생의 답은 `DESIGN_NOTE`에 저장한다 (§5).
- **교안 틀**: 단원의 스텝 종류와 순서, 스텝 안의 칸 구성은 「스크래치 학생용 교안 틀」([scratch-studio/scratch-lesson-template.md](scratch-studio/scratch-lesson-template.md))이 기준이다.
- **다른 기능과의 연결**: 제출한 작품은 포트폴리오(§3.5)와 학부모 리포트(§3.6)에서 작품 실행으로 보여주고, 교사 승인을 거쳐 커뮤니티에 공유할 수 있다 (§3.7).

#### 3.3.2 그 외 블록코딩 과목 (`editor_type = none`)

- 엔트리, 레고코딩, 마이크로비트, 앱인벤터 등은 기존 방식을 유지한다. 학생은 외부 사이트에서 직접 제작 후 **공유 링크를 제출**한다 (`PROJECT.project_link`).
- 완성 결과물은 영상/이미지(`media_url`)도 함께 첨부 가능 → 포트폴리오로 활용.

### 3.4 파이썬 문제풀이 (문제풀이형 과목)
- 화면 구조: 좌측 문제 설명, 우측 코드 에디터, 실행/제출 버튼 (기존 사용 교재와 동일한 UX).
- 채점: **여러 테스트 케이스(입력→출력 쌍)를 모두 통과해야 정답**.
- 재시도 횟수(`attempt_count`)를 기록하여 성취도 분석에 활용.
- 문제에는 개념 태그(`concept_tags`, 예: if문/반복문/리스트)를 붙여 약점 분석에 활용.
- **실시간 교사 개입 기능 포함 (MVP 범위)**:
  - 교사가 여러 학생의 코드 작성 화면을 실시간으로 확인
  - 페어프로그래밍: **제어권 넘기기 방식** (한 번에 한 사람만 타이핑, 버튼으로 제어권 교환)
    - 교사 → 학생: 교사가 언제든 자유롭게 즉시 넘길 수 있음
    - 학생 → 교사: 학생이 버튼으로 "제어권 요청"을 보내면, 교사가 **수락 또는 거절**할 수 있음 (즉시 뺏기 방지, 수업 흐름 보호). 거절은 DB에 기록되지 않는 순간적 상태로, 통신 계층에서만 처리
  - ⚠️ 실시간 통신 자체(화면 동기화, 제어권 상태)는 웹소켓 기반이며 **DB 스키마 밖의 별도 기술 스펙**으로 설계해야 함
  - **개입 이력은 `HELP_SESSION`에 기록**하며, 관련 문제의 `concept_tags`를 통해 "어떤 개념에서 도움을 받았는지"를 리포트의 보완할 점 분석에 반영
  - 담당 교사 여부와 무관하게 **모든 교사와 관리자가 개입 가능** (반 배정과 별개)
  - **화면 UI 구성** (hi-fi label 11 "교사 — 실시간 개입 화면" 기준, 2026-08-16 확정 — 아래는 UI 요소 확정이며, 실시간 통신 구현 자체는 여전히 미착수, §7 참고):
    - 좌측 학생 로스터: 개입 가능한 여러 학생을 아바타 목록으로 동시 표시. 아바타 테두리/배지 색상으로 학생별 상태(활동중/도움 요청 등)를 구분하고, 클릭으로 관찰 대상 학생을 전환
    - 상단 바: 현재 보고 있는 학생 이름 + 상태 배지, 문제 위치 브레드크럼(과목 › 단원 › 문제), "💡 해설 보기"(기존 교사 전용 `Problem.explanation` 노출), "📝 수업 자료 수정"(교안 관리 화면으로 이동), "학습 종료" 버튼
    - 제어권 요청 배너: 학생이 요청을 보내면 상단에 배너로 표시되고 수락/거절 버튼 제공
    - 학생 화면 미러링: 문제 설명(좌측, 폭 조절 가능) + 코드 에디터 + 콘솔(입력 대기/실행 결과/테스트 결과 상태 포함)이 학생이 보는 화면과 동일하게 실시간 반영되고, 제어권을 가진 쪽만 실행/제출을 조작
    - 제어권 토글: 현재 제어권 소유자 라벨 + 토글 스위치로 "교사 → 학생 즉시 전환"을 구현하는 실제 UI 형태
    - 문제 목록 드로어(사이드 패널): 햄버거 버튼으로 열리며 과목 전체 진행률 + 단원별 문제 목록을 보여주고, 클릭 시 개입 중인 화면에서 바로 다른 문제로 전환 가능

### 3.5 포트폴리오
- 튜토리얼형 단원의 `project` 완료 결과물(`PROJECT`)을 모아 갤러리 형태로 제공.
- 파이썬/블록코딩 모두 포함.
- 스크래치 과목의 결과물은 썸네일로 표시하고, 누르면 작품 페이지에서 직접 실행한다 (§3.7). 영상(`media_url`)이 있으면 함께 보여준다.

### 3.6 리포트 — 두 종류로 분리
| 구분 | 대상 | 성격 | 내용 |
|---|---|---|---|
| 학생 대시보드 | 학생 본인 | **실시간 누적 집계** (스냅샷 아님, 항상 최신) | 과목별 진행률, 포트폴리오, 학습 활동 히트맵, 타자연습 그래프. **교사 코멘트는 학생에게 노출하지 않음** |
| 학부모 리포트 (`REPORT`) | 학부모(공유 링크) | **매월 1일 자동 생성되는 스냅샷** (그 시점 상태로 고정) | 출석/참여도, 교사 총평 및 자동 생성된 잘한 점/보완할 점, 완성 프로젝트 예시(영상/이미지, 스크래치는 작품 실행 링크), 타자연습 추이 그래프 |

- 학생 대시보드의 **학습 활동 히트맵**은 최근 52주를 일요일 시작 주 단위로 표시하며, 각 날짜의 강도는 그날의 학습 활동 건수(`SUBMISSION` + `TYPING_RECORD` + `PROJECT` + `UNIT_PROGRESS`(완료) + `STEP_PROGRESS`(완료) + `QUIZ_SUBMISSION` + `HELP_SESSION`을 합산한 건수, 설계하기 답(`DESIGN_NOTE`)은 넣지 않음)를 0 / 1 / 2 / 3 / 4건 이상의 5단계로 그대로 매핑해 계산한다. `ATTENDANCE`(등원/하원 체크)와는 별개 지표이며, 등원 여부가 아니라 실제 학습 활동량을 보여준다.
- 잘한 점/보완할 점은 정답률·소요시간·재시도 횟수·개념 태그·**교사 개입 이력(`HELP_SESSION`)** 데이터를 기반으로 **자동 생성**.
  개입이 잦았던 개념 태그는 "보완할 점"에 우선 반영.
  스크래치 과목은 개념 태그가 없으므로 잘한 점/보완할 점 자동 분석에서 제외하고, 진도·학습시간·히트맵에만 반영한다.
- "총 학습시간"은 `SUBMISSION.time_spent` + `TYPING_RECORD.duration` + `UNIT_PROGRESS.time_spent`(튜토리얼)를 모두 합산한다.
- 교사는 언제든 자유롭게 코멘트(`TEACHER_COMMENT`)를 남길 수 있고, 리포트에 타임라인으로 반영됨. 학생에게는 비공개.
- 학부모 리포트의 스크래치 작품은 **리포트 생성 시점(`REPORT.generated_at`)까지 제출된 버전 중 가장 최신 버전**으로 고정한다. 이후에 학생이 새 버전을 제출해도 그 리포트에서 열리는 버전은 바뀌지 않는다 (별도 필드 없이 `PROJECT_VERSION.submitted_at`으로 판별).
- 공유 링크(`share_token`)는 **만료 기한(`expires_at`)**을 두어 무기한 유출 위험을 방지.

### 3.7 작품 공유와 커뮤니티 페이지

학생이 제출한 스크래치 작품의 공유를 신청하고 교사가 승인하면 커뮤니티 페이지에 올라간다. 첫 버전은 스크래치 작품만 대상이며, 다른 과목은 추후 확장한다.

- **보호자 동의**: 작품 공개에 대한 보호자 동의는 학원 등록 때 서면으로 받고, 교사 또는 관리자가 학생 상세 화면에서 그 학생에게 동의 여부를 표시한다 (`USER.share_consent`). **동의가 표시된 학생만 공유 신청을 할 수 있다.** 동의 표시를 해제하면 그 학생의 공개 작품을 모두 내리고 신청 중인 건을 취소한다.
- **공유 절차 (교사 승인 후 공개)**:
  - 공유 상태는 제출 버전마다 기록한다 (`PROJECT_VERSION.share_status`: `none` | `pending` | `approved` | `rejected` | `taken_down`).
  - 학생이 제출한 버전을 골라 "공유 신청"을 한다 (`pending`). 학생용 확인 창은 두지 않는다. 한 작품에서 신청 중인 버전은 하나뿐이며, 다른 버전을 신청하면 앞선 신청은 취소된다.
  - 교사 또는 관리자가 작품을 열어 확인한 뒤 승인하거나 거절한다 (`approved` / `rejected`). 담당 여부와 무관하게 모든 교사와 관리자가 처리할 수 있고, 처리한 사람과 시각을 그 버전에 남긴다.
  - 승인하면 그 버전이 공개되고(`PROJECT.shared_version_id`), 작품 링크용 토큰(`PROJECT.share_token`)이 만들어진다.
  - 공개 중에 학생이 새 버전을 제출해도 공개되는 것은 승인받은 버전 그대로다. 새 버전을 공개하려면 다시 신청해 승인받는다. 그동안 이전 버전은 계속 공개된다. 새 버전이 승인되어 공개 버전이 바뀌어도 **작품 링크는 그대로 유지**하고, 이전 버전의 상태는 `none`으로 돌아간다.
  - 학생은 언제든 신청을 취소하거나 공유를 내릴 수 있다 (그 버전의 상태는 `none`). **학생이 스스로 내린 버전은 같은 버전으로 다시 신청할 수 있고**, 교사 승인을 다시 거친다.
- **교사의 내리기와 재신청**: 교사와 관리자는 공개된 작품을 내릴 수 있다 (`taken_down`). 거절되었거나 교사가 내린 버전은 다시 신청할 수 없고, 학생이 **고쳐서 새 버전을 제출하면 다시 신청**할 수 있다 (다시 교사 승인).
- **내린 뒤**: 작품을 내리면(학생·교사 모두) 작품 링크 토큰을 폐기하고, 다시 공개되면 새 토큰을 만든다. **좋아요와 댓글은 지우지 않으며**, 다시 공개되면 그대로 보인다.
- **볼 수 있는 사람**:
  - **커뮤니티 페이지(목록)**: 로그인한 학원 구성원(학생·교사·관리자)만 볼 수 있다. 공개된 작품의 썸네일, 제목, 만든 사람, 좋아요 수를 보여주고 최신순·좋아요순 정렬과 과목 필터를 제공한다.
  - **작품 페이지(링크)**: 공개된 작품은 링크(`share_token`)를 아는 사람이면 로그인 없이 누구나 열어 **실행**할 수 있다.
  - **블록 보기**: 로그인한 학원 구성원만 가능하다. 링크로 들어온 외부인에게는 실행 화면만 보여준다.
  - 공개되지 않은 작품은 본인, 교사, 관리자만 열 수 있다. 학부모 리포트에 실린 작품은 그 리포트의 `share_token`으로 열 수 있다.
- **만든 사람 표시 — 닉네임**: 커뮤니티 페이지와 작품 페이지에는 학생이 정한 **닉네임**(`USER.nickname`)을 표시한다. 실명과 이메일은 표시하지 않는다.
  - **설정 시점**: 학생은 **첫 로그인 때 닉네임을 반드시 정해야** 사이트를 쓸 수 있다. 기존 학생도 이 기능이 적용된 뒤 처음 로그인할 때 정한다. 계정 설정 화면에서 자신의 닉네임을 확인할 수 있다.
  - **규칙**: 한글·영문·숫자만 쓰고 공백과 특수문자는 쓸 수 없다. 길이는 2~12자이며, 영문과 숫자로만 된 닉네임은 3자 이상이어야 한다. 학원 안에서 중복될 수 없다 (퇴원생의 닉네임도 계속 점유).
  - **실명 불가**: 본인의 등록 이름(`USER.name`)이 들어간 닉네임은 입력 단계에서 거부한다. 그 밖의 실명·개인정보는 자동으로 걸러낼 수 없으므로 교사가 확인해 변경한다.
  - **수정**: 학생은 한 번 정한 닉네임을 스스로 바꿀 수 없다. 변경은 교사 또는 관리자가 학생 상세 화면에서 한다.
  - 교사와 관리자는 닉네임을 만들지 않는다.
- **좋아요와 댓글**: 로그인한 학원 구성원만 누르고 쓸 수 있으며, 링크로 들어온 외부인에게는 보여주지 않는다.
  - 좋아요는 작품당 한 사람이 한 번 (`PROJECT_LIKE`), 다시 누르면 취소.
  - 댓글은 글자만, 300자 이내, 답글 없음 (`PROJECT_COMMENT`). 쓰면 바로 게시된다. 작성자 본인은 자기 댓글을, 교사와 관리자는 모든 댓글을 삭제할 수 있다.
  - 금지어(욕설·비속어 목록)가 들어간 댓글은 등록을 거부한다. 금지어 목록은 개발자가 파일로 관리한다.
  - 교사와 관리자 화면에 **최근 댓글 목록**을 두어, 작품마다 들어가지 않고 한 화면에서 확인하고 삭제할 수 있게 한다.
  - 학생의 댓글 작성자는 닉네임으로 표시하고, 교사와 관리자에게는 실명도 함께 보여준다. 교사와 관리자가 쓴 댓글의 작성자는 "선생님"으로 표시한다.
- **퇴원생 작품**: 퇴원(`status = withdrawn`) 처리된 학생의 공개 작품, 좋아요, 댓글은 기한 없이 그대로 유지한다 (타자연습 랭킹과 같은 원칙, §4.1).
- **요청에 의한 삭제**: 보호자나 학생이 요청하면 관리자가 그 학생의 작품 파일(작업 중인 저장본, 모든 제출 버전, 썸네일), 영상 링크, 그 학생이 쓴 댓글을 삭제한다. 재적생과 퇴원생 모두 해당한다.
- **검색엔진**: 작품 페이지는 검색엔진이 수집하지 않도록 `noindex`로 설정한다.
- **넣지 않는 것**: 리믹스, 팔로우, 신고 기능은 첫 버전에 넣지 않는다 (§7).

#### 3.7.1 API 동작과 서버 검증

경로는 본 사이트의 기존 규칙에 맞춘다. 아래는 필요한 동작이다. 작품의 저장, 채점, 제출, 교사 열람 쪽 동작은 「스크래치 스튜디오 기획서」 8장에 있다.

| 동작 | 권한 | 내용 |
| --- | --- | --- |
| 공유 신청, 신청 취소, 공유 내리기 | 학생 본인 | 버전을 지정해 신청. 공유 상태는 버전마다 기록 |
| 공유 신청 목록, 승인, 거절, 내리기 | 교사, 관리자 | 담당 여부와 무관 |
| 커뮤니티 목록 | 로그인한 구성원 | 공개된 작품의 썸네일, 제목, 닉네임, 좋아요 수 |
| 작품 정보와 파일 (링크) | 유효한 작품 링크 토큰 또는 리포트 링크 | 공개 중인 버전만. 좋아요와 댓글은 응답에 없음 |
| 좋아요, 좋아요 취소 | 로그인한 구성원 | 공개된 작품에만 |
| 댓글 목록, 작성 | 로그인한 구성원 | 공개된 작품에만. 300자 이내 |
| 댓글 삭제 | 작성자 본인, 교사, 관리자 | 삭제한 사람과 시각을 남김 |
| 닉네임 설정 | 학생 본인 | 첫 로그인 때 1회. 이미 있으면 거부 |
| 닉네임 변경 | 교사, 관리자 | 학생 상세 화면에서 |
| 보호자 동의 표시, 해제 | 교사, 관리자 | 해제하면 그 학생의 공개 작품을 내리고 신청을 취소 |
| 최근 댓글 목록 | 교사, 관리자 | 전체 작품의 댓글을 최신순으로. 여기서 삭제 가능 |
| 학생의 작품·댓글 삭제 | 관리자 | 보호자나 학생의 요청 시. 작품 파일, 썸네일, 영상 링크, 그 학생이 쓴 댓글 |

**서버 검증**

- 공유 신청은 보호자 동의가 표시된 학생(`USER.share_consent`)의 것만 받는다.
- 공유 신청은 거절되었거나 교사가 내린 버전(`rejected`, `taken_down`)에 대해서는 거부한다. 학생이 스스로 내린 버전은 다시 신청할 수 있다.
- 닉네임은 형식, 중복, 본인 등록 이름 포함 여부를 서버에서 검사한다.
- 금지어가 들어간 댓글은 등록을 거부한다. 금지어 목록은 본 사이트 저장소의 파일로 관리한다.
- 로그인 없는 응답에는 닉네임 외의 학생 정보(실명, 이메일, 반, 내부 사용자 id)와 좋아요, 댓글을 넣지 않는다.
- 로그인 없는 요청에는 요청 빈도 제한을 건다. 작품을 내리면 링크 토큰을 폐기하고, 공개 버전만 바뀔 때는 토큰을 유지한다.
- 댓글 작성에도 요청 빈도 제한을 건다.
- 학부모 리포트 링크로는 그 리포트의 생성 시점까지 제출된 버전 중 최신 버전만 응답한다 (§3.6).

#### 3.7.2 운영 준비와 알려진 한계

학원이 운영 전에 준비해야 하는 것은 다음과 같다.

- 작품 공개 동의 항목이 들어간 등록 서류. 만 14세 미만은 법정대리인의 동의가 필요하다.
- 댓글 금지어 목록의 초안.

알고 가야 할 한계는 다음과 같다.

- 공유 전 확인을 교사 승인에만 맡긴다. 교사가 작품을 실행하고 블록, 스프라이트, 소리까지 확인하지 않으면 얼굴 사진, 목소리, 실명이 들어간 작품이 공개될 수 있다.
- 외부인에게 블록 보기를 숨기는 것은 화면상의 제한이다. 작품을 실행하려면 파일이 브라우저로 전달되므로, 파일을 직접 분석하면 블록을 볼 수 있다.
- 금지어 거르기는 목록에 있는 표현만 막는다. 변형된 표현은 교사가 최근 댓글 목록에서 확인해 삭제해야 한다.
- 닉네임은 학생이 첫 로그인 때 정하고 교사 확인 없이 바로 쓰인다. 본인의 등록 이름만 자동으로 걸러지므로, 다른 실명이나 부적절한 이름은 교사가 발견해 바꿔야 한다.
- 댓글은 확인 없이 바로 게시된다. 학생 사이의 놀림이나 다툼이 생길 수 있어, 교사가 주기적으로 확인하고 삭제하는 운영이 필요하다.

## 4. 역할별 권한표

| 기능 | Admin | Teacher | Student |
|---|---|---|---|
| 교사 계정 생성/삭제, 권한 관리 | ✅ | ❌ | ❌ |
| 전체 학생 통계 조회 | ✅ | 기본 전체 조회 + "내 담당 학생" 필터 | 본인만 |
| 과목/단원/문제/교안 등록·수정 | ✅ | ✅ | ❌ |
| 스크래치 교안·미니퀴즈·채점 규칙 등록·수정 | 조회만 (개발자가 가져오기 스크립트로 반영) | 조회만 | ❌ |
| 학생-교사 배정 관리 | ✅ | ❌ | ❌ |
| 결제/운영 정보 관리 | ✅ | ❌ | ❌ |
| 프로젝트 영상 링크(유튜브) 등록·교체 | ✅ | ✅ | 본인 것만 |
| 학생 스크래치 작품 열람 (제출 버전 + 작업 중인 저장본) | ✅ (전체 학생) | ✅ (전체 학생) | 본인 것만 |
| 커뮤니티 페이지 열람, 공개 작품의 블록 보기 | ✅ | ✅ | ✅ |
| 작품 공유 신청 / 취소 | ❌ | ❌ | 본인 것만 |
| 공유 신청 승인·거절, 공개 작품 내리기 | ✅ | ✅ (담당 무관) | ❌ |
| 좋아요, 댓글 작성 | ✅ | ✅ | ✅ |
| 닉네임 설정 (첫 로그인 때 1회) | - | - | 본인 것만 |
| 학생 닉네임 변경 | ✅ | ✅ | ❌ |
| 작품 공개 보호자 동의 표시·해제 | ✅ | ✅ | ❌ |
| 최근 댓글 목록 열람 | ✅ | ✅ | ❌ |
| 학생의 작품·댓글 삭제 (보호자 요청 시) | ✅ | ❌ | ❌ |
| 댓글 삭제 | ✅ (전체) | ✅ (전체) | 본인 것만 |
| 테스트케이스·정답 코드·해설 열람 | ✅ | ✅ | ❌ (API 응답에서 반드시 제외) |
| 교사 코멘트 열람 | ✅ | ✅ (작성 포함) | ❌ |
| 실시간 개입/페어프로그래밍 (파이썬 문제풀이만, 스크래치 제외) | ✅ (전체 학생) | ✅ (전체 학생, 담당 무관) | - |

### 4.1 재적/퇴원(`User.status`) 필터링 원칙

- 로그인: `status`가 `withdrawn`이면 비밀번호가 맞아도 로그인 거부.
- **타자연습 랭킹/기록 쿼리는 `status`로 필터링하지 않는다.** 퇴원생의 과거 기록도 랭킹에 계속 포함된다.
- **"전체 학생 통계", "담당 학생 목록" 등 재적생 조회 기능은 `status = active`로 필터링한다.**
- 퇴원 처리 시 `CLASS_STUDENT` 레코드는 삭제하지 않고 그대로 둔다 (반 소속 이력 보존). 다만 "현재 반 명단" 같은 조회는 `CLASS_STUDENT` 자체를 지우거나 필터링하는 게 아니라, 조회 시 `User.status = active` 조건으로 걸러서 퇴원생이 화면에 안 보이게 한다.

## 5. 데이터 모델 (ERD)

```mermaid
erDiagram
  USER ||--o{ TYPING_RECORD : practices
  USER ||--o{ SUBMISSION : submits
  USER ||--o{ PROJECT : creates
  USER ||--o{ QUIZ_SUBMISSION : takes
  USER ||--o{ ATTENDANCE : has
  USER ||--o{ TEACHER_COMMENT : receives
  USER ||--o{ REPORT : receives
  USER ||--o{ ENROLLMENT : enrolls
  USER ||--o{ UNIT_PROGRESS : progresses
  USER ||--o{ CLASS : teaches
  USER ||--o{ CLASS_STUDENT : belongs_to
  USER ||--o{ HELP_SESSION : receives_help
  USER ||--o{ HELP_SESSION : provides_help
  USER |o--o{ USER : creates_account
  USER |o--o{ SUBJECT : creates
  USER |o--o{ PROBLEM : creates
  PROBLEM ||--o{ HELP_SESSION : context_of
  CLASS ||--o{ CLASS_STUDENT : has
  CLASS ||--o{ CLASS_SCHEDULE : has
  CLASS |o--o{ SUBJECT : represents
  CLASS ||--o{ CLASS_CHANGE_LOG : has
  SUBJECT ||--o{ ENROLLMENT : has
  SUBJECT ||--o{ UNIT : contains
  TRACK ||--o{ SUBJECT : groups
  UNIT ||--o{ PROBLEM : contains
  UNIT ||--o{ LESSON_STEP : contains
  LESSON_STEP ||--o{ STEP_PROGRESS : tracked_by
  USER ||--o{ STEP_PROGRESS : progresses
  UNIT ||--o{ PROJECT : produces
  UNIT ||--o{ SCRATCH_PROJECT : has
  PROJECT ||--o{ PROJECT_VERSION : has
  PROJECT ||--o{ PROJECT_LIKE : liked_by
  PROJECT ||--o{ PROJECT_COMMENT : has
  USER ||--o{ PROJECT_LIKE : likes
  USER ||--o{ PROJECT_COMMENT : writes
  USER ||--o{ SCRATCH_PROJECT : saves
  USER ||--o{ DESIGN_NOTE : writes
  LESSON_STEP ||--o{ DESIGN_NOTE : answered_in
  UNIT ||--o{ QUIZ : contains
  UNIT ||--o{ UNIT_PROGRESS : tracked_by
  PROBLEM ||--o{ TEST_CASE : has
  PROBLEM ||--o{ SUBMISSION : has
  QUIZ ||--o{ QUIZ_QUESTION : has
  LESSON_STEP |o--o{ QUIZ_QUESTION : has
  QUIZ ||--o{ QUIZ_SUBMISSION : has
  PROBLEM }o--o{ CONCEPT_TAG : tagged_with
  HELP_SESSION }o--o{ CONCEPT_TAG : tagged_with

  USER {
    string id PK
    string name
    string email UK
    string nickname UK "nullable, 학생만 사용. 첫 로그인 때 설정, 변경은 교사/관리자만 (§3.7)"
    boolean share_consent "기본값 false, 작품 공개에 대한 보호자 서면 동의 여부. 교사/관리자가 표시 (§3.7)"
    string password_hash "bcrypt 해시, NextAuth Credentials Provider(email+password)용"
    string role "admin | teacher | student"
    string status "active | withdrawn, 기본값 active. 필터링 원칙은 4.1절 참고"
    string created_by FK
    string created_at
  }
  CLASS {
    string id PK
    string name
    string teacher_id FK "담당 교사 1명"
    string subject_id FK "대표 과목, nullable — 참고용 표시 목적, 학생별 실제 수강과 무관"
    string status "active | closed, 기본값 active"
  }
  CLASS_CHANGE_LOG {
    string id PK
    string class_id FK
    string field_name "예: teacher_id, subject_id 등 변경된 필드명"
    string old_value
    string new_value
    string changed_by FK
    string changed_at
  }
  CLASS_SCHEDULE {
    string id PK
    string class_id FK
    string day_of_week "MON~SUN 중 하나, 반복 요일 수만큼 행 생성 (예: 화목반=2행)"
    string start_time
    string end_time
  }
  CLASS_STUDENT {
    string id PK
    string class_id FK
    string user_id FK
  }
  SUBJECT {
    string id PK
    string name
    string category "tutorial | problem_solving"
    string editor_type "none | scratch, 기본값 none. 튜토리얼형에서만 의미 있음 (§3.3)"
    string import_key UK "nullable, 스크래치 교안 가져오기에서 과목을 찾는 키"
    string track_id FK "소속 트랙"
    string created_by FK
  }
  TRACK {
    string id PK
    string name "예: Rookies, Starter, Creator, Master"
    string age_range "예: 7세~, 참고용 텍스트"
    int order_no
  }
  ENROLLMENT {
    string id PK
    string user_id FK
    string subject_id FK
    string status "active | inactive"
    string enrolled_at
  }
  UNIT {
    string id PK
    string subject_id FK
    string title
    int order_no
    boolean is_published "공개/비공개, 기본값 false"
    string starter_project_url "nullable, 스크래치 단원의 시작용 sb3"
    string import_key "nullable, 스크래치 교안 가져오기에서 단원을 찾는 키 (과목 안에서 유일)"
  }
  UNIT_PROGRESS {
    string id PK
    string user_id FK
    string unit_id FK
    string status
    string completed_by "system | teacher"
    int time_spent "단원 학습 누적 시간(초), 튜토리얼형 진행시간 집계용"
    string completed_at
  }
  TYPING_RECORD {
    string id PK
    string user_id FK
    string practice_type "자리연습 | 낱말연습 | 단문연습 | 장문연습"
    int wpm
    float accuracy
    int duration "연습 소요시간(초)"
    string created_at
  }
  PROBLEM {
    string id PK
    string unit_id FK
    string title
    string description
    string difficulty
    string starter_code "학생에게 미리 제공되는 템플릿 코드"
    string solution_code "교사/관리자만 열람"
    string explanation "교사/관리자만 열람"
    string created_by FK
  }
  CONCEPT_TAG {
    string id PK
    string name UK
    string category "nullable"
  }
  TEST_CASE {
    string id PK
    string problem_id FK
    string input
    string expected_output
    note "교사/관리자만 열람"
  }
  SUBMISSION {
    string id PK
    string user_id FK
    string problem_id FK
    string code
    boolean is_correct
    int attempt_count
    int time_spent
    string created_at
  }
  LESSON_STEP {
    string id PK
    string unit_id FK
    int step_order
    string title
    string description
    string image_url
    json content "nullable, 스크래치 교안용 구조화 콘텐츠(텍스트/이미지/영상/블록 그림, ko/en). 있으면 title·description·image_url 대신 사용"
    string kind "lesson | design, 기본값 lesson. design은 스크래치 Lv.3 설계하기 스텝"
    json checks "nullable, 스크래치 채점 규칙. 학생에게는 해당 스텝을 채점할 때만 전달"
    string import_key "nullable, 스크래치 교안 가져오기에서 스텝을 찾는 키 (단원 안에서 유일)"
  }
  STEP_PROGRESS {
    string id PK
    string user_id FK
    string step_id FK "LESSON_STEP"
    string status "completed | incomplete"
    int attempt_count "기본값 0, 스크래치 스텝의 확인(채점) 시도 횟수"
    string completed_at
  }
  QUIZ {
    string id PK
    string unit_id FK
    string title
    int order_no "LESSON_STEP과 같은 순서체계 — 단원 내 어디에든 배치 가능"
  }
  QUIZ_QUESTION {
    string id PK
    string quiz_id FK "nullable, 단원 종료용 퀴즈일 경우"
    string step_id FK "nullable, 스텝 중간 미니퀴즈일 경우 (LESSON_STEP)"
    string question_text
    string option_a
    string option_b
    string option_c
    string option_d
    string correct_option "A | B | C | D"
    json content "nullable, 스크래치 미니퀴즈의 문항과 보기(ko/en). 있으면 question_text·option_a~d 대신 사용"
    string import_key "nullable, 스크래치 교안 가져오기에서 문항을 찾는 키 (스텝 안에서 유일)"
  }
  QUIZ_SUBMISSION {
    string id PK
    string user_id FK
    string quiz_id FK
    int score
    string submitted_at
  }
  PROJECT {
    string id PK
    string user_id FK
    string unit_id FK
    string project_link "nullable, editor_type = none 과목의 외부 공유 링크"
    string title "nullable, 스크래치 작품의 제목"
    string shared_version_id FK "nullable, 현재 공개 중인 버전 (PROJECT_VERSION)"
    string share_token UK "nullable, 작품 링크용. 처음 공개될 때 생성, 공개 버전이 바뀌어도 유지, 내리면 폐기"
    string media_url "영상/이미지. 스크래치 과목은 선택 사항이며 유튜브 링크만 허용"
    string media_uploaded_by FK "nullable, 영상 링크를 입력한 사용자 (학생 본인 또는 교사)"
    string student_note "학생이 남기는 한 줄 소감/메모"
    int teacher_score "선택 입력 (nullable)"
    string review_comment
    string submitted_at
  }
  PROJECT_VERSION {
    string id PK
    string project_id FK
    int version_no "제출할 때마다 1씩 증가"
    string file_url "제출 시점의 sb3 사본"
    string thumbnail_url "제출 시 자동 캡처한 무대 화면"
    int file_size
    string share_status "none | pending | approved | rejected | taken_down, 기본값 none (§3.7)"
    string share_reviewed_by FK "nullable, 승인·거절·내리기를 처리한 교사/관리자"
    string share_reviewed_at "nullable"
    string submitted_at
  }
  PROJECT_LIKE {
    string id PK
    string project_id FK
    string user_id FK "project_id + user_id 유일"
    string created_at
  }
  PROJECT_COMMENT {
    string id PK
    string project_id FK
    string user_id FK
    string content "300자 이내"
    string created_at
    string deleted_at "nullable"
    string deleted_by FK "nullable, 삭제한 사용자"
  }
  SCRATCH_PROJECT {
    string id PK
    string user_id FK
    string unit_id FK
    string file_url "sb3 파일 경로. 학생×단원마다 최신 저장본 1개 (user_id + unit_id 유일)"
    int file_size
    string updated_at
  }
  DESIGN_NOTE {
    string id PK
    string user_id FK
    string step_id FK "LESSON_STEP, 스크래치 Lv.3 설계하기 스텝 (user_id + step_id 유일)"
    json answers "문항별 학생의 답. 문항은 사이트 코드에 고정"
    string updated_at
  }
  ATTENDANCE {
    string id PK
    string user_id FK
    string date
    string check_in_at "등원 시각"
    string check_out_at "하원 시각"
    string status
  }
  TEACHER_COMMENT {
    string id PK
    string user_id FK
    string teacher_id FK
    string content
    string created_at
  }
  REPORT {
    string id PK
    string user_id FK
    string period_start
    string period_end
    string strengths "자동 생성"
    string improvements "자동 생성"
    string share_token UK
    string expires_at
    string generated_at
  }
  HELP_SESSION {
    string id PK
    string user_id FK "도움받은 학생"
    string helper_id FK "개입한 교사/관리자, 담당 무관"
    string problem_id FK
    string created_at
  }
```

## 6. 보안 고려사항

1. **테스트케이스/정답/해설 비공개**: `PROBLEM.solution_code`, `PROBLEM.explanation`, `TEST_CASE`는
   API 레벨에서 `role`이 `teacher`/`admin`일 때만 응답에 포함. 학생 요청 응답에는 절대 포함하지 않는다.
2. **공유 링크 만료**: `REPORT.share_token`은 `expires_at` 이후 접근 불가 처리, 필요 시 교사가 재발급 가능하도록 구현.
3. **실시간 개입 접근 통제**: `role`이 `teacher` 또는 `admin`인 계정만 학생 세션에 개입 가능하도록 서버에서 검증
   (담당 학생 여부는 제한 조건 아님, `student` role은 어떤 경우에도 타 학생 세션 접근 불가).
4. **코드 실행 샌드박스**: 학생 제출 코드는 반드시 격리된 샌드박스(리소스/시간/네트워크 제한)에서 실행.
5. **스크래치 에디터 출처 분리**: 스크래치 에디터는 본 사이트와 다른 출처(서브도메인)에서 제공한다. 이를 위해 **본 사이트의 세션 쿠키에는 도메인(`Domain` 속성)을 지정하지 않는다** (지정하면 서브도메인에서도 쿠키가 보여, 학생 작품이 실행되는 환경에서 세션 쿠키에 접근할 수 있게 된다).
   출처 검증, 임베드 제한 등 나머지 조건은 「스크래치 스튜디오 기획서」 3장 "보안"이 기준이다.
6. **스크래치 채점의 한계**: 채점이 학생 브라우저에서 실행되므로 통과 기록을 조작할 수 있다 (파이썬 `TEST_CASE`와 다른 점). 서버가 검증하는 범위와 한계는 기획서 8장 "서버 검증"과 11장 "알고 가야 할 한계"가 기준이다.
7. **작품 파일 접근 통제**: 작업 중인 저장본과 공개되지 않은 제출 버전의 읽기·쓰기 권한과 업로드 검증은 기획서 8장 "서버 검증"이, 비로그인 요청에 대한 응답은 §3.7.1이 기준이다.
8. **공개 작품의 미성년자 보호**: 작품은 교사 승인을 거쳐야 공개된다. 비로그인 응답에는 닉네임 외의 학생 정보(실명, 이메일, 반,
   내부 사용자 id)와 좋아요·댓글을 넣지 않는다. 작품 페이지는 `noindex`로 설정하고, 비로그인 요청에는 요청 빈도 제한을 건다.
   외부인에게 블록 보기를 숨기는 것은 화면상의 제한이다. 작품을 실행하려면 파일이 브라우저로 전달되므로, 파일을 직접 분석하면 블록을 볼 수 있다.
   댓글은 승인 없이 게시되므로 교사와 관리자의 삭제 수단을 반드시 제공한다. 작품 공개에 대한 보호자 동의는 서면으로 받아 학생 계정에 표시하고, 서버는 동의가 표시되지 않은 학생의 공유 신청을 거부한다 (§3.7). 금지어가 들어간 댓글은 서버에서 거부한다.
9. **미성년자 개인정보 처리**: 학생 대부분이 미성년자로 추정되므로, 데이터 보관 기간·학부모 동의·탈퇴 시
   삭제 절차 등 운영 정책을 별도로 수립 필요 (스키마 범위 밖, 법무/운영 검토 필요).

## 7. MVP 범위 밖 (추후 별도 설계)

- **결제/수강료 관리**: 별도 도메인으로 분리. 추후 `PAYMENT` 테이블을 독립적으로 추가 예정.
  관리자 학생 리포트 화면(와이어프레임 14c)의 "결제 미납/수납" 배지는 **UI 목업**으로만 존재하며, 이번 MVP 스키마엔 반영하지 않는다 (더미 데이터 또는 화면 자체 비활성 처리).
- **실시간 세션/제어권 관리**: 웹소켓 기반, 별도 기술 스펙 문서로 설계 필요 (DB 스키마 없음, Redis 등 활용 검토). 화면 UI 요소는 §3.4에서 hi-fi 기준으로 확정됨(2026-08-16) — 아래는 그 UI를 실제로 동작시키는 실시간 통신 구현 자체를 가리키며, 여전히 미착수.
- **스크래치 과목의 교사 개입**: 실시간 관찰·제어권 교환은 범위 밖 (§3.3.1). 저장된 작품의 열람은 범위 안.
- **스크래치 과목의 태블릿 지원**: 스크래치 학습 화면은 PC와 크롬북만 대상으로 한다 (§3.3.1).
- **스크래치 채점 규칙 편집 화면**: 교사가 화면에서 채점 규칙을 만드는 기능은 범위 밖. 개발자가 JSON으로 작성한다.
- **커뮤니티 기능 확장**: 리믹스, 팔로우, 신고, 댓글의 답글, 검색엔진 노출, 교사가 고른 작품의 홈페이지 소개는 범위 밖. 스크래치 외 과목의 커뮤니티 공유도 추후 확장.
- **교사 대시보드 UI 상세 설계**: 화면 목록은 정리되었으나 세부 와이어프레임은 별도 진행 필요.
- **학부모 상담 이력 관리**: 관리자 학생 리포트 화면(와이어프레임 14c)의 "마지막 상담일"은 **UI 목업**으로만 존재하며, 이번 MVP 스키마엔 반영하지 않는다. 추후 별도 상담 기록 기능 설계 시 재검토.

## 8. 화면 목록 (요약)

**학생**: 대시보드 · 타자연습 · 타자연습 랭킹 · 과목별 단원 목록 · 튜토리얼 진행 및 제출 · 스크래치 전용 학습 화면(스텝 교안 + 에디터 임베드, §3.3.1) ·
파이썬 문제 풀이 · 내 학습 리포트(실시간) · 포트폴리오 갤러리 · 커뮤니티 페이지(공개 작품 목록) · 작품 페이지(실행, 블록 보기, 좋아요, 댓글, 공유 신청) · 닉네임 설정(첫 로그인 때 필수) · 계정 설정(닉네임 확인)

**교사**: 대시보드(담당 학생 현황) · 실시간 개입 화면 · 학생 상세(이력/코멘트/프로젝트 리뷰) ·
과목/단원/문제/교안 등록·수정 · 공유 신청 목록(승인/거절) · 커뮤니티 페이지(내리기, 댓글 삭제) · 최근 댓글 목록(확인, 삭제)

- 학생 상세 화면의 작업 범위 3가지 (hi-fi 목업에 해당 화면이 없어 스펙으로만 정의 — `docs/decisions.md` 공용 기준 "화면 번호 매핑" 참고):
  - **조회**: 학생별 제출(`SUBMISSION`) · 출석(`ATTENDANCE`) · 도움요청(`HELP_SESSION`) 이력
  - **코멘트**: 교사가 자유롭게 남기는 코멘트(`TEACHER_COMMENT`) 작성 — 학생에게는 비공개(§3.6)
  - **프로젝트 리뷰**: 제출된 프로젝트(`PROJECT`)에 대한 점수(`teacher_score`)·리뷰 코멘트(`review_comment`) 작성
  - **프로젝트 영상 링크**: 교사가 촬영해 유튜브에 올린 작품 영상의 링크를 학생의 프로젝트에 등록하거나 교체 (`PROJECT.media_url`, 「스크래치 스튜디오 기획서」 5장)
  - **보호자 동의 표시와 닉네임 변경**: 작품 공개 동의 여부 표시·해제, 학생 닉네임 변경 (§3.7)
  - **작품 열람**: 학생의 제출 버전 목록과 작업 중인 저장본 열기 (「스크래치 스튜디오 기획서」 5장)
  - **설계하기 답 열람**: 스크래치 Lv.3 학생이 설계하기 스텝에 쓴 답 (`DESIGN_NOTE`, 「스크래치 스튜디오 기획서」 5장)

**관리자**: 대시보드(전체 통계) · 계정/권한 관리 · 반/시간대별 수업 스케줄 관리(그리드 뷰) ·
전체 학생 리포트 조회 · 학생의 작품·댓글 삭제(보호자 요청 시) · (교사 화면 전체 접근)

**학부모**: 공유 링크 리포트 뷰 (읽기 전용, 로그인 불필요)

**링크를 받은 누구나 (로그인 불필요)**: 공개된 작품의 작품 페이지 (실행만) — §3.7

- hi-fi 목업엔 두 안(17 "학습 리포트", 18 "월간 리포트")이 있었으나 **18("월간 리포트")로 단일채택**(2026-08-16, 사용자 결정 — 비교 근거는 `docs/decisions.md` 공용 기준 "미배정 화면 사전 조사" 참고). 구성: 학생 프로필 · 출석률/평균 타자 속도 · 과정별 진도 · 선생님 총평(잘한 점/보완할 점 구조화) · 완성 프로젝트 예시(영상/이미지) · 타자연습 추이 그래프. 17의 "최근 활동" 피드와 자유서술형 코멘트는 채택하지 않음.

---

## 10. 향후 확장 고려사항 (설계 전 메모)

MVP 범위는 아니지만, 원장님이 향후 계획 중인 확장 방향을 참고용으로 기록해둔다. 아래는 아이디어 수준이며 스키마 설계는 각 기능을 실제로 착수할 때 별도로 진행한다.

1. **결제/청구서 발송 (수강료 관리)**: 온라인 결제 연동, 자동 청구서 발송, 미납 관리.
2. **매출 통계/대시보드**: 결제 데이터를 기반으로 기간별·과목별 매출 집계.
3. **메시지 기능**: 학부모·교사·관리자 간 학원 내부 메시지/알림.
4. **교사 상담 이력 관리**: 학부모 상담 일자·내용 기록. 학생 리포트와 연동 가능성 있음.
5. **admin/teacher 계정 보안 강화**: 로그인 실패 횟수 제한(잠금), 2단계 인증(2FA) 등 학생 계정보다 강화된 정책 적용.
6. **도메인/세션 분리**: admin 영역을 서브도메인(예: `admin.dlab.kr`)으로 분리해 세션(쿠키)을 격리, 학생용 화면에서 발생한 취약점이 admin 세션까지 번지지 않도록 방어.
7. **카카오톡/SMS 알림 연동**: 출석, 리포트 생성 등 주요 이벤트 발생 시 학부모에게 자동 알림 발송.
8. **출결 자동화 (태블릿)**: 원내 태블릿 전용 출결 페이지에서 학생이 출결 번호를 입력하면 자동 체크인 처리 및 학부모 알림 발송.

## 11. 다음 단계 제안

1. 이 문서를 Claude Code에 전달하여 DB 스키마(Prisma/SQL) 및 프로젝트 구조 생성 요청
2. 실시간 페어프로그래밍 기능은 별도 기술 스펙 문서로 분리 설계
3. 핵심 사용자 흐름(예: 학생의 파이썬 문제 풀이 흐름) 플로우차트로 상세화
4. 화면별 와이어프레임 작업
5. 스크래치 스튜디오: 「스크래치 스튜디오 기획서」의 0단계(에디터 검증)부터 진행. 본 사이트의 스키마 변경(§5)은 그 결과를 확인한 뒤 반영
