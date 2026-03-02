# 🍱 food-classification

> AIHub 음식 이미지 데이터를 수집·전처리하고 EfficientNet 기반 분류 모델을 학습·배포하는 End-to-End MLOps 파이프라인

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![EfficientNet](https://img.shields.io/badge/Model-EfficientNet-green)
![GCP](https://img.shields.io/badge/GCP-Storage-orange)
![Status](https://img.shields.io/badge/status-in%20progress-yellow)

---

## 📌 프로젝트 개요

AIHub에서 제공하는 음식 이미지 데이터셋을 기반으로  
**데이터 수집 → 전처리 → 모델 학습 → 배포**까지 전 과정을 직접 구현한 MLOps 프로젝트입니다.

| 항목 | 내용 |
|------|------|
| 데이터 | AIHub 음식 이미지 데이터셋 |
| 모델 | EfficientNet (Transfer Learning) |
| 인프라 | GCP Cloud Storage |
| 실행 환경 | CPU 서버 (전처리) / GPU 서버 (학습) |

---

## 🏗️ 전체 파이프라인

```
AIHub ZIP
    ↓
image-prep-worker     ← 데이터 수집 및 전처리 (CPU 서버)
    ↓
GCP Bucket
    ↓
model-training        ← 모델 학습 및 평가 (GPU 서버)
    ↓
deploy                ← 모델 배포 및 서빙
```

---

## 📁 프로젝트 구조

```
food-classification/
├── image-prep-worker/        # 데이터 전처리 워커
│   ├── main.py
│   ├── config.py
│   ├── config.yaml
│   ├── .env.example
│   └── README.md
│
├── model-training/           # 모델 학습 (구현 예정)
│   └── README.md
│
├── deploy/                   # 모델 배포 (구현 예정)
│
├── efficientnetfoods.ipynb   # EfficientNet 프로토타입 실험
├── .gitignore
└── README.md
```

---

## 🧩 모듈 설명

### 🖼️ image-prep-worker
AIHub에서 ZIP 파일을 다운로드하여 이미지를 리사이즈하고 GCP Bucket에 적재하는 CPU 서버용 전처리 워커

→ [자세히 보기](./image-prep-worker/README.md)

```
다운로드 → ZIP 압축해제 → cv2.resize → GCP 업로드
```

### 🧠 model-training *(구현 예정)*
GCP Bucket의 전처리 이미지를 불러와 EfficientNet 기반 음식 분류 모델 학습

### 🚀 deploy *(구현 예정)*
학습된 모델을 서빙 가능한 형태로 배포

---

## 🔬 프로토타입 실험

[`efficientnetfoods.ipynb`](./efficientnetfoods.ipynb) — Google Colab 기반 EfficientNet 음식 분류 실험

- EfficientNet Transfer Learning 적용
- 음식 카테고리 분류 모델 검증

---

## 🗺️ 로드맵

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | 기본 전처리 파이프라인 구현 | ✅ 완료 |
| Phase 2 | 전처리 안정화 (예외처리, 로깅, 테스트) | 🔧 진행 중 |
| Phase 3 | 인메모리 파이프라인 + 병렬처리 | 📋 예정 |
| Phase 4 | 모델 학습 파이프라인 구현 | 📋 예정 |
| Phase 5 | 모델 배포 및 서빙 | 📋 예정 |

→ [상세 로드맵](./image-prep-worker/ROADMAP.md)

---

## ⚙️ 빠른 시작

각 모듈은 독립적으로 실행됩니다. 모듈별 README를 참고하세요.

```bash
# 전처리 워커 실행
cd image-prep-worker
cp .env.example .env  # 환경변수 설정
pip install -r requirements.txt
python main.py
```
