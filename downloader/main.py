import multiprocessing
import time
import argparse

from aihub_downloader import download_worker
from extractor import extract_worker
from image_transformer import transform_worker
from bucket_uploader import upload_worker

def run_pipeline(is_test=False):
    print("🚀 병렬 처리 파이프라인 시작")
    if is_test:
        print("⚠️ 테스트 모드로 실행 중 (다운로더 모킹 시 해당 로직 연동 가능)")
    
    # 프로세스 간 통신 큐 (maxsize로 Backpressure 제어)
    zip_queue = multiprocessing.Queue(maxsize=2)
    folder_queue = multiprocessing.Queue(maxsize=5)
    upload_queue = multiprocessing.Queue(maxsize=50)
    
    # 워커 프로세스 초기화
    p_download = multiprocessing.Process(target=download_worker, args=(zip_queue,))
    p_extract = multiprocessing.Process(target=extract_worker, args=(zip_queue, folder_queue))
    p_transform = multiprocessing.Process(target=transform_worker, args=(folder_queue, upload_queue))
    p_upload = multiprocessing.Process(target=upload_worker, args=(upload_queue,))
    
    # 소비자(Consumer)부터 프로세스 시작
    p_upload.start()
    p_transform.start()
    p_extract.start()
    p_download.start()
    
    # 다운로더가 자신의 작업을 마친 후 Queue에 Poison Pill(None)을 전송하여
    # 뒤이은 파이프라인 프로세스들이 연쇄적으로 안전하게 종료됨
    p_download.join()
    p_extract.join()
    p_transform.join()
    p_upload.join()
    
    print("✅ 파이프라인 동작 완료!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Food Classification Data Pipeline")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    multiprocessing.set_start_method("spawn", force=True)
    start_time = time.time()
    run_pipeline(is_test=args.test)
    print(f"⏱️ 총 소요 시간: {time.time() - start_time:.2f}초")

