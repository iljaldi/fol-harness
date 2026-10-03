# R4 · 산출물

> 2026-10-03 확정

## 단계별 파일

산출물은 Figma 페이지에 만들고, 판정 스크립트가 셀 기록은 로컬 JSON으로 남긴다.

| 단계 | Figma 페이지 | 로컬 기록 (runs/<화면>/) | 담는 값 |
|---|---|---|---|
| S1 | 01 레퍼런스 | s1/s1-reference.json | 레퍼런스 목록 (id, uibowl 링크) |
| S2 | 02 분석 | s2/s2-analysis.json | 반영 포인트 (id, 내용, 출처 레퍼런스 id, 유저스토리 번호, 태그) |
| S3 | 03 화면설계 | s3/s3-spec.json | 화면 목적, 구성 요소, 상태, 이동 흐름 (keepContent·keepChat·resetStep·keepLogin 포함) |
| S4 | 04 키스크린 | s4/s4-keyscreen.json | 프레임 목록 (이름, 너비, 높이, 레이어 이름) |
| S5 | 05 최종 | s5/s5-final.json | Figma에서 뽑은 색·폰트·글자 크기·굵기·radius·간격·터치 영역 |
| 게이트 | – | gates.json | 게이트별 결과, 실패 횟수, 마지막 통과 게이트, G5 승인 기록 |

Figma는 파일 1개를 쓰고, 주소는 `harness/figma.json`에 둔다. 페이지 이름은 화면 이름을 앞에 붙여 `<화면> · 01 레퍼런스`처럼 쓴다.

`<화면>`은 R2의 입력값(login, projects, intake, workspace, preview)이다. 단계별 하위 폴더(s1/~s5/)는 R6에서 정한 에이전트별 편집 폴더다.

## 규칙 SSOT

**harness/rules.json 1개.** fol-DESIGN.md와 fol-story-service.md의 규칙을 셀 수 있는 값으로 옮기고, 항목마다 출처를 적는다.

- fol-DESIGN.md에서 옮기는 것: 색 토큰, 폰트, 타입 스케일, 굵기, radius, spacing, 터치 영역 최소 크기
- fol-story-service.md에서 옮기는 것: 규칙 A(keepContent·keepChat), 규칙 B(금지어, 예시 예외), MVP 제외 기능
- 기타: 프레임 너비 1440px·최소 높이 900px, 키스크린 2~3개, 레퍼런스 5개

## 재개

- 재개할 수 있다. gates.json의 '마지막 통과 게이트'를 보고 그다음 단계부터 이어서 실행한다.
- G5에서 관계자 컨펌을 기다리는 동안 멈춰도, 다시 실행하면 G5부터 이어진다.
- 폴더를 git 저장소로 만들고, 게이트를 통과할 때마다 커밋한다.
