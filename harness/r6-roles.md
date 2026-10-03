# R6 · 역할

> 2026-10-03 확정

## 작업 에이전트 (단계마다 1개)

| 에이전트 | 단계 | 편집 폴더 (runs/<화면>/) | Figma 페이지 | 읽기만 하는 것 |
|---|---|---|---|---|
| ref-collector | S1 | s1/ | 01 레퍼런스 | rules.json |
| ref-analyst | S2 | s2/ | 02 분석 | s1/, fol-story-service.md, rules.json |
| screen-planner | S3 | s3/ | 03 화면설계 | s2/, fol-story-service.md, fol-PRD.md, rules.json |
| keyscreen-maker | S4 | s4/ | 04 키스크린 | s3/, fol-DESIGN.md, rules.json |
| ui-designer | S5 | s5/ | 05 최종 | s4/, fol-DESIGN.md, rules.json |

- 에이전트는 자기 폴더와 자기 Figma 페이지만 고친다.
- 기준 문서(fol-PRD.md, fol-DESIGN.md, fol-story-*.md, harness/)는 모든 에이전트가 읽기만 한다.
- 에이전트 정의는 `.claude/agents/<이름>.md`에 둔다.
- 로컬 폴더 제한은 R7·R8에서 훅(PreToolUse)으로 강제한다. Figma 페이지 제한은 도구로 막을 수 없어 에이전트 지시문으로 지킨다.

## 읽기 전용 판정자

- **harness/gates/check.py**: G1~G6를 판정하고, gates.json에 PASS/FAIL과 실패 횟수를 쓴다. gates.json을 쓰는 건 이 스크립트뿐이다.
- **gate-judge 에이전트**: 도구는 Read와 Bash(check.py 실행만)뿐이다. Edit·Write가 없어서 산출물을 고칠 수 없다. 실패한 항목을 설명하고, 돌아갈 단계를 알려준다.
- **G5**: 내가 직접 입력한다. (`check.py G5 --approve` / `--reject`)

## 자연어 트리거

| 내가 하는 말 | 하는 일 |
|---|---|
| "<화면> 화면 시작해줘" | runs/<화면>/을 만들고 S1부터 실행 |
| "<화면> 이어서 해줘" | gates.json을 보고 다음 단계부터 실행 |
| "<화면> 상태 보여줘" | 게이트별 PASS/FAIL과 실패 횟수를 보여줌 |
| "<화면> G5 승인" | G5를 approved로 기록하고 S5 실행 |
| "<화면> G5 반려: <사유> (S3/S4로)" | G5를 rejected로 기록하고 해당 단계로 돌아감 |

화면 이름: 로그인·내 프로젝트·프로젝트 시작/자료 입력·프로젝트 작업 공간·문서 미리보기/다운로드 → login·projects·intake·workspace·preview
