import subprocess
import re
import shutil
from logger import pipeline_logger
from config import AIHUB_PROJECT_KEY

def parse_size_to_bytes(size_str):
    """'15 MB', '1 GB' 등의 문자열을 바이트 단위 정수로 변환"""
    size_str = size_str.strip().upper()
    if "GB" in size_str:
        return float(size_str.replace("GB", "").strip()) * 1024 * 1024 * 1024
    elif "MB" in size_str:
        return float(size_str.replace("MB", "").strip()) * 1024 * 1024
    elif "KB" in size_str:
        return float(size_str.replace("KB", "").strip()) * 1024
    else:
        raise ValueError(f"알 수 없는 용량 형식: {size_str}")

def check_storage(file_key, download_dir):
    """AIHub에서 파일 용량을 조회하고, 현재 디스크의 여유 공간과 비교합니다."""
    # 1. AIHub 파일 용량 조회
    pipeline_logger.info(f"[{file_key}] 다운로드 전 파일 용량 및 디스크 여유 공간 확인 중...")
    result = subprocess.run(
        f"aihubshell -mode l -datasetkey {AIHUB_PROJECT_KEY}",
        capture_output=True, text=True, shell=True
    )
    
    # ├─음식302_Val.zip | 1 GB | 49525 패턴에서 용량 부분 추출
    pattern = re.compile(r"\|([^|]+)\|[\s]*" + str(file_key))
    match = pattern.search(result.stdout)
    
    if not match:
        pipeline_logger.warning(f"⚠️ [{file_key}] AIHub에서 파일 용량 정보를 찾을 수 없습니다. 공간 체크를 건너뜁니다.")
        return True
        
    size_str = match.group(1).strip()
    required_bytes = parse_size_to_bytes(size_str)
    
    # 여유 공간을 위해 필요 용량의 1.5배를 안전 마진으로 잡음 (압축 해제 고려)
    safe_required_bytes = required_bytes * 2
    
    # 2. 현재 디스크 여유 공간 확인
    total, used, free = shutil.disk_usage(download_dir)
    
    pipeline_logger.info(f"📊 [{file_key}] 필요 용량: {size_str} (여유 마진 포함: {safe_required_bytes / (1024**3):.2f} GB)")
    pipeline_logger.info(f"💾 현재 디스크 여유 공간: {free / (1024**3):.2f} GB")
    
    if free < safe_required_bytes:
        error_msg = f"디스크 공간 부족! 여유 공간({free / (1024**3):.2f} GB)이 필요 용량({safe_required_bytes / (1024**3):.2f} GB)보다 적습니다."
        pipeline_logger.error(error_msg)
        raise OSError(error_msg)
        
    pipeline_logger.info("디스크 여유 공간이 충분합니다. 다운로드를 진행합니다.")
    return True
