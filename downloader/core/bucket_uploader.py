import os
from config.default import LOG_DIR
from logger import ChunkTracker, step_monitor, pipeline_logger
from google.cloud import storage

upload_tracker = ChunkTracker(state_file=LOG_DIR / "upload_state.json")

@step_monitor(upload_tracker)
def upload_to_s3(chunk_key, archive_file, bucket_name):
    """
    GCS 버킷에 파일을 업로드
    """
    pipeline_logger.info(f"⬆️ [{chunk_key}] gs://{bucket_name}/ 에 이미 압축된 파일 업로드 시작...")
    
    if not archive_file or not os.path.exists(archive_file):
        pipeline_logger.error(f"❌ 업로드할 압축 파일이 존재하지 않습니다: {archive_file}")
        return False
        
    try:
        # GCP Storage 클라이언트 초기화
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        blob_name = chunk_key + ".zip"
        blob = bucket.blob(blob_name)
        
        file_size_mb = os.path.getsize(archive_file) / (1024**2)
        pipeline_logger.info(f"⬆️ [{chunk_key}] '{blob_name} ({file_size_mb:.2f} MB)' 업로드 중...")
        
        blob.upload_from_filename(archive_file)
    except Exception as e:
        pipeline_logger.error(f"❌ 업로드 중 오류 발생: {e}")
        return False
    
    pipeline_logger.info(f"✅ [{chunk_key}] 단일 압축 파일(GCS 버킷 적재) 완료! ({blob_name})")
    return True
