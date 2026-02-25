import functools
import logging
import json
import os
from config.default import *
from datetime import datetime
# ==========================================
# 로깅 기본 설정 추가
# ==========================================
def setup_logger(log_file=LOG_DIR / "pipeline.log"):
    """로깅 설정을 초기화하고 로거 객체를 반환합니다."""
    logger = logging.getLogger("PipelineLogger")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    return logger

# 전역 로거 인스턴스 (모듈 로드 시 1회 생성)
# 데코레이터에서 참조하거나, 필요한 곳에서 직접 임포트하여 사용할 수 있습니다.
pipeline_logger = setup_logger()

def with_logging(func):
    """함수 실행 전후로 로그를 남기는 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pipeline_logger.info(f"⏳ [{func.__name__}] 실행 시작")
        try:
            result = func(*args, **kwargs)
            pipeline_logger.info(f"✅ [{func.__name__}] 실행 완료")
            return result
        except Exception as e:
            pipeline_logger.error(f"❌ [{func.__name__}] 실행 중 에러 발생: {str(e)}")
            raise
    return wrapper
# ==========================================
# 진행상황 기록
# ==========================================
class ChunkTracker:
    def __init__(self, state_file=LOG_DIR / "state.json"):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}

    def update(self, chunk_key, status, error=None):
        self.state[chunk_key] = {
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        # 즉시 파일에 쓰기 (Check-pointing)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def is_done(self, chunk_key):
        return self.state.get(chunk_key, {}).get("status") == "SUCCESS"

def step_monitor(tracker):
    """트래커 인스턴스를 인자로 받는 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(chunk_key, *args, **kwargs):
            # 이미 성공한 청크는 건너뜁니다
            if tracker.is_done(chunk_key):
                pipeline_logger.info(f"⏩ [SKIP] {chunk_key} (이미 완료됨)")
                return True

            try:
                pipeline_logger.info(f"▶ [START] {chunk_key} 처리를 시작합니다.")
                result = func(chunk_key, *args, **kwargs)
                
                if result:
                    tracker.update(chunk_key, "SUCCESS")
                    pipeline_logger.info(f"✔ [SUCCESS] {chunk_key} 완료")
                else:
                    tracker.update(chunk_key, "FAILED", error="내부 로직 실패")
                return result
                
            except Exception as e:
                # 에러 발생 시 파일 키는 유지하되 상태를 FAILED로 기록
                pipeline_logger.error(f"❌ [FAILED] {chunk_key} 에러 발생: {str(e)}")
                tracker.update(chunk_key, "FAILED", error=str(e))
                # 다음 청크 진행을 위해 에러를 밖으로 던지지 않고 로그만 남김
                return False
                
        return wrapper
    return decorator

if __name__ == "__main__":
    tracker = ChunkTracker()
    @step_monitor(tracker)
    def test_func(chunk_key):
        print(f"Processing {chunk_key}")
    test_func("test_chunk")
