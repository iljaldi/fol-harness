# R7 · 오케스트레이터

> 2026-10-03 확정
> 오케스트레이터는 CLAUDE.md를 읽고 움직이는 메인 Claude다.

## 하는 일

1. 트리거를 읽고 <화면>을 정한다.
2. gates.json을 보고 실행할 단계를 정한다.
3. 그 단계의 에이전트를 부른다.
4. 게이트 자리에 오면 gate-judge를 부른다.
5. 판정 결과에 따라 움직인다.
   - PASS: git 커밋 후 다음 단계로 간다.
   - FAIL: r3-pipeline.md 표대로 되돌아간다.
   - 같은 게이트 3회 FAIL: 멈추고 나에게 묻는다.
6. G5 자리에서는 Figma 링크를 보여주고 멈춘다. 내가 입력할 때까지 기다린다.

## 하지 않는 일

- S1~S5 작업을 직접 하지 않는다.
- gates.json을 직접 고치지 않는다.
- 기준 문서와 rules.json을 고치지 않는다.
- 게이트를 건너뛰지 않는다.

## 훅으로 강제하기

- `.claude/settings.json`에 PreToolUse 훅을 걸고, `harness/hooks/guard.py`가 Edit·Write를 검사한다.
- 막는 것 (막으면 이유를 출력한다)
  - 기준 문서 수정: fol-PRD.md, fol-DESIGN.md, fol-story-*.md, harness/ 아래 전부
  - gates.json 직접 수정 (check.py만 쓴다)
  - 에이전트가 자기 sN/ 폴더 밖에 쓰기
- 잠금 해제
  - 내가 `! touch harness/.unlock`을 실행하면 기준 문서와 rules.json을 고칠 수 있다.
  - 다 고친 뒤에는 `! rm harness/.unlock`으로 다시 잠근다.
  - .unlock이 있어도 gates.json 직접 수정과 에이전트 폴더 제한은 그대로다.
  - Claude가 .unlock을 만들려고 하면 막는다.

## CLAUDE.md 구성

150줄 이하로 짧게 쓰고, 자세한 내용은 harness/r*.md를 가리킨다.

1. 이 폴더는 무엇인가 (3줄)
2. 트리거 5개
3. 단계·에이전트·게이트 흐름 표
4. 오케스트레이터가 하는 일 / 하지 않는 일
5. 절대 규칙: 게이트 건너뛰기 금지, 기준 문서 읽기 전용, 규칙 A·B
6. 자세한 내용: harness/r0~r8 링크

## R8로 넘기는 확인 사항

- Bash로 .unlock을 만들거나 보호 파일을 고치는 우회를 guard.py가 막는지
- 훅 입력에서 '어느 에이전트가 쓰는지'를 알 수 있는지 (모르면 sN/ 폴더 제한 방식을 바꾼다)
