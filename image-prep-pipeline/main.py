import config
import subprocess
import zipfile
import cv2
import dotenv
import os
import glob
from pathlib import Path
import time
import shutil

dotenv.load_dotenv()

def get_zip_files(directory: Path) -> set:
	"""지정된 디렉토리에서 모든 zip 파일을 찾습니다."""
	search_pattern = os.path.join(os.path.abspath(directory), "**", "*.zip")
	return set(glob.glob(search_pattern, recursive=True))


def main():
	# 파일별 다운로드 -> 압축 해제 -> 변환 -> 적재 -> 정리 루프
	for file_key in config.AIHUB_FILE_KEYS:
		# 폴더 생성
		config.init_directories()
		# 1. aihub 다운로드
		command = f"aihubshell -mode d -datasetkey {config.AIHUB_PROJECT_KEY} -filekey {file_key} -aihubapikey {config.AIHUB_API_KEY}"
		subprocess.run(command, cwd=config.DOWNLOAD_DST_DIR, shell=True, check=True)

		# 2. 압축 해제
		print(get_zip_files(config.DOWNLOAD_DST_DIR))
		file_paths = get_zip_files(config.DOWNLOAD_DST_DIR)
		image_paths = list()
		for file_path in file_paths:
			with zipfile.ZipFile(file_path, 'r') as z:
				# 이미지 파일 경로 수집
				for member in z.infolist():
					original_name = member.filename
					encoded_name = original_name.encode('cp437').decode('cp949')
					print(encoded_name)

					target_path = config.EXTRACT_DST_DIR / encoded_name
					if member.is_dir():
						target_path.mkdir(parents=True, exist_ok=True)
						continue

					if target_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
						image_paths.append(target_path)
				# 압축 해제
					with open(target_path, 'wb') as f:
						f.write(z.read(member))

		# 3. 이미지 변환
		for image_path in image_paths:
			img = cv2.imread(image_path)
			print(f"이미지 처리중 {image_path}")
			print(img.shape)
			img = cv2.resize(img, (config.TARGET_SIZE, config.TARGET_SIZE))

			relative_path = image_path.relative_to(config.EXTRACT_DST_DIR)
			save_path = config.TRANSFORM_DST_DIR / relative_path.with_suffix(f".{config.TRANSFORM_EXTENSION}")
			save_path.parent.mkdir(parents=True, exist_ok=True)
			print(f"save_path: {save_path}")
			cv2.imwrite(save_path, img, [cv2.IMWRITE_WEBP_QUALITY, 90])

		# 4. 전처리된 이미지 압축파일 로컬 저장
		shutil.make_archive(config.ARCHIVE_DST_DIR / file_key, 'zip', config.ARCHIVE_SRC_DIR)

		# 5. 원본 파일 삭제
		shutil.rmtree(config.DOWNLOAD_DST_DIR) 	# 1. 다운로드 zip 경로
		shutil.rmtree(config.EXTRACT_DST_DIR)  	# 2. 압축 해제 경로
		shutil.rmtree(config.TRANSFORM_DST_DIR) # 3. 전처리된 이미지 경로
		# shutil.rmtree(config.ARCHIVE_DST_DIR) 	# 4. 전처리된 이미지 압축파일 경로(GCS 업로드 후 삭제 예정)

if __name__ == "__main__":
	main()