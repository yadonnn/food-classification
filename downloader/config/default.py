import os
from pathlib import Path
# from dotenv import load_dotenv
# load_dotenv()

# ======================================================================
# --- 공통 경로 설정 ---
# ======================================================================
CURRENT_FILE_PATH = Path(__file__).resolve() # 현재 파일의 절대 경로 (downloader/config/default.py)
BASE_DIR = CURRENT_FILE_PATH.parent.parent # 프로젝트 루트 디렉토리 (downloader/)
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"


os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
# ======================================================================
# --- AIHub 다운로더 설정 ---
# ======================================================================
AIHUB_API_KEY = os.getenv("AIHUB_API_KEY")
DOWNLOAD_DIR = DATA_DIR / "tmp" / "src"
EXTRACT_DIR = DATA_DIR / "tmp" / "extracted"
AIHUB_PROJECT_KEY = "242"
AIHUB_FILE_KEYS = [
    "49602", "49603", "49520", "49521", "49522", "49523", "49524", "49525", "49526", "49527", "49528", "49529", "49530", # 원천(Img)
    "49589", "49590", "49591", "49592", "49593", "49594", "49595", "49596", "49597", "49598", "49599", "49600", "49601"  # 라벨(Json)
]


os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)
# ====================================================================== 
# --- 이미지 전처리 설정 ---
# ====================================================================== 
TARGET_SIZE = 384
TRANSFORM_SRC_DIR = EXTRACT_DIR
TRANSFORM_DST_DIR = BASE_DIR / "data" / f"webp_{TARGET_SIZE}"


os.makedirs(TRANSFORM_SRC_DIR, exist_ok=True)
os.makedirs(TRANSFORM_DST_DIR, exist_ok=True)