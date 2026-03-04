import config
import dotenv
dotenv.load_dotenv()
import preprocessor
import downloader

def run_pipeline(file_key: str, is_test: bool = False):
	"""파일별 다운로드 -> 압축 해제 -> 변환 -> 적재 -> 정리 루프"""
	config.init_directories()
	if is_test == False:
		# 1. 다운로드
		downloader.download_file(file_key)
		# 2. 압축 해제
		info_list = downloader.extract_archive()
		# 3. 이미지 변환
		for info in info_list:
			preprocessor.resize_image(info.filename)
		# 4. 전처리된 이미지 압축파일 로컬 저장
		preprocessor.make_archive()
		# 5. 원본 파일 삭제
		# shutil.rmtree(config.DOWNLOAD_DST_DIR) 	# 1. 다운로드 zip 경로
		# shutil.rmtree(config.EXTRACT_DST_DIR)  	# 2. 압축 해제 경로
		# shutil.rmtree(config.TRANSFORM_DST_DIR) # 3. 전처리된 이미지 경로
		# shutil.rmtree(config.ARCHIVE_DST_DIR) 	# 4. 전처리된 이미지 압축파일 경로(GCS 업로드 후 삭제 예정)
	else:
		print("test mode")
		
		# 2. 압축 해제
		info_list = downloader.extract_archive()
		# 3. 이미지 변환
		for info in info_list:
			preprocessor.resize_image(info.filename)
		# 4. 전처리된 이미지 압축파일 로컬 저장
		preprocessor.make_archive()
if __name__ == "__main__":
	for file_key in config.AIHUB_FILE_KEYS:
		run_pipeline(file_key, is_test=True)