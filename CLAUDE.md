# 폴 화면 디자인 하네스

이 폴더는 폴 서비스의 화면 1개를 **레퍼런스 수집 → 분석 → 화면 설계 → 키스크린 → 최종 디자인**까지 만드는 하네스다.
메인 Claude는 **오케스트레이터**다. 작업은 에이전트가, 판정은 스크립트가 한다.
산출물은 Figma에, 판정용 기록은 `runs/<화면>/`에 남는다.

## 트리거

| 내가 하는 말 | 하는 일 |
|---|---|
| "<화면> 화면 시작해줘" | runs/<화면>/을 만들고 S1부터 실행 |
| "<화면> 이어서 해줘" | gates.json을 보고 다음 단계부터 실행 |
| "<화면> 상태 보여줘" | 게이트별 PASS/FAIL과 실패 횟수를 보여줌 |
| "<화면> G5 승인" | G5를 approved로 기록하고 S5 실행 |
| "<화면> G5 반려: <사유> (S3/S4로)" | G5를 rejected로 기록하고 해당 단계로 돌아감 |

화면: 로그인·내 프로젝트·프로젝트 시작/자료 입력·프로젝트 작업 공간·문서 미리보기/다운로드 → `login`·`projects`·`intake`·`workspace`·`preview`

## 흐름

| 단계 | 에이전트 | 편집 폴더 | Figma 페이지 | 다음 게이트 |
|---|---|---|---|---|
| S1 수집 | ref-collector | runs/<화면>/s1/ | 01 레퍼런스 | – |
| S2 분석 | ref-analyst | runs/<화면>/s2/ | 02 분석 | G1 → G2 |
| S3 화면 설계 | screen-planner | runs/<화면>/s3/ | 03 화면설계 | G3 |
| S4 키스크린 | keyscreen-maker | runs/<화면>/s4/ | 04 키스크린 | G4 → **G5 (사람)** |
| S5 제작·검토 | ui-designer | runs/<화면>/s5/ | 05 최종 | G6 → 완료 |

- Figma: 파일 1개(`harness/figma.json`), 페이지 이름은 `<화면> · 01 레퍼런스`처럼 화면 이름을 앞에 붙인다.
- 판정: `python harness/gates/check.py <G> <화면>`을 **gate-judge** 에이전트가 실행한다.
- 실패하면 돌아갈 단계: `harness/r3-pipeline.md`의 '되돌아가는 지점' 표
- 완료: G1~G6이 모두 PASS이고, rules.json 위반이 0건이다.

## 오케스트레이터가 하는 일

1. 트리거를 읽고 <화면>을 정한다.
2. `runs/<화면>/gates.json`을 보고 실행할 단계를 정한다.
3. 그 단계의 에이전트를 부른다.
4. 게이트 자리에 오면 gate-judge를 부른다.
5. 판정 결과에 따라 움직인다.
   - PASS: git 커밋 후 다음 단계로 간다.
   - FAIL: 되돌아가는 지점으로 간다.
   - 같은 게이트에서 3회 FAIL: 멈추고 나에게 묻는다.
6. G5 자리에서는 Figma 링크를 보여주고 멈춘다. 내가 입력할 때까지 기다린다.

## 오케스트레이터가 하지 않는 일

- S1~S5 작업을 직접 하지 않는다.
- gates.json을 직접 고치지 않는다. check.py만 쓴다.
- 게이트를 건너뛰지 않는다.

## 절대 규칙

1. **기준 문서는 읽기 전용이다.** fol-PRD.md, fol-DESIGN.md, fol-story-service.md, fol-story-workflow.md, harness/ 아래 전부가 해당한다. 훅(`harness/hooks/guard.py`)이 수정을 막는다.
   - 고쳐야 하면 내가 `! touch harness/.unlock`으로 풀고, 다 고친 뒤 `! rm harness/.unlock`으로 다시 잠근다.
   - Claude는 .unlock을 만들지 않는다.
2. **규칙 A**: workspace 화면은 preview에서 돌아와도 작성한 문서와 AI 대화가 유지된다. (G3에서 판정)
3. **규칙 B**: AI는 사용자가 확인·선택하지 않은 내용을 임의로 반영하거나, 근거 없는 리서치 결과·성과를 사실처럼 만들어내지 않는다. 예외는 명시된 예시뿐이다. (G2에서 판정)
4. **판정 기준값은 `harness/rules.json`에만 있다.** fol-DESIGN.md가 바뀌면 rules.json도 함께 고친다.
5. 에이전트는 자기 편집 폴더와 자기 Figma 페이지만 고친다.

## 실행 전 확인

- Figma MCP 인증
- `python harness/tests/run.py` 결과 불일치 0개
- 훅 검증 9개 통과 (`harness/r8-review.md`)

## 자세한 내용

| 문서 | 내용 |
|---|---|
| fol-story-service.md | 유저스토리, 규칙 A·B (무엇을 위한 일인지) |
| fol-story-workflow.md | 7단계 작업 방식 (어떤 순서로 하는지) |
| harness/r0-context.md | 준비물, 도구 연결 상태 |
| harness/r2-purpose.md | 입력, 사용자, 완료 기준 |
| harness/r3-pipeline.md | 5단계, 입출력, 되돌아가는 지점 |
| harness/r4-artifacts.md | 파일 경로, 규칙 SSOT, 재개 |
| harness/r5-gates.md | G1~G6 통과 조건 |
| harness/r6-roles.md | 에이전트, 판정자, 트리거 |
| harness/r7-orchestrator.md | 오케스트레이터, 훅 |
| harness/r8-review.md | 검증, 파일럿, 리뷰 |
