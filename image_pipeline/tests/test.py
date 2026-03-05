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
	import csv
	import sys
	parent_root = Path(__file__).parent.parent
	csv_path = parent_root / "manifests/download_list.csv"
	data_map = dict()
	
	with open(csv_path, "r") as f:
		reader = csv.DictReader(f, fieldnames=["file_name", "size", "file_key"])
		next(reader) # skip header
		import time
		start_time = time.time()
		for row in reader:
			data_map[row["file_key"]] = {
				"file_name" : row["file_name"],
				"size" : row["size"]
			}
			
		print(sys.getsizeof(data_map))
		end_time = time.time()
		print(f"{end_time - start_time:.3f}")

def test_make_info_key_map() -> dict[str, tuple[str, str]]:
	"""
	aihubshell을 통해 다운로드할 파일 정보 매핑
	--> dict(key: file_key, value: (file_name, size))
	"""
	import re
	import subprocess
	regex = re.compile(r'([^\s│├─└─]+(?:_[A-Za-z0-9]+)*\.zip)\s*\|\s*([0-9]+\s*[A-Z]+)\s*\|\s*([0-9]+)')
	raw_text = subprocess.run(f"aihubshell -mode l -datasetkey {config.AIHUB_PROJECT_KEY}",
		shell=True, capture_output=True, text=True, encoding="utf-8")
	# (name, size, key)
	match_group = regex.findall(raw_text.stdout)
	key_map = {key: (name, size) for name, size, key in match_group}
	return raw_text.stdout
import re
from pathlib import Path

def extract_full_paths(tree_text):
    lines = tree_text.strip().split('\n')
    path_stack = []
    results = []
    
    # 파일 정보 추출용 정규식 (이름 | 용량 | 키)
    file_regex = re.compile(r'([^\s│├─└─]+\.zip)\s*\|\s*([0-9]+\s*[A-Z]+)\s*\|\s*([0-9]+)')

    for line in lines:
        # 1. 현재 줄의 들여쓰기 깊이 계산 (공백 2개 또는 트리 기호를 한 단계로 간주)
        content = line.replace('│', ' ').replace('├─', '  ').replace('└─', '  ').replace(' ', ' ')
        depth = (len(line) - len(line.lstrip(' │├─└─ '))) // 2
        
        # 2. 파일인지 폴더인지 판별
        file_match = file_regex.search(line)
        clean_name = line.strip(' │├─└─ ').split('|')[0].strip()

        if file_match:
            # 파일인 경우: 현재 스택에 있는 폴더들과 결합
            file_name = file_match.group(1)
            full_path = Path(*path_stack[:depth]) / file_name
            file_key = file_match.group(3)
            results.append({
                "full_path": str(full_path),
                "file_key": file_key,
                "size": file_match.group(2)
            })
        else:
            # 폴더인 경우: 스택 업데이트
            if clean_name:
                # 현재 깊이에 맞춰 스택 조정 후 새 폴더 추가
                path_stack = path_stack[:depth]
                path_stack.append(clean_name)
                
    return results

# 실행
# raw_tree_data = """(여기에 트리 텍스트 입력)"""
# extracted_data = extract_full_paths(raw_tree_data)
def matching_download_list(match_group):
	key_list = []
	for i in match_group:
		print(i)
	return key_list
	
if __name__ == "__main__":
	reset_dir()
	info_list =test_extract_archive()
	print(info_list)

	# import sys, time, random
	# match_group = test_make_info_key_map()
	# results = extract_full_paths(match_group)
	# with open("test.txt", "w") as f:
	# 	f.write(match_group)
	# if test_key in file_info:
	# 	print(file_info[test_key])
	# matching_download_list(match_group, test_key)

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