import logging

def setup_logger(log_file="extraction.log"):
    """로깅 설정을 초기화하고 로거 객체를 반환합니다."""
    # 로거 생성
    logger = logging.getLogger("ExtractorLogger")
    
    # 이미 핸들러가 설정되어 있다면 중복 추가 방지
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 로그 포맷 설정
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 파일 핸들러 (파일에 로그 기록)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 스트림 핸들러 (콘솔에 로그 출력)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        
    return logger
