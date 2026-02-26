import functools
import logging
import json
import os
from config import *
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


