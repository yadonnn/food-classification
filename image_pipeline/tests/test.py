# tests/test_extract.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config
import preprocessor as preprocessor
import downloader as downloader
import shutil
import cv2
# 현재 파일 기준으로 상대 경로 고정
FIXTURE_DIR = Path(__file__).parent / "fixtures"
TEST_ZIP     = FIXTURE_DIR / "sample.zip"
TEST_EXTRACT_DST_DIR = FIXTURE_DIR / "output" / "extracted"
TEST_EXTRACT_DST_DIR.mkdir(parents=True, exist_ok=True)
TEST_TRANSFORM_DST_DIR = FIXTURE_DIR / "output" / "transformed"
TEST_TRANSFORM_DST_DIR.mkdir(parents=True, exist_ok=True)
TEST_ARCHIVE_DST_DIR = FIXTURE_DIR / "output" / "archive"
TEST_ARCHIVE_DST_DIR.mkdir(parents=True, exist_ok=True)

def reset_dir():
	shutil.rmtree(TEST_EXTRACT_DST_DIR)
	shutil.rmtree(TEST_TRANSFORM_DST_DIR)
	shutil.rmtree(TEST_ARCHIVE_DST_DIR)
	TEST_EXTRACT_DST_DIR.mkdir(parents=True, exist_ok=True)
	TEST_TRANSFORM_DST_DIR.mkdir(parents=True, exist_ok=True)
	TEST_ARCHIVE_DST_DIR.mkdir(parents=True, exist_ok=True)


def test_extract_archive():
	info_list = preprocessor.extract_archive(TEST_ZIP, TEST_EXTRACT_DST_DIR)
	return info_list

def test_resize_image(info_list):
	transformed_img_paths = []
	for info in info_list:
		# print(TEST_DST_DIR / info.filename)
		transformed_img_path = preprocessor.resize_image(TEST_EXTRACT_DST_DIR / info.filename,
			src_root=TEST_EXTRACT_DST_DIR,
			dst_root=TEST_TRANSFORM_DST_DIR,
			target_size=config.TARGET_SIZE,
			extension=config.TRANSFORM_EXTENSION,
			quality=90)
		transformed_img_paths.append(transformed_img_path)
	return transformed_img_paths

def test_make_archive():
	info_list = preprocessor.make_archive(TEST_TRANSFORM_DST_DIR, TEST_ARCHIVE_DST_DIR)
	return info_list

def test_get_download_file_info():
	import re, subprocess
	a = subprocess.run(f"aihubshell -mode l -datasetkey {config.AIHUB_PROJECT_KEY}",
					shell=True, check=True, text=True, capture_output=True)
	print(a.stdout.split("\n"))
	pattern = re.compile(r"\s*\([a-zㄱ-힣]+\)\s*\|\s*\([0-9]+ [KB|MB|GB]\)\s*\|\s*\([0-9]+\)\s*$")
	match = pattern.match(a.stdout)
	if match:
		filename, size, count = match.groups()
		print(filename)

if __name__ == "__main__":
	test_get_download_file_info()
# 	reset_dir()
# 	info_list = test_extract_archive()
# 	print(info_list)
# 	print("="*100)
# 	transformed_img_paths = test_resize_image(info_list)
# 	print(transformed_img_paths)
# 	print(config.TARGET_SIZE)
# 	img = cv2.imread("/home/lys/my-project/food-classification/image_pipeline/tests/fixtures/output/볶음밥/B010443XX_00365.jpg")
# 	print(img.shape)
# 	info_list = test_make_archive()
# 	print("*"*30)
# 	print(len(info_list))