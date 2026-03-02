# 🗺️ Project Roadmap: Food Classification Pipeline

본 로드맵은 주피터 노트북 기반의 연구 코드를 고성능 MLOps 파이프라인으로 진화시키는 과정을 담고 있습니다. 각 단계는 GitHub Milestones와 연동되어 관리됩니다.

---

## 📍 현재 진행 상태 (Current Status)
- **Current Phase:** Phase 1 (Foundation) 완료 및 Phase 2 진입 중
- **Latest Version:** `v0.1.0`

---

## 🛠️ Phase 1: Foundation (v0.1.0) - 완료 ✅
**"실험에서 엔지니어링으로의 전환"**
- [x] **Notebook Migration:** .ipynb 프로토타입 코드를 실행 가능한 파이썬 스크립트로 이식
- [x] **Setup Automation:** `setup.sh`를 통한 클라우드 서버 원스텝 환경 구축 자동화
- [x] **Data Pipeline:** AIHub API 연동 및 데이터 다운로드 로직 자동화
- [x] **Baseline Prep:** 이미지 리사이징 및 WebP 변환 기본 파이프라인 구축

---

## 🚀 Phase 2: Scalability & Performance (v0.2.0) - 진행 중 🏗️
**"성능 최적화 및 모듈화"**
- [ ] **Modularization:** 통짜 함수(`main.py`)를 Downloader, Processor, Uploader 모듈로 분리
- [ ] **Parallel Processing:** `ProcessPoolExecutor`를 활용한 이미지 전처리 속도 최적화
- [ ] **Logging System:** `logging` 모듈 도입으로 파이프라인 실행 상태 및 에러 추적 시스템 구축
- [ ] **Configuration:** YAML/JSON 기반의 고도화된 설정 관리 체계 도입

---

## ☁️ Phase 3: MLOps & Integration (v0.3.0+) - 예정 📅
**"클라우드 통합 및 모델 학습 파이프라인"**
- [ ] **Cloud Storage:** 로컬 저장소를 넘어 GCP Bucket과의 다이렉트 스트리밍 연동
- [ ] **Training Pipeline:** 가공된 데이터를 모델 학습 스크립트와 자동 연결
- [ ] **CI/CD:** GitHub Actions를 활용한 코드 검증 및 자동 배포 시스템 구축
- [ ] **Monitoring:** 처리량 및 시스템 자원 사용량 모니터링 대시보드 구성

---

## 🔗 관련 링크
- [GitHub Milestones](https://github.com/yadonnn/food-classification/milestones)에서 상세 진행 상황을 확인할 수 있습니다.
- 모든 기능 구현은 [Issues](https://github.com/yadonnn/food-classification/issues)를 통해 관리됩니다.