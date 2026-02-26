import os
import shutil
from config import DOWNLOAD_DIR, EXTRACT_DIR, TRANSFORM_DST_DIR
from utils.logger import pipeline_logger

def cleanup_chunk_files(file_key):
    """
    S3 업로드까지 완벽히 완료된 청크(file_key)에 한하여
    다운로드 된 원본 zip 파일, 압축 해제된 폴더, 변환된 폴더를 일괄 삭제(정리)합니다.
    
    Args:
        file_key: AIHub 파일 키 (예: '49602')
        zip_path: 명시적으로 삭제할 zip 파일 경로 (옵션)
    """
    pipeline_logger.info(f"🧹 [{file_key}] 트랜잭션 완료 클린업(Cleanup) 시작...")
    
    cleanup_success = True
    
    # 1. 스테이징 영역 삭제
    try:
        shutil.rmtree(DOWNLOAD_DIR)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        pipeline_logger.info(f"  🗑️ 스테이징 영역 삭제 성공: {DOWNLOAD_DIR}")
    except Exception as e:
        pipeline_logger.error(f"  ❌ 스테이징 영역 삭제 실패: {DOWNLOAD_DIR} - {e}")
        cleanup_success = False
            
    # 2. 압축 해제 스테이징 폴더 삭제 
    try:
        shutil.rmtree(EXTRACT_DIR)
        os.makedirs(EXTRACT_DIR, exist_ok=True)
        pipeline_logger.info(f"  🗑️ 압축 해제 폴더 삭제 성공: {EXTRACT_DIR}")
    except Exception as e:
        pipeline_logger.error(f"  ❌ 압축 해제 폴더 삭제 실패: {EXTRACT_DIR} - {e}")
        cleanup_success = False

    # 3. 리사이징 변환 폴더 삭제 (TRANSFORM_DST_DIR / file_key)
    try:
        shutil.rmtree(TRANSFORM_DST_DIR)
        os.makedirs(TRANSFORM_DST_DIR, exist_ok=True)
        pipeline_logger.info(f"  🗑️ 변환 후 폴더 삭제 성공: {TRANSFORM_DST_DIR}")
    except Exception as e:
        pipeline_logger.error(f"  ❌ 변환 후 폴더 삭제 실패: {TRANSFORM_DST_DIR} - {e}")
        cleanup_success = False

    if cleanup_success:
        pipeline_logger.info(f"✨ [{file_key}] 클린업(Cleanup) 완벽히 종료!")
    else:
        pipeline_logger.warning(f"⚠️ [{file_key}] 클린업(Cleanup) 중 일부 실패가 있었습니다.")
        
    return cleanup_success

# if __name__ == "__main__":