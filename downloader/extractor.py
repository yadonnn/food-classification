import os
import zipfile
from collections import defaultdict
from logger import ChunkTracker, step_monitor, pipeline_logger
from config.default import LOG_DIR, DOWNLOAD_DIR, EXTRACT_DIR
import glob

extract_tracker = ChunkTracker(state_file=LOG_DIR / "extract_state.json")

def get_zip_files(directory):
    search_pattern = os.path.join(os.path.abspath(directory), "**", "*.zip")
    return set(glob.glob(search_pattern, recursive=True))

def encode_korean(filename):
    """ZIP 스펙(CP437)때문에 깨진 한글 파일명을 시스템 인코딩(CP949)로 복원합니다."""
    try:
        name = filename.encode('cp437').decode('cp949')
    except Exception:
        name = filename
    return name

@step_monitor(extract_tracker)
def unzip_file(file_key, zip_dir=DOWNLOAD_DIR, extract_dir=EXTRACT_DIR):
    zip_files = get_zip_files(zip_dir)
    target_zip = None
    
    # AIHub 다운로더는 보통 `{file_key}.zip` 형태로 저장함. 
    # 1. file_key와 정확히 일치하거나 파일명에 포함된 경우를 찾음
    for zp in zip_files:
        base_name = os.path.basename(zp)
        if base_name == f"{file_key}.zip" or file_key in base_name:
            target_zip = zp
            break
            
    # 2. 만약 매칭되는 파일이 없다면, 다운로드 폴더 내의 남아있는 zip 파일을 찾습니다.
    # aihubshell이 임의의 이름(예: 원천데이터.zip 등)으로 저장했을 가능성을 대비합니다.
    if not target_zip and zip_files:
        # 가장 최근에 다운로드(수정)된 zip 파일을 선택합니다.
        target_zip = max(zip_files, key=os.path.getmtime)
        pipeline_logger.info(f"💡 이름 규칙이 맞지 않아 가장 최신 ZIP 파일을 선택했습니다: {target_zip}")

    if not target_zip:
        pipeline_logger.warning(f"⚠️ [SKIP] {file_key}에 해당하는 zip 파일을 찾을 수 없습니다.")
        return False

    pipeline_logger.info(f"📦 압축 해제 시작: {target_zip}")
    
    # 2. 고유 폴더명(file_key 기준)으로 타겟 폴더 강제 할당
    target_folder = os.path.join(extract_dir, str(file_key))
    os.makedirs(target_folder, exist_ok=True)
    
    extraction_success = False
    expected_files = 0
    actual_files = 0
    
    try:
        with zipfile.ZipFile(target_zip, 'r') as zip_ref:
            # 1. 기대하는 파일 총 개수 계산 (디렉토리 제외)
            expected_files = sum(
                1 for info in zip_ref.infolist() 
                if not info.is_dir()
            )
            
            for info in zip_ref.infolist():
                decoded_name = encode_korean(info.filename)
                
                target_path = os.path.join(target_folder, decoded_name)
                
                if info.is_dir():
                    os.makedirs(target_path, exist_ok=True)
                    continue
                    
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                with zip_ref.open(info) as source, open(target_path, "wb") as target:
                    target.write(source.read())
                    actual_files += 1

        pipeline_logger.info(f"✅ 압축 해제 완료: {target_folder}")
        extraction_success = True
        
    except Exception as e:
        pipeline_logger.error(f"❌ 압축 해제 중 오류 발생: {e}")
        return False
        
    return extraction_success

