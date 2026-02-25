import os
import shutil
from config.default import DOWNLOAD_DIR, EXTRACT_DIR, TRANSFORM_DST_DIR
from logger import pipeline_logger

def cleanup_chunk_files(file_key, zip_path=None):
    """
    S3 업로드까지 완벽히 완료된 청크(file_key)에 한하여
    다운로드 된 원본 zip 파일, 압축 해제된 폴더, 변환된 폴더를 일괄 삭제(정리)합니다.
    
    Args:
        file_key: AIHub 파일 키 (예: '49602')
        zip_path: 명시적으로 삭제할 zip 파일 경로 (옵션)
    """
    pipeline_logger.info(f"🧹 [{file_key}] 트랜잭션 완료 클린업(Cleanup) 시작...")
    
    cleanup_success = True
    
    # 1. 다운로드 원본 ZIP 파일 삭제
    # 명시된 zip_path가 있으면 그것을, 없으면 DOWNLOAD_DIR에서 찾음
    if not zip_path:
        zip_path = os.path.join(DOWNLOAD_DIR, f"{file_key}.zip")
    
    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
            pipeline_logger.info(f"  🗑️ 원본 ZIP 삭제 성공: {zip_path}")
        except Exception as e:
            pipeline_logger.error(f"  ❌ 원본 ZIP 삭제 실패: {zip_path} - {e}")
            cleanup_success = False
            
    # 2. 압축 해제 스테이징 폴더 삭제 (EXTRACT_DIR / file_key)
    extract_target_dir = os.path.join(EXTRACT_DIR, str(file_key))
    if os.path.exists(extract_target_dir):
        try:
            shutil.rmtree(extract_target_dir)
            pipeline_logger.info(f"  🗑️ 압축 해제 폴더 삭제 성공: {extract_target_dir}")
        except Exception as e:
            pipeline_logger.error(f"  ❌ 압축 해제 폴더 삭제 실패: {extract_target_dir} - {e}")
            cleanup_success = False

    # 3. 리사이징 변환 폴더 삭제 (TRANSFORM_DST_DIR / file_key)
    transform_target_dir = os.path.join(TRANSFORM_DST_DIR, str(file_key))
    if os.path.exists(transform_target_dir):
        try:
            shutil.rmtree(transform_target_dir)
            pipeline_logger.info(f"  🗑️ 변환 후 폴더 삭제 성공: {transform_target_dir}")
        except Exception as e:
            pipeline_logger.error(f"  ❌ 변환 후 폴더 삭제 실패: {transform_target_dir} - {e}")
            cleanup_success = False

    if cleanup_success:
        pipeline_logger.info(f"✨ [{file_key}] 클린업(Cleanup) 완벽히 종료!")
    else:
        pipeline_logger.warning(f"⚠️ [{file_key}] 클린업(Cleanup) 중 일부 실패가 있었습니다.")
        
    return cleanup_success
