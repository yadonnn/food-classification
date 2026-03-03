# Project Roadmap

본 로드맵은 Jupyter Notebook 기반의 연구 코드를 MLOps 파이프라인으로 진화시키는 과정을 담고 있습니다. 각 단계는 GitHub Milestones와 연동되어 관리됩니다.

---

## Current Status
- **Latest Version:** `v0.1.0`

---

## v0.1.0: [Pipeline] Foundation
**"기본 전처리 파이프라인 구현"**
- [x]  **Setup Automation:** `setup.sh`를 통한 클라우드 서버 환경 구축 자동화
- [x]  **Data Pipeline:** AIHub API 연동 및 데이터 다운로드, 전처리 로직 자동화
- [x]  **Baseline Prep:** 이미지 리사이징 및 WebP 변환 기본 파이프라인 구축

---

## v0.2.0: [Pipeline] Stability & Robustness
**"모듈화 및 테스트 코드 작성"**
- [ ] **Modularization:** 확장성 고려 Downloader, Processor, Uploader 모듈로 분리
- [ ] **Error Handling:** 다운로드 실패, 이미지 손상 등 예외 상황에 대한 견고한 처리 로직 구현
- [ ] **Validation:** 전처리된 이미지의 무결성 검증 자동화
- [ ] **Resume Capability:** 중단된 작업의 이어서 실행 기능 구현


## v0.3.0: [Pipeline] Scalability & Performance
**"성능 최적화 및 모듈화"**
- [ ] **Parallel Processing:** 멀티프로세싱으로 전처리 성능 개선
- [ ] **Logging System:** 로깅 시스템 구축으로 파이프라인 실행 상태 및 에러 추적
- [ ] **Configuration:** YAML/JSON 기반의 고도화된 설정 관리 체계 도입

## v0.4.0: [Training] Scalability & Performance
**"성능 최적화 및 모듈화"**
- [ ] **Parallel Processing:** 멀티프로세싱으로 전처리 성능 개선
- [ ] **Logging System:** 로깅 시스템 구축으로 파이프라인 실행 상태 및 에러 추적
- [ ] **Configuration:** YAML/JSON 기반의 고도화된 설정 관리 체계 도입

## v1.0.0: [Deploy] MLOps & Integration
**"클라우드 통합 및 모델 학습 파이프라인"**
- [ ] **Cloud Storage:** 로컬 저장소를 넘어 GCP Bucket과의 다이렉트 스트리밍 연동
- [ ] **Training Pipeline:** 가공된 데이터를 모델 학습 스크립트와 자동 연결
- [ ] **CI/CD:** GitHub Actions를 활용한 코드 검증 및 자동 배포 시스템 구축
- [ ] **Monitoring:** 처리량 및 시스템 자원 사용량 모니터링 대시보드 구성

---

## 🔗 관련 링크
- [GitHub Milestones](https://github.com/yadonnn/food-classification/milestones)에서 상세 진행 상황을 확인할 수 있습니다.
- 모든 기능 구현은 [Issues](https://github.com/yadonnn/food-classification/issues)를 통해 관리됩니다.