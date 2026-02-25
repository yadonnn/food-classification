import subprocess
from config.default import (
    AIHUB_API_KEY,
    DOWNLOAD_DIR,
    EXTRACT_DIR,
    LOG_DIR,
    AIHUB_PROJECT_KEY,
    AIHUB_FILE_KEYS
)
from logger import ChunkTracker, step_monitor

# 1. 다운로드 작업을 트래커로 모니터링 (첫 번째 인자가 chunk_key로 사용됨)
download_tracker = ChunkTracker(state_file=LOG_DIR / "download_state.json")

# 2. 다운로드 작업을 트래커로 모니터링 (첫 번째 인자가 chunk_key로 사용됨)
@step_monitor(download_tracker)
def download_file(file_key, download_dir=DOWNLOAD_DIR):
    command = f"aihubshell -mode d -datasetkey {AIHUB_PROJECT_KEY} -filekey {file_key} -aihubapikey {AIHUB_API_KEY}"
    # subprocess.run에 check=True를 주어 실패 시 예외가 발생하게 하면, 
    # 데코레이터가 캐치해서 상태를 FAILED로 기록합니다.
    subprocess.run(command, cwd=download_dir, check=True)
    return True
