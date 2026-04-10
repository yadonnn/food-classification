"""
Tree: Nested Structure View

AppConfig (Root)
├── pipeline (PipelineConfig)
│   ├── source (SourceConfig)
│   │   ├── source_type: "aihub", "local"
│   │   ├── aihub (AIHubSourceConfig)
│   │   └── local (LocalSourceConfig)
│   ├── transform (TransformConfig)
│   └── loader (LoaderConfig)
│       ├── storage_type: "local", "gcs"
│       ├── gcs (GCSConfig)
│       └── local (LocalStorageConfig)
└── system (SystemConfig)
    ├── logging (LoggingConfig)
    └── monitor (MonitorConfig)
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, model_validator
from typing import Literal, Optional

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# ========== 1-1. Source component ==========
class AIHubSourceConfig(BaseModel):
    api_key: SecretStr = Field(default_factory=lambda: os.getenv("AIHUB_API_KEY"))
    project_key: str = "242"
    manifest_path: Path = BASE_DIR / "manifests" / "download_list.csv"
    file_key: str|list = None

class LocalSourceConfig(BaseModel):
    src_zip_path: Path = BASE_DIR / "data" / "debug" / "sample.zip"
    label_zip_path: Path = None
    
# ========== 1-2. Source config ==========
class SourceConfig(BaseModel):
    source_type: Literal["aihub", "local"] = "local"
    raw_dir: Path = BASE_DIR / "data" / "tmp" / "raw"
    processed_dir: Path = BASE_DIR / "data" / "tmp" / "processed"
    local: LocalSourceConfig = Field(default_factory=LocalSourceConfig)
    aihub: Optional[AIHubSourceConfig] = None
    # gcs: Optional[GCSSourceConfig] = None

# ========== 2. Transform component ==========
class TransformConfig(BaseModel):
    target_size: tuple[int, int] = (384, 384)
    extension: Literal["webp", "jpeg", "png"] = "jpeg"
    quality: int = Field(default=85, ge=0, le=100)
    interpolation: Literal[
        "linear", "bilinear", "bicubic", "lanczos"] = "linear"

# ========== 3-1. Loader component ==========
class LocalStorageConfig(BaseModel):
    dst_dir: Path = BASE_DIR / "data" / "tmp" / "raw"

class GCSConfig(BaseModel):
    credentials_path: SecretStr = Field(default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    bucket_name: str
    upload_src_dir: Path = BASE_DIR / "data" / "tmp" / "rdtupload"

# ========== 3-2. Loader config ==========
class LoaderConfig(BaseModel):
    storage_type: Literal["local", "gcs"] = "local" 
    local: LocalStorageConfig = Field(default_factory=LocalStorageConfig)

    gcs: Optional[GCSConfig] = None
    @model_validator(mode="after")
    def validate_gcs_settings(self) -> 'LoaderConfig':
        if self.storage_type == "gcs" and not self.gcs.bucket_name:
            raise ValueError("GCS storage requires bucket_name")
        return self
        
# ========== 4. Log / Alert / Monitor config ==========
class LoggingConfig(BaseModel):
    level: str = "INFO" 
    log_dir: Path = BASE_DIR / "data" / "logs"
    rotation: str = "1 day" 
    format: str = "%(asctime)s | %(levelname)-8s | %(worker_id)s | %(message)s"
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

class AlertConfig(BaseModel):
    pass

class MonitorConfig(BaseModel):
    activate: bool = True
    metrics_interval: int = 1
    metrics_dir: Path = BASE_DIR / "data" / "metrics"
    save_visualize: bool = False

# ========== 5. Pipeline config ==========
class PipelineConfig(BaseModel):
    chunk_size: int = 50
    num_consumers: int = 1
    transform: TransformConfig = Field(default_factory=TransformConfig)
    loader: LoaderConfig = Field(default_factory=LoaderConfig)
    source: SourceConfig = Field(default_factory=SourceConfig)
    
# ========== 6. System config ==========
class SystemConfig(BaseModel):
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

# ========== 7. App config ==========
class AppConfig(BaseModel):
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)

    @classmethod
    def load_yaml(cls, yaml_path: str | Path) -> 'AppConfig':
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)
            