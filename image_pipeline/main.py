import config
import dotenv
dotenv.load_dotenv()
import preprocessor
import downloader
import shutil
from config import AIHUB_MANIFEST_CSV_PATH
from pathlib import Path
from logger import pipeline_logger, time_logger

@time_logger
def make_key_map_from_manifest(csv_path: Path = AIHUB_MANIFEST_CSV_PATH
							) -> dict[str, tuple[str, str]]:
	"""download_list.csv를 읽어 key: (name, size) 매핑 테이블 생성"""
	import csv
	key_map = {}
	with open(csv_path, "r", encoding="utf-8") as f:
		reader = csv.DictReader(f, fieldnames=["file_name", "size", "file_key"])
		# skip header
		next(reader)
		for i in reader:
			key_map[i["file_key"]] = (i["file_name"], i["size"])
	return key_map

@time_logger
def run_pipeline(file_key: str, key_map: dict[str, tuple[str, str]]):
	"""파일별 다운로드 -> 압축 해제 -> 변환 -> 적재 -> 정리 루프"""
	config.init_directories()
	file_name, _ = key_map[file_key]

	# 1. 다운로드
	file_path = downloader.download_file(file_key, file_name)

	# 2. 압축 해제 분기(json 파일일 경우, 이동만 하고 종료)
	if "json" in file_name:
		json_file_path = preprocessor.move_file(file_path)
		return
	
	# 2-1. 이미지 파일 압축 해제
	image_path_list = preprocessor.extract_archive(file_path)
	
	# 3. 이미지 변환
	preprocessor.transform_images(file_key, image_path_list)
	
	# 4. 전처리된 이미지 압축파일 로컬 저장
	preprocessor.make_archive(file_name)
	
	# 5. 원본 파일 삭제
	shutil.rmtree(config.DOWNLOAD_DST_DIR) 	# 1. 다운로드 zip 경로
	shutil.rmtree(config.EXTRACT_DST_DIR)  	# 2. 압축 해제 경로
	shutil.rmtree(config.TRANSFORM_DST_DIR) # 3. 전처리된 이미지 경로
	# shutil.rmtree(config.ARCHIVE_DST_DIR) 	# 4. 전처리된 이미지 압축파일 경로(GCS 업로드 후 삭제 예정)

if __name__ == "__main__":
	config.init_directories()
	key_map = make_key_map_from_manifest()
	for file_key in ["49589", "49526"]:
		run_pipeline(file_key, key_map)