import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# ======================================================================
# --- 공통 경로 설정 ---
# ======================================================================
CURRENT_FILE_PATH = Path(__file__).resolve() # 현재 파일의 절대 경로 (image-prep-worker/config.py)
BASE_DIR = CURRENT_FILE_PATH.parent # 프로젝트 루트 디렉토리 (image-prep-worker/)
DATA_DIR = BASE_DIR / "data"

# ======================================================================
# --- AIHub 다운로더 설정 ---
# ======================================================================
AIHUB_API_KEY = os.getenv("AIHUB_API_KEY")
DOWNLOAD_DST_DIR = DATA_DIR / "tmp" / "src"
AIHUB_PROJECT_KEY = "242"
AIHUB_FILE_KEYS = [
    "49602", "49603", "49520", "49521", "49522", "49523", "49524", "49525", "49526", "49527", "49528", "49529", "49530", # 원천(Img)
    "49589", "49590", "49591", "49592", "49593", "49594", "49595", "49596", "49597", "49598", "49599", "49600", "49601"  # 라벨(Json)
]
AIHUB_MANIFEST_CSV_PATH = BASE_DIR / "manifests" / "download_list.csv"
# ======================================================================
# --- 압축파일 경로 설정 ---
# ======================================================================
"""다운로드 이후 압축파일 경로 설정"""
EXTRACT_SRC_DIR = DOWNLOAD_DST_DIR
EXTRACT_DST_DIR = DATA_DIR / "tmp" / "extracted"

# ====================================================================== 
# --- 이미지 전처리 설정 ---
# ====================================================================== 
TRANSFORM_SRC_DIR = EXTRACT_DST_DIR
TARGET_SIZE = 384
TRANSFORM_EXTENSION = "webp"
TRANSFORM_DST_DIR = DATA_DIR / "tmp" / f"{TRANSFORM_EXTENSION}_{TARGET_SIZE}"

# ======================================================================
# --- 압축파일 경로 설정 ---
# ======================================================================
"""전처리 이후 압축파일 경로 설정"""
ARCHIVE_SRC_DIR = TRANSFORM_DST_DIR
ARCHIVE_DST_DIR = DATA_DIR / "tmp" / "archive"

# ====================================================================== 
# --- GCS 버킷 설정 ---
# ====================================================================== 
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = "lee_modelcamp"
UPLOAD_SRC_DIR = DATA_DIR / "tmp" / "rdtupload"
# UPLOAD_DST_DIR

# ====================================================================== 
# --- 폴더 생성 함수 ---
# ====================================================================== 
def init_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DST_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DST_DIR.mkdir(parents=True, exist_ok=True)
    TRANSFORM_DST_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DST_DIR.mkdir(parents=True, exist_ok=True)
