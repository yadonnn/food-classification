'''
aihubshell 이용 가이드: https://www.aihub.or.kr/devsport/apishell/list.do
'''
import subprocess
from config import (
    AIHUB_API_KEY,
    DOWNLOAD_DST_DIR,
    EXTRACT_DST_DIR,
    AIHUB_PROJECT_KEY,
    AIHUB_FILE_KEYS,
    AIHUB_MANIFEST_CSV_PATH
)
from pathlib import Path
from logger import time_logger

@time_logger
def download_file(
        file_key: str | int,
        file_name: str,
        download_dir: Path = DOWNLOAD_DST_DIR,
        manifest_csv_path: Path = AIHUB_MANIFEST_CSV_PATH) -> Path:
    file_key = str(file_key)

    command = f"aihubshell -mode d -datasetkey {AIHUB_PROJECT_KEY} -filekey {file_key} -aihubapikey {AIHUB_API_KEY}"
    subprocess.run(command, cwd=download_dir, shell=True, check=True)

    # 해당 키로 다운로드된 .zip 파일을 찾습니다.
    try:
        downloaded_file_path = next(download_dir.rglob(file_name))
        return downloaded_file_path
    except StopIteration:
        raise FileNotFoundError(f"Download failed for key: {file_key}")

# if __name__ == "__main__":
# 	print(download_file("49525", "음식302_Val.zip"))