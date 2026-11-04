# AGENTS.md

이 저장소(temporary_BE)에서 코딩 작업을 하는 모든 에이전트(AI 코딩 도구 포함)를 위한 규칙이다.

## 작업 전 필수 사항 (MUST)

이 폴더에서 코드를 작성·수정·리뷰하기 전에 **항상** `development-guidelines/` 아래의 Markdown 문서를 모두 읽고, 그 규칙에 맞춰 작업한다.

읽어야 할 문서:

- `development-guidelines/README.md` — 가이드 전체 개요, MUST/SHOULD/MAY 의미, 우선순위
- 공통
  - `development-guidelines/common/coding-principles.md`
  - `development-guidelines/common/documentation.md`
  - `development-guidelines/common/testing.md`
  - `development-guidelines/common/security.md`
  - `development-guidelines/common/git-workflow.md`
- Backend
  - `development-guidelines/backend/be-principles.md`
  - `development-guidelines/backend/api-specification.md`
  - `development-guidelines/backend/readme-template.md`
- Frontend
  - `development-guidelines/frontend/fe-principles.md`
  - `development-guidelines/frontend/readme-template.md`

`development-guidelines/` 아래에 Markdown 문서가 새로 추가되면 위 목록에 없더라도 함께 읽는다.

## 적용 방법

- 가이드와 이 저장소의 실제 코드·구조가 다르면 임의로 판단하지 말고, 차이를 먼저 사용자에게 알린다.
- 가이드의 MUST 규칙을 지킬 수 없는 경우, 그 이유와 대안을 작업 결과에 함께 적는다.
- 가이드의 우선순위(보안·법적 요구사항 > 승인된 ADR > 가이드)를 따른다.
