import subprocess
import os
import zipfile
from datetime import datetime
from config import (
    AIHUB_API_KEY,
    DOWNLOAD_DIR,
    EXTRACT_DIR,
    LOG_DIR,
    AIHUB_PROJECT_KEY,
    AIHUB_FILE_KEYS
)

def log_download_error(log_path, file_key, error):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] file_key={file_key} error={error}\n")

# 압축해제
def unzip_file(zip_path, extract_dir=EXTRACT_DIR):
	try:
		with zipfile.ZipFile(zip_path, 'r') as zip_ref:
			zip_ref.extractall(extract_dir)
		return True
	except Exception as e:
		print(f"❌ 압축 해제 실패: {e}")
		return False

def run_download(download_dir=DOWNLOAD_DIR, extract_dir=EXTRACT_DIR, log_dir=LOG_DIR):
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "download_error.log")

    for key in AIHUB_FILE_KEYS:
        print(f"📦 파일 키 {key} 다운로드 시도 중...")
        
        # 실행할 명령어 (리스트 형태 권장)
        command = f"aihubshell -mode d -datasetkey {AIHUB_PROJECT_KEY} -filekey {key} -aihubapikey {AIHUB_API_KEY}"
        
        try:
            # cwd 인자를 사용하여 해당 경로로 'cd' 한 뒤 명령어를 실행한 효과를 냄
            subprocess.run(command, cwd=download_dir, check=True)
            print(f"✅ 파일 키 {key} 완료!")
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ 파일 키 {key} 실패: {e}")
            log_download_error(log_path, key, e)
		
if __name__ == "__main__":
    run_download()
