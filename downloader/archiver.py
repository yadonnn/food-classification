import os
import shutil
from pathlib import Path
from config.default import LOG_DIR, ARCHIVE_DIR
from logger import ChunkTracker, step_monitor, pipeline_logger

archive_tracker = ChunkTracker(state_file=LOG_DIR / "archive_state.json")

@step_monitor(archive_tracker)
def compress_folder(chunk_key, source_folder, archive_dir=ARCHIVE_DIR):
    """
    지정된 폴더를 zip 파일로 압축하는 역할을 수행하는 함수 (SRP)
    """
    pipeline_logger.info(f"📦 [{chunk_key}] '{source_folder}' 로컬 데이터를 하나로 압축 시작 중...")
    
    # 임시 압축 폴더 생성
    archive_dir_path = Path(archive_dir)
    archive_dir_path.mkdir(parents=True, exist_ok=True)
    
    archive_path_without_ext = str(archive_dir_path / chunk_key)
    archive_file = archive_path_without_ext + ".zip"
    
    # 지정한 source_folder 압축
    try:
        shutil.make_archive(archive_path_without_ext, 'zip', source_folder)
        pipeline_logger.info(f"✅ [{chunk_key}] 압축 성공: {archive_file}")
        return archive_file
    except Exception as e:
        pipeline_logger.error(f"❌ [{chunk_key}] 로컬 압축 중 오류 발생: {e}")
        return False
