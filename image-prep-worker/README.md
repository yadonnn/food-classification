# 🖼️ image-prep-worker

> AIHub 음식 이미지 데이터를 다운로드하고 리사이즈하여 GCP Bucket에 적재하는 CPU 서버용 전처리 워커

![Python](https://img.shields.io/badge/Python-3.11-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![GCP](https://img.shields.io/badge/GCP-Storage-orange)
![Version](https://img.shields.io/badge/version-v0.1.0-lightgrey)
![Status](https://img.shields.io/badge/status-Phase%202%20in%20progress-yellow)

---

## 📌 개요

MLOps 파이프라인의 **데이터 수집 및 전처리 단계**를 담당하는 독립 워커입니다.  
AIHub에서 ZIP 파일을 파일키 단위로 순차 다운로드하고, 이미지를 리사이즈한 뒤 GCP Bucket에 적재합니다.

```
AIHub ZIP (파일키 단위)
    ↓  다운로드 (aihubshell)
    ↓  ZIP 압축 해제 (cp949 인코딩 처리)
    ↓  이미지 리사이즈 (cv2.resize → WebP 변환)
    ↓  아카이브 압축
    ↓  GCP Bucket 업로드
```

| 항목 | 내용 |
|------|------|
| 실행 환경 | CPU 서버 |
| 데이터 소스 | AIHub 데이터셋 (프로젝트 키: 242) |
| 출력 포맷 | WebP (384×384) |
| 출력 대상 | GCP Cloud Storage |

---

## 📁 프로젝트 구조

```
image-prep-worker/
├── main.py           # 메인 파이프라인
├── config.py         # 환경변수 및 경로 설정
├── .env.example      # 환경변수 템플릿
├── requirements.txt  # Python 패키지 목록
├── setup.sh          # 환경 세팅 스크립트 (aihubshell 설치 포함)
├── ROADMAP.md        # 개발 로드맵
└── README.md
```

---

## ⚙️ 설정

### 1. 환경변수 설정

```bash
cp .env.example .env
```

```env
# .env
AIHUB_API_KEY=your_aihub_api_key
GOOGLE_APPLICATION_CREDENTIALS=your_gcp_service_account_key_path
```

### 2. config.py 주요 설정

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `AIHUB_PROJECT_KEY` | AIHub 데이터셋 프로젝트 키 | `242` |
| `AIHUB_FILE_KEYS` | 다운로드할 파일 키 목록 | 원천 13개 + 라벨 13개 |
| `TARGET_SIZE` | 리사이즈 해상도 | `(384, 384)` |
| `TRANSFORM_EXTENSION` | 변환 포맷 | `webp` |
| `BUCKET_NAME` | GCP Bucket 이름 | `lee_modelcamp` |

---

## 🚀 실행

### 환경 세팅 (최초 1회)

```bash
# aihubshell + Python 패키지 설치
chmod +x setup.sh
./setup.sh
```

### 파이프라인 실행

```bash
python main.py
```

---

## 🗂️ 데이터 디렉토리 구조

실행 시 자동 생성됩니다.

```
data/
└── tmp/
    ├── raw/                      # AIHub 다운로드 원본 ZIP
    ├── extracted/                # ZIP 압축 해제 결과
    ├── webp_(384, 384)/          # 리사이즈 변환 결과
    └── archive/                  # 변환 결과 재압축
```

> `data/` 디렉토리는 `.gitignore`에 포함되어 있습니다.

---

## 📦 의존성

```
opencv-python
python-dotenv
google-cloud-storage
```

---

## 🗺️ 로드맵

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | 기본 파이프라인 구현 | ✅ 완료 (`v0.1.0`) |
| Phase 2 | 안정화 (예외처리, 로깅, 테스트, 벤치마크) | 🔧 진행 중 |
| Phase 3 | 인메모리 파이프라인 + 병렬처리 | 📋 예정 |
| Phase 4 | Production Ready | 📋 예정 |

→ [상세 로드맵](./ROADMAP.md)

