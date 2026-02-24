import subprocess
import os
import glob
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 1. 경로 설정 및 API 키 로드
api_key = os.getenv("AIHUB_API_KEY")
DOWNLOAD_DIR = "data/raw/"
LABEL_DIR = "data/labels/"
LOG_DIR = "logs/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "download_error.log")

# 2. Validation용 파일 키 리스트 (이미지 + 라벨링)
AIHUB_PROJECT_KEY = "242"
# AIHUB_FILE_KEYS = [
#     "49602", "49603", "49520", "49521", "49522", "49523", "49524", "49525", "49526", "49527", "49528", "49529", "49530", # 원천(Img)
#     "49589", "49590", "49591", "49592", "49593", "49594", "49595", "49596", "49597", "49598", "49599", "49600", "49601" # 라벨(Json)
# ]
AIHUB_FILE_KEYS = [
    "49520", "49528", "49529",
    "49589", "49590", "49591", "49592", "49593", "49594", "49595", "49596", "49597", "49598", "49599", "49600", "49601" 
]

LABEL_KEYS = {
    "49589", "49590", "49591", "49592", "49593", "49594", "49595", "49596", "49597", "49598", "49599", "49600", "49601"
}

def log_download_error(file_key, error):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] file_key={file_key} error={error}\n")

def get_zip_files(directory):
    search_pattern = os.path.join(os.path.abspath(directory), "**", "*.zip")
    return set(glob.glob(search_pattern, recursive=True))

def download_worker(zip_queue, is_test=False):
    """
    다운로더 워커 함수:
    aihubshell로 파일을 다운로드하고, 새로 다운로드된 ZIP 파일 경로를 zip_queue에 넣습니다.
    (is_test=True일 경우 mock_generator를 사용합니다.)
    """
    # 테스트 모드일 경우 대상을 줄여서 1개만 수행
    keys_to_download = AIHUB_FILE_KEYS[:1] if is_test else AIHUB_FILE_KEYS
    
    for key in keys_to_download:
        is_label = key in LABEL_KEYS
        target_dir = LABEL_DIR if is_label else DOWNLOAD_DIR
        
        print(f"📦 파일 키 {key} 다운로드 시도 중... (Test Mode: {is_test})")
        
        before_files = get_zip_files(target_dir)
        
        try:
            if is_test:
                from tests.mock_generator import create_mock_zip
                # 가상의 경로에 ZIP 생성
                mock_filename = f"test_data_{key}.zip"
                mock_path = os.path.join(target_dir, mock_filename)
                create_mock_zip(mock_path)
            else:
                command = f"aihubshell -mode d -datasetkey {AIHUB_PROJECT_KEY} -filekey {key} -aihubapikey {api_key}"
                subprocess.run(command, cwd=target_dir, shell=True, check=True)
            
            print(f"✅ 파일 키 {key} 완료!")
            
            after_files = get_zip_files(target_dir)
            new_files = after_files - before_files
            
            if new_files:
                for new_zip in new_files:
                    if is_label:
                        print(f"라벨 파일 저장 완료 (Queue 제외): {new_zip} (filekey: {key})")
                    else:
                        print(f"새로 다운로드된 파일 큐에 추가: {new_zip} (filekey: {key})")
                        zip_queue.put((new_zip, key))
            else:
                print(f"⚠️ 파일 키 {key} 완료. 새 ZIP 파일 발견 안됨.")
                
        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            print(f"❌ 파일 키 {key} 실패: {e}")
            log_download_error(key, e)

    # Poison pill for Extractor
    zip_queue.put(None)
    print("다운로더 워커 종료 신호 전송")
