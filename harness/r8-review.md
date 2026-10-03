# R8 · 검증과 리뷰

> 2026-10-03 확정

## 1. 판정 스크립트 검증 (실제로 쓰기 전)

harness/tests/fixtures/에 게이트마다 통과용 JSON과 실패용 JSON을 만들고, harness/tests/run.py로 돌린다.

| 게이트 | 통과해야 하는 입력 | 걸려야 하는 입력 |
|---|---|---|
| G1 | G1-pass | G1-fail-ref4 (레퍼런스 4개) |
| G2 | G2-pass, G2-pass-example (예시 예외) | ★ G2-fail-보장 (규칙 B) |
| G3 | G3-pass | ★ G3-fail-keepContent (규칙 A) |
| G4 | G4-pass | G4-fail-1280w (프레임 너비 1280) |
| G6 | G6-pass | G6-fail-radius10, G6-fail-hex |

**통과 기준**: 예상(PASS/FAIL)과 결과가 다른 입력이 0개다.

## 2. 훅 검증

막혀야 하는 행동과 허용돼야 하는 행동을 일부러 시켜 본다.

| 막혀야 하는 것 (6개 모두 차단) | 허용돼야 하는 것 (3개 모두 통과) |
|---|---|
| Claude가 fol-DESIGN.md 수정 | ref-analyst가 s2/에 쓰기 |
| Claude가 gates.json 직접 수정 | .unlock 상태에서 fol-DESIGN.md 수정 |
| Claude가 Write로 harness/.unlock 생성 | check.py가 gates.json 쓰기 |
| Claude가 Bash로 touch harness/.unlock | |
| ref-analyst가 s3/에 쓰기 | |
| gate-judge가 파일 쓰기 | |

**통과 기준**: 9개 모두 예상대로 동작한다.

**'ref-analyst가 s3/에 쓰기'가 안 막히면** (훅이 에이전트를 구분하지 못하는 경우):
- 에이전트 지시문으로 자기 폴더만 쓰게 한다.
- check.py가 자기 폴더 밖에서 바뀐 파일을 찾아 FAIL로 판정한다.

## 3. 파일럿

- 첫 실제 실행은 **workspace 화면**으로 한다. ("작업 공간 화면 시작해줘")
- 고른 이유: 규칙 A·B가 모두 걸리는 화면이다.

## 4. 파일럿 리뷰 (harness/reviews/workspace.md)

| 항목 | 기준 | 넘으면 할 일 |
|---|---|---|
| 게이트별 FAIL 횟수 | 기록만 | – |
| 잘못 걸린 FAIL (오탐) | 0개 | rules.json 또는 check.py 수정 |
| 걸렸어야 했는데 통과한 것 (놓침) | 0개 | 게이트 조건 추가 |
| 내가 직접 고친 횟수 | 기록만 | – |
| 기존 시안과의 차이 | 기록만 | – |

리뷰를 마친 뒤 다음 화면으로 넘어간다.
