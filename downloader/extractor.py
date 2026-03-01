import os
import zipfile
from pathlib import Path
from utils.logger import with_logging, pipeline_logger
from config import LOG_DIR, DOWNLOAD_DIR, EXTRACT_DIR, BASE_DIR
import glob

def get_zip_files(directory: Path) -> set:
    """지정된 디렉토리에서 모든 zip 파일을 찾습니다."""
    search_pattern = os.path.join(os.path.abspath(directory), "**", "*.zip")
    return set(glob.glob(search_pattern, recursive=True))

def encode_korean(filename: str) -> str:
    """ZIP 스펙(CP437)때문에 깨진 한글 파일명을 시스템 인코딩(CP949)로 복원합니다."""
    try:
        name = filename.encode('cp437').decode('cp949')
    except Exception:
        name = filename
    return name

@with_logging
def unzip_file(file_path: Path, extract_dir: Path=EXTRACT_DIR) -> bool:
    """지정된 zip 파일을 한글 깨짐 현상 복원 후 압축 해제합니다."""
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            # 1. 파일명 복원
            original_name = member.filename
            fixed_name = encode_korean(original_name)
            
            # 2. 디렉토리인 경우 경로 설정
            target_path = extract_dir / fixed_name
            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue

            # 3. 파일 추출
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'wb') as f:
                f.write(zip_ref.read(member))
    return True

if __name__ == "__main__":
    test_zip_path = BASE_DIR / "tests" / "test_data" / "src" / "test.zip"
    test_extract_dir = BASE_DIR / "tests" / "test_data" / "extracted"
    print(test_zip_path)
    print(test_extract_dir)
    if test_zip_path.exists():
        print(f"🚀 테스트 실행: {test_zip_path.name} 압축 해제 중...")
        unzip_file(test_zip_path, test_extract_dir)
    else:
        print("❌ 테스트할 ZIP 파일이 없습니다.")