import functools
import logging
import json
import os
from config.default import *

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
                
                # step_monitor를 무결성 체크 데코레이터보다 바깥에 둘 경우
                # result가 (성공여부, expected, actual) 튜플일 수 있으므로 이를 처리함
                is_success = result[0] if isinstance(result, tuple) else result
                
                if is_success:
                    tracker.update(chunk_key, "SUCCESS")
                    pipeline_logger.info(f"✔ [SUCCESS] {chunk_key} 완료")
                else:
                    tracker.update(chunk_key, "FAILED", error="무결성 검증 또는 내부 로직 실패")
                return result
                
            except Exception as e:
                # 에러 발생 시 파일 키는 유지하되 상태를 FAILED로 기록
                pipeline_logger.error(f"❌ [FAILED] {chunk_key} 에러 발생: {str(e)}")
                tracker.update(chunk_key, "FAILED", error=str(e))
                # 다음 청크 진행을 위해 에러를 밖으로 던지지 않고 로그만 남김
                return False
                
        return wrapper
    return decorator

def integrity_checker(action_name):
    """
    함수 실행 결과가 (success_bool, expected_count, actual_count) 튜플일 때
    이를 검증해 무결성을 통과했는지 로깅하는 데코레이터.
    무결성이 실패하면 파이프라인 진행(success)을 False로 만듭니다.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(chunk_key, *args, **kwargs):
            result = func(chunk_key, *args, **kwargs)
            
            # 함수 결과가 (성공여부, 예상치, 실제치) 형태일 때 무결성 검증
            if isinstance(result, tuple) and len(result) == 3:
                success, expected, actual = result
                if not success:
                    return False
                    
                if expected != actual:
                    pipeline_logger.error(f"❌ [무결성 실패 - {action_name}] {chunk_key} 파일 개수 불일치 (예상: {expected}, 실제: {actual})")
                    return False
                else:
                    pipeline_logger.info(f"✅ [무결성 통과 - {action_name}] {chunk_key} 일치 확인 (총 {actual}개)")
                    return True
                    
            # 그 외의 반환값(단순 boolean 등)은 그대로 리턴
            return result
        return wrapper
    return decorator

if __name__ == "__main__":
    tracker = ChunkTracker()
    @step_monitor(tracker)
    def test_func(chunk_key):
        print(f"Processing {chunk_key}")
    test_func("test_chunk")
