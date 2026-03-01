import os
from config import (
    AIHUB_FILE_KEYS,
    DOWNLOAD_DIR,
    EXTRACT_DIR,
    TRANSFORM_SRC_DIR,
    TRANSFORM_DST_DIR,
    BUCKET_NAME
)
from utils.logger import pipeline_logger
from aihub_downloader import download_file
from extractor import unzip_file
from image_transformer import run_transform_for_chunk
from archiver import compress_folder
from bucket_uploader import upload_to_s3
from cleanup_manager import cleanup_chunk_files
from utils.utils import check_storage

def run_pipeline():
    pipeline_logger.info("======================================================")
    pipeline_logger.info("🚀 AIHub MLOps 파이프라인 시작 (중앙 제어)")
    pipeline_logger.info("======================================================")


    # 1. 파일별 다운로드 -> 압축 해제 -> 변환 -> 적재 -> 정리 트랜잭션 루프
    for key in AIHUB_FILE_KEYS:
        pipeline_logger.info(f"\n--- [ {key} 트랜잭션 시작 ] ---")
        
        # [Step 1] 다운로드 시도 (이미 처리된 경우 스킵)
        # 다운로드 시작 전 용량 체크 로직 수행
        if check_storage(key, download_dir=DOWNLOAD_DIR):
            download_success = download_file(key, download_dir=DOWNLOAD_DIR)
            if not download_success:
                pipeline_logger.warning(f"❌ [에러] 파일 {key} 다운로드 실패. 해당 청크를 건너뜁니다.")
                continue
            
        # [Step 2] 압축 해제 (최신 zip 파일 기준)
        unzip_success = unzip_file(zip_dir=DOWNLOAD_DIR, extract_dir=EXTRACT_DIR)
        if not unzip_success:
            pipeline_logger.warning(f"⚠️ [오류] {key} 압축 해제 실패. 해당 청크를 건너뜁니다.")
            continue
            
        # [Step 3] 이미지 전처리 (해당 파일 캐시 디렉토리만 대상)
        current_src_dir = os.path.join(EXTRACT_DIR, str(key))
        current_dst_dir = os.path.join(TRANSFORM_DST_DIR, str(key))
        
        transform_success = run_transform_for_chunk(
            chunk_key=f"transform_{key}",
            src_root=current_src_dir,
            dst_root=current_dst_dir
        )
        if not transform_success:
            pipeline_logger.warning(f"⚠️ [오류] {key} 이미지 변환 실패. 다음 청크로.")
            continue
            
        # [Step 4] 임시 ZIP 압축 (GCP 분리 저장 전 단일 파일화)
        archive_file = compress_folder(
            chunk_key=f"archive_{key}",
            source_folder=current_dst_dir
        )
        if not archive_file:
            pipeline_logger.warning(f"⚠️ [오류] {key} 패키징(압축) 실패. 다음 청크로.")
            continue
            
        # [Step 5] 클라우드 스토리지 단일 파일 적재 (GCP Cloud Storage)
        upload_success = upload_to_s3(
            chunk_key=f"upload_{key}",
            archive_file=archive_file,
            bucket_name=BUCKET_NAME
        )
        if not upload_success:
            pipeline_logger.warning(f"⚠️ [오류] {key} 패키지(GCP) 업로드 실패.")
            continue
            
        # [Step 6] S3 업로드까지 완벽히 끝난 경우에 한해 로컬 스테이징 파일 클린업
        cleanup_chunk_files(file_key=key)
        
    pipeline_logger.info("\n🎉 전체 파일 처리 및 트랜잭션 파이프라인이 종료되었습니다!! 🎉")

if __name__ == "__main__":
    run_pipeline()
