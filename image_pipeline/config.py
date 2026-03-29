import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Literal

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

# ========== 1-1. Source component ==========
@dataclass(frozen=True)
class AIHubSourceConfig:
    api_key: str = field(default_factory=lambda: os.getenv("AIHUB_API_KEY"))
    project_key: str = "242"
    manifest_path: Path = BASE_DIR / "manifests" / "download_list.csv"
    file_key: str = None

# ========== 1-2. Source config ==========
@dataclass(frozen=True)
class SourceConfig:
    source_type: Literal["aihub"] = "aihub"
    aihub: AIHubSourceConfig = field(default_factory=AIHubSourceConfig)
    # local: LocalSourceConfig = field(default_factory=LocalSourceConfig)
    # gcs: GCSSourceConfig = field(default_factory=GCSSourceConfig)

# ========== 2. Transform component ==========
@dataclass(frozen=True)
class TransformConfig:
    target_size: tuple[int, int]=(384, 384)
    extension: str="webp"
    quality: int=85
    interpolation: str="linear"

# ========== 3-1. Loader component ==========
@dataclass(frozen=True)
class LocalStorageConfig:
    dst_dir: Path = BASE_DIR / "data" / "tmp" / "raw"

@dataclass(frozen=True)
class GCSConfig:
    credentials_path: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    bucket_name: str = "lee_modelcamp"
    upload_src_dir: Path = BASE_DIR / "data" / "tmp" / "rdtupload"

# ========== 3-2. Loader config ==========
@dataclass(frozen=True)
class LoaderConfig:
    storage_type: Literal["local", "gcs"] = "local" 
    local: LocalStorageConfig = field(default_factory=LocalStorageConfig)
    gcs: GCSConfig = field(default_factory=GCSConfig)

# ========== 4. Log / Alert / Monitor config ==========
@dataclass(frozen=True)
class LoggingConfig:
    level: str = "INFO" 
    log_dir: Path = BASE_DIR / "data" / "logs"
    rotation: str = "1 day" 
    format: str = "%(asctime)s | %(levelname)-8s | %(worker_id)s | %(message)s"
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

    def __post_init__(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)

@dataclass(frozen=True)
class AlertConfig:
    pass

@dataclass(frozen=True)
class MonitorConfig:
    activate: bool = True
    metrics_interval: int = 10
    metrics_dir: Path = BASE_DIR / "data" / "metrics"
    save_visualize: bool = True

    def __post_init__(self):
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

# ========== 5. Pipeline config ==========
@dataclass
class PipelineConfig:
    chunk_size: int = 50
    num_consumers: int = 4
    transform_conf: TransformConfig = field(default_factory=TransformConfig)
    loader: LoaderConfig = field(default_factory=LoaderConfig)
    source: SourceConfig = field(default_factory=SourceConfig)
    
# ========== 6. System config ==========
@dataclass(frozen=True)
class SystemConfig:
    download_dir: Path = BASE_DIR / "data" / "tmp" / "raw"
    archive_dst: Path = BASE_DIR / "data" / "tmp" / "archive"
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

# ======================================================================
# --- 공통 경로 설정 ---
# ======================================================================
CURRENT_FILE_PATH = Path(__file__).resolve() # 현재 파일의 절대 경로 (image-prep-worker/config.py)
BASE_DIR = CURRENT_FILE_PATH.parent # 프로젝트 루트 디렉토리 (image-prep-worker/)
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# ======================================================================
# --- AIHub 다운로더 설정 ---
# ======================================================================
AIHUB_API_KEY = os.getenv("AIHUB_API_KEY")
DOWNLOAD_DST_DIR = DATA_DIR / "tmp" / "raw"
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
IMAGE_QUALITY = 90
# ======================================================================
# --- 압축파일 경로 설정 ---
# ======================================================================
"""전처리 이후 압축파일 경로 설정"""
ARCHIVE_SRC_DIR = TRANSFORM_DST_DIR
ARCHIVE_DST_DIR = DATA_DIR / "tmp" / "archive"

# ====================================================================== 
# --- 폴더 생성 함수 ---
# ====================================================================== 
def init_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DST_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DST_DIR.mkdir(parents=True, exist_ok=True)
    TRANSFORM_DST_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DST_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)