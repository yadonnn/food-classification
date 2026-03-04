'''
aihubshell 이용 가이드: https://www.aihub.or.kr/devsport/apishell/list.do
'''
import subprocess
from config import (
    AIHUB_API_KEY,
    DOWNLOAD_DST_DIR,
    EXTRACT_DST_DIR,
    AIHUB_PROJECT_KEY,
    AIHUB_FILE_KEYS
)

def download_file(file_key, download_dir=DOWNLOAD_DST_DIR) -> bool:
    command = f"aihubshell -mode d -datasetkey {AIHUB_PROJECT_KEY} -filekey {file_key} -aihubapikey {AIHUB_API_KEY}"
    subprocess.run(command, cwd=download_dir, shell=True, check=True)
    return True

if __name__ == "__main__":
    download_file(AIHUB_FILE_KEYS[0])