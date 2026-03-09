import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
from functools import wraps
from config import LOG_FILE

def setup_pipeline_logger(log_file: Path = LOG_FILE):
    """파이프라인 전역에서 사용할 로거를 세팅하고 반환합니다."""
    logger = logging.getLogger("PipelineLogger")
    
    # 이미 핸들러가 추가되어 있다면 중복 추가 방지
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG) # 전체 최소 레벨 설정

    # 1. 로그 포맷 정의
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 2. 콘솔 출력 핸들러 (INFO 레벨 이상 출력)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 3. 파일 출력 핸들러 (DEBUG 레벨 이상, Rotating 적용)
    # maxBytes=5MB, 최대 3개 파일 유지 (pipeline.log, pipeline.log.1, ...)
    file_handler = RotatingFileHandler(
        filename=log_file, 
        maxBytes=5 * 1024 * 1024, 
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 핸들러 부착
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# 싱글톤처럼 어디서든 import pipeline_logger 로 가져다 쓸 수 있도록 인스턴스화
pipeline_logger = setup_pipeline_logger()

def time_logger(func):
    """실행 시간(elapsed time) 파악을 위한 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        pipeline_logger.info(f"⏳ [{func.__name__}] Stage Start")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            pipeline_logger.info(f"✅ [{func.__name__}] Stage Done ({elapsed:.2f}s)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            pipeline_logger.exception(f"❌ [{func.__name__}] Stage Failed ({elapsed:.2f}s) - ERROR: {e}")
            raise
            
    return wrapper