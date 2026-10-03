# R0 · 준비물 확인

> 2026-10-03 확정

## 컨텍스트 문서

| 문서 | 상태 | 하네스에서 맡을 역할 |
|---|---|---|
| fol-PRD.md | 있음 | 서비스 원본 |
| fol-story-service.md | 있음 (R1-A) | 유저스토리, 규칙 A·B → G2·G3 기준 |
| fol-story-workflow.md | 있음 (R1-B) | 7단계 작업, 게이트 6개 |
| fol-DESIGN.md | 있음 | 디자인 시스템 원문 (사람이 읽는 문서) |
| harness/rules.json | R4에서 만듦 | 판정 스크립트가 읽는 규칙 SSOT |
| CLAUDE.md | 없음 | R7에서 작성 |
| git 저장소 | 아님 | R4 결정에 따라 초기화 |

## 결정 사항

1. **G6 기준**: fol-DESIGN.md가 원문이고, 판정은 fol-DESIGN.md에서 옮긴 rules.json으로 한다. fol-DESIGN.md가 바뀌면 rules.json도 함께 고친다.
2. **산출물 위치**: Figma에 직접 만든다. 분석, 화면 설계, 키스크린, 최종 화면 모두 Figma MCP로 작업한다.
3. **프레임 기준**: fol-DESIGN.md가 반응형 웹이므로 키스크린은 PC(데스크톱) 기준 1440px 너비로 그린다. 높이는 고정하지 않고 화면별 내용에 맞춘다(최소 900px).
4. **레퍼런스 수집**: 경쟁 서비스 목록 없이 uibowl에서 검색어 4개(`AI 어시스턴트`, `프로젝트 관리`, `문서 에디터`, `채널톡`)로 찾고, 대상 화면마다 레퍼런스 5개를 모은다.

## 도구 연결 상태

| 도구 | 상태 | 해야 할 일 |
|---|---|---|
| uibowl MCP | 연결됨 | – |
| Figma MCP | 인증 필요 | 하네스를 실행하기 전에 인증한다. 파일: `fol-harness` (fileKey `3mCgJqOTZzSE9hFDFHiR9f`) |
