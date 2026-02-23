import subprocess
import os
import zipfile
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# 1. 경로 설정 및 API 키 로드
api_key = os.getenv("AIHUB_API_KEY")
DOWNLOAD_DIR = "data/raw/"
EXTRACT_DIR = "extracted/"
LOG_DIR = "logs/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "download_error.log")

# 2. Validation용 파일 키 리스트 (이미지 + 라벨링)
AIHUB_PROJECT_KEY = "242"
AIHUB_FILE_KEYS = [
    "49602", "49603", "49520", "49521", "49522", "49523", "49524", "49525", "49526", "49527", "49528", "49529", "49530", # 원천(Img)
    "49589", "49590", "49591", "49592", "49593", "49594", "49595", "49596", "49597", "49598", "49599", "49600", "49601"  # 라벨(Json)
]

def log_download_error(file_key, error):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] file_key={file_key} error={error}\n")

# 압축해제
def unzip_file(zip_path):
	try:
		with zipfile.ZipFile(zip_path, 'r') as zip_ref:
			zip_ref.extractall(EXTRACT_DIR)
		return True
	except Exception as e:
		print(f"❌ 압축 해제 실패: {e}")
		return False

zip_path = "raw/052.건강관리를_위한_음식_이미지_데이터/01.데이터/2.Validation/원천데이터/음식001_Val.zip"

def run_download():
    for key in AIHUB_FILE_KEYS:
        print(f"📦 파일 키 {key} 다운로드 시도 중...")
        
        # 실행할 명령어 (리스트 형태 권장)
        command = f"aihubshell -mode d -datasetkey {AIHUB_PROJECT_KEY} -filekey {key} -aihubapikey {api_key}"
        
        try:
            # cwd 인자를 사용하여 해당 경로로 'cd' 한 뒤 명령어를 실행한 효과를 냄
            subprocess.run(command, cwd=DOWNLOAD_DIR, check=True)
            print(f"✅ 파일 키 {key} 완료!")
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ 파일 키 {key} 실패: {e}")
            log_download_error(key, e)
		
if __name__ == "__main__":
    run_download()
