import os
import zipfile
from collections import defaultdict
from logger import setup_logger

EXTRACT_DIR = "data/extracted/"

def extract_worker(zip_queue, folder_queue):
    """
    앞 단계(다운로드 워커)에서 생성된 ZIP 파일의 절대경로를 받아
    압축을 풀고 원본 ZIP 코어 파일을 삭제합니다.
    이후 해제된 폴더의 절대경로를 folder_queue에 넣습니다.
    """
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    logger = setup_logger()
    
    while True:
        item = zip_queue.get()
        if item is None:
            logger.info("압축 해제 워커: 종료 신호 수신")
            folder_queue.put(None)
            break
        zip_path, file_key = item
            
        logger.info(f"📦 압축 해제 시작: {zip_path} (filekey: {file_key})")
        
        # 고유 폴더명 설정
        base_name = os.path.basename(zip_path)
        folder_name = os.path.splitext(base_name)[0]
        target_folder = os.path.abspath(os.path.join(EXTRACT_DIR, folder_name))
        os.makedirs(target_folder, exist_ok=True)
        
        class_counts = defaultdict(int)
        extraction_success = False

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                total_count = len(z.infolist())
                logger.info(f"총 {total_count}개의 항목 확인: {zip_path}")

                for info in z.infolist():
                    # 1. 파일명 (한글 처리 포함)
                    try:
                        name = info.filename.encode('cp437').decode('cp949')
                    except Exception as e:
                        name = info.filename
                        logger.warning(f"인코딩 변환 실패 (기본값 사용): {info.filename} - {e}")
                    
                    # '/' 기준으로 분리하여 최상위 폴더명을 클래스명으로 사용
                    name_parts = name.split('/')
                    class_name = name_parts[0]
                    
                    # 2. 폴더 여부 확인
                    if not info.is_dir():
                        class_counts[class_name] += 1
                
                logger.info("클래스 카운팅 완료. 대상 폴더로 압축 해제를 진행합니다.")
                
                # 압축 해제
                z.extractall(target_folder)
                
                # 압축 풀기 전/후 파일 개수 무결성 검증
                actual_files = sum(len(files) for r, d, files in os.walk(target_folder))
                expected_files = sum(1 for info in z.infolist() if not info.is_dir())
                
                if expected_files != actual_files:
                    logger.error(f"❌ 무결성 검증 실패 (압축 해제): 파일 개수 불일치 (예상: {expected_files}, 실제: {actual_files}, filekey: {file_key})")
                else:
                    logger.info(f"✅ 무결성 검증 통과 (압축 해제): 총 {actual_files}개 파일 일치")
                    extraction_success = True

                logger.info(f"✅ '{target_folder}' (으)로 압축 해제 프로세스 완료!")
                logger.info(f"최종 클래스별 이미지/파일 개수: {dict(class_counts)}")

        except zipfile.BadZipFile:
            logger.error(f"❌ 손상된 ZIP 파일입니다: {zip_path}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ 압축 해제 중 오류 발생: {e}", exc_info=True)

        if extraction_success:
            # [중요] 삭제 로직 1: 압축 해제가 완전히 끝나면 원본 ZIP 코어 파일 삭제
            try:
                os.remove(zip_path)
                logger.info(f"🗑️ 원본 ZIP 삭제 완료: {zip_path}")
            except Exception as e:
                logger.error(f"❌ 원본 ZIP 삭제 실패: {e}")
                
            # 해제된 디렉토리 경로를 folder_queue에 넣습니다. (filekey도 함께)
            folder_queue.put((target_folder, file_key))
        else:
            logger.error(f"❌ 압축 해제 실패로 인해 원본을 삭제하지 않습니다: {zip_path}")
