# Contributing Guide

## 코드 스타일
- Python: PEP8 준수

## 버전 관리 (Semantic Versioning)
- `v[MAJOR].[MINOR].[PATCH]` 형식 사용
- MAJOR: 하위 호환 불가능한 변경
- MINOR: 하위 호환 가능한 기능 추가
- PATCH: 버그 수정

## 커밋 메시지 (Conventional Commits)
- `feat:` 새 기능
- `fix:` 버그 수정
- `refactor:` 리팩토링
- `docs:` 문서 수정
- `chore:` 빌드/설정 변경

## 브랜치 전략
- `main`: 안정 버전 (문서 작업 제외 직접 push 금지)
- `develop`: 개발 브랜치
- `feature/#이슈번호-설명`: 기능 개발

## PR & Merge 규칙
- 기능 개발 PR: **Squash and Merge** 사용
  - feature 브랜치의 잡다한 커밋을 1개로 압축
  - merge 후 feature 브랜치 삭제
- hotfix / release PR: **Merge Commit** 사용