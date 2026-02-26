'''
DOWNLOAD_DIR
'''
import subprocess
from config.default import (
    AIHUB_API_KEY,
    DOWNLOAD_DIR,
    EXTRACT_DIR,
    LOG_DIR,
    AIHUB_PROJECT_KEY,
    AIHUB_FILE_KEYS
)
from logger import pipeline_logger
from utils.utils import check_storage

@with_logging
def download_file(file_key, download_dir=DOWNLOAD_DIR) -> bool:
    command = f"aihubshell -mode d -datasetkey {AIHUB_PROJECT_KEY} -filekey {file_key} -aihubapikey {AIHUB_API_KEY}"
    # subprocess.run에 check=True를 주어 실패 시 예외가 발생하게 하면, 
    # 데코레이터가 캐치해서 상태를 FAILED로 기록합니다.
    # 문자열로 된 명령어를 실행하려면 shell=True 가 필요합니다.
    subprocess.run(command, cwd=download_dir, shell=True, check=True)
    return True
