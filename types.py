from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Any
import multiprocessing as mp

@dataclass(frozen=True)
class PathConfig:
    base_dir: Path
    data_dir: Path
    tmp_dir: Path
    log_dir: Path
    log_file: Path
    # 단계별 경로
    download_dir: Path
    extract_dir: Path
    transform_dir: Path
    archive_dir: Path

@dataclass(frozen=True)
class AIHubConfig:
    api_key: str
    project_key: str
    file_keys: List[str]
    manifest_path: Path

@dataclass(frozen=True)
class TransformConfig:
    target_size: tuple[int, int]=(384, 384)
    extension: str="webp"
    quality: int=85

@dataclass(frozen=True)
class GCSConfig:
    credentials_path: Optional[str]
    bucket_name: str
    upload_src_dir: Path

@dataclass
class PipelineContext:
    worker_id: Any
    in_queue: Optional[mp.Queue] = None
    out_queue: Optional[mp.Queue] = None
    metrics_dict: Optional[dict] = None