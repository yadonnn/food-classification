"""
인메모리 스트리밍 방식

OpenCV 기반 이미지 변환 로직
압축 관련 로직
파일 이동 로직
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "image_pipeline"))
import argparse
import csv
import config
import preprocessor
import zipfile
import shutil
import itertools
import subprocess
import time
import json
import benchmark_pipeline
import cv2
import numpy as np
from datetime import datetime
from typing import Iterator
# 경로 설정
# 현재 파일 기준으로 상대 경로 고정
BENCHMARK_DIR = Path(__file__).parent / "data" / "benchmarks"
BENCHMARK_ZIP_PATH     = BENCHMARK_DIR / "sample_val_302.zip"
BENCHMARK_EXTRACT_DST_DIR = BENCHMARK_DIR / "extracted"
BENCHMARK_TRANSFORM_DST_DIR = BENCHMARK_DIR / "transformed"
BENCHMARK_ARCHIVE_DST_DIR = BENCHMARK_DIR / "archive"
BENCHMARK_TMP_DIR = BENCHMARK_DIR / "tmp"
BENCHMARK_OUTPUT_JSON = Path(__file__).parent / "results" / f"benchmark_output_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
BENCHMARK_OUTPUT_DIR = Path(__file__).parent / "data" / "results"
# 이미지 설정
BENCHMARK_TARGET_SIZE = 384
BENCHMARK_EXTENSION = "webp"
BENCHMARK_QUALITY = 90

image_list = list(BENCHMARK_EXTRACT_DST_DIR.rglob("*.jpg"))

def setup():
	"""pedantic setup 함수"""
	shutil.rmtree(BENCHMARK_TMP_DIR, ignore_errors=True)
	BENCHMARK_TMP_DIR.mkdir(parents=True, exist_ok=True)

def test_extract_archive(benchmark):
	benchmark.pedantic(
		preprocessor.extract_archive,
		args=(BENCHMARK_ZIP_PATH, BENCHMARK_TMP_DIR),
		setup=setup,
		rounds=3,
		warmup_rounds=1
	)

def test_transform_images(benchmark):
	benchmark.pedantic(
		transform_images,
		args=("sample", image_list),
		setup=setup,
		rounds=3,
		warmup_rounds=1
	)

def test_make_archive(benchmark):
	benchmark.pedantic(
		preprocessor.make_archive,
		args=("sample.zip",
			  BENCHMARK_TRANSFORM_DST_DIR,
			  BENCHMARK_TMP_DIR,
			  BENCHMARK_TARGET_SIZE,
			  BENCHMARK_EXTENSION),
		setup=setup,
		rounds=3,
		warmup_rounds=1
	)

def transform_images(file_key: str,
					image_path_list: list,
                 	src_root: Path = BENCHMARK_EXTRACT_DST_DIR,
                 	dst_root: Path = BENCHMARK_TRANSFORM_DST_DIR,
                 	target_size: int = BENCHMARK_TARGET_SIZE,
                 	extension: str = BENCHMARK_EXTENSION,
                 	quality: int = BENCHMARK_QUALITY):
	for image_path in image_path_list:
		preprocessor.resize_image(image_path,
								src_root,
								dst_root,
								target_size,
								extension,
								quality)

def stream_zip_data(zip_path: Path = BENCHMARK_ZIP_PATH) -> Iterator[tuple[str, bytes]]:
	with zipfile.ZipFile(zip_path, 'r') as z:
		img_names = [n for n in z.namelist() \
					if n.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))
					]

		for name in img_names:
			yield name, z.read(name)

def resize_image(image_src_bytes: bytes,
                 target_size: int = BENCHMARK_TARGET_SIZE,
                 extension: str = BENCHMARK_EXTENSION,
                 quality: int = BENCHMARK_QUALITY) -> bytes:
	img_array = np.frombuffer(image_src_bytes, dtype=np.uint8)
	img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

	if img is None:
		raise ValueError(f"Image not found at {image_src_path}")

	img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_AREA)
	is_success, buffer = cv2.imencode(f".{extension}", img, [cv2.IMWRITE_WEBP_QUALITY, quality])
    
	if not is_success:
		raise ValueError(f"Image encoding error")
	
	return buffer.tobytes()

# ====================================================
# --- 압축 함수 ---
# ====================================================
def make_archive(data_info: tuple,
				file_name: str,
				dst_root: Path = BENCHMARK_TMP_DIR,
				target_size: int = BENCHMARK_TARGET_SIZE,
				extension: str = BENCHMARK_EXTENSION) -> Path:
	"""디렉토리를 zip으로 압축하고, ZipInfo 리스트 반환"""
	img_name, processed_bytes = data_info
	zip_dst_path = dst_root / f"{extension}_{str(target_size)}_{file_name}"
	with zipfile.ZipFile(zip_dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
		z.writestr(img_name, processed_bytes)
	
	return zip_dst_path

def move_file(src_path: Path,
              dst_root: Path = BENCHMARK_ARCHIVE_DST_DIR) -> Path:
    """src_path를 dst_root로 이동하고 이동한 파일 경로 반환"""
    dst_path = dst_root / src_path.name
    src_path.replace(dst_path)
    return dst_path
def run_stream_pipeline_v3_with_metrics():
    file_name = BENCHMARK_ZIP_PATH.name
    zip_dst_path = BENCHMARK_TMP_DIR / f"{BENCHMARK_EXTENSION}_{str(BENCHMARK_TARGET_SIZE)}_{file_name}"
    
    # 시간 누적용 딕셔너리
    metrics = {
        "total_read_time_sec": 0.0,
        "total_transform_time_sec": 0.0,
        "total_write_time_sec": 0.0,
        "total_images_processed": 0
    }

    with zipfile.ZipFile(zip_dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
        
        # 제너레이터를 수동으로 제어하기 위해 iter()로 감쌉니다.
        stream_iterator = iter(stream_zip_data(BENCHMARK_ZIP_PATH))
        
        while True:
            # ------------------------------------------------
            # 1. READ 시간 측정 (제너레이터에서 데이터 뽑기)
            # ------------------------------------------------
            t0 = time.perf_counter()
            try:
                image_name, image_bytes = next(stream_iterator)
            except StopIteration:
                break # 더 이상 데이터가 없으면 루프 종료
            
            t1 = time.perf_counter()
            metrics["total_read_time_sec"] += (t1 - t0)

            # ------------------------------------------------
            # 2. TRANSFORM 시간 측정 (리사이즈 및 인코딩)
            # ------------------------------------------------
            resized_bytes = resize_image(image_bytes)
            
            t2 = time.perf_counter()
            metrics["total_transform_time_sec"] += (t2 - t1)

            # ------------------------------------------------
            # 3. WRITE 시간 측정 (ZIP 파일에 쓰기)
            # ------------------------------------------------
            new_image_name = Path(image_name).with_suffix(f'.{BENCHMARK_EXTENSION}').name
            z_out.writestr(new_image_name, resized_bytes)
            
            t3 = time.perf_counter()
            metrics["total_write_time_sec"] += (t3 - t2)
            
            metrics["total_images_processed"] += 1

    # 전체 소요 시간 계산
    total_pipeline_time = (
        metrics["total_read_time_sec"] + 
        metrics["total_transform_time_sec"] + 
        metrics["total_write_time_sec"]
    )
    metrics["total_pipeline_time_sec"] = total_pipeline_time

    # 결과를 JSON 파일로 저장 (작성해두신 변수 활용)
    with open(BENCHMARK_OUTPUT_DIR / f"v0.2_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
        
    print(f"✅ 벤치마크 완료! 결과가 저장되었습니다.")

def run_stream_pipeline_v2_with_metrics():
	# 디렉토리 초기화
	shutil.rmtree(BENCHMARK_EXTRACT_DST_DIR)  	# 2. 압축 해제 경로
	shutil.rmtree(BENCHMARK_TRANSFORM_DST_DIR) # 3. 전처리된 이미지 경로
	BENCHMARK_EXTRACT_DST_DIR.mkdir(parents=True, exist_ok=True)
	BENCHMARK_TRANSFORM_DST_DIR.mkdir(parents=True, exist_ok=True)
	
	# 시간 누적용 딕셔너리
	metrics = {
		"total_read_time_sec": 0.0,
		"total_transform_time_sec": 0.0,
		"total_write_time_sec": 0.0,
		"total_images_processed": 0
	}
	
	# ------------------------------------------------
	# 1. READ 시간 측정 (제너레이터에서 데이터 뽑기)
	# ------------------------------------------------
	t0 = time.perf_counter()
	image_path_list = preprocessor.extract_archive(BENCHMARK_ZIP_PATH, BENCHMARK_EXTRACT_DST_DIR)
	t1 = time.perf_counter()
	metrics["total_read_time_sec"] += (t1 - t0)

	# ------------------------------------------------
	# 2. TRANSFORM 시간 측정 (리사이즈 및 인코딩)
	# ------------------------------------------------
	benchmark_pipeline.transform_images(file_key="sample",
					image_path_list= image_path_list,
                 	src_root= BENCHMARK_EXTRACT_DST_DIR,
                 	dst_root= BENCHMARK_TRANSFORM_DST_DIR,
                 	target_size= BENCHMARK_TARGET_SIZE,
                 	extension= BENCHMARK_EXTENSION,
                 	quality= BENCHMARK_QUALITY)
	t2 = time.perf_counter()
	metrics["total_transform_time_sec"] += (t2 - t1)

	# ------------------------------------------------
	# 3. WRITE 시간 측정 (ZIP 파일에 쓰기)
	# ------------------------------------------------
	preprocessor.make_archive("sample.zip",
			  BENCHMARK_TRANSFORM_DST_DIR,
			  BENCHMARK_TMP_DIR,
			  BENCHMARK_TARGET_SIZE,
			  BENCHMARK_EXTENSION)
	t3 = time.perf_counter()
	metrics["total_write_time_sec"] += (t3 - t2)

	metrics["total_images_processed"] += 1

    # 전체 소요 시간 계산
	total_pipeline_time = (
		metrics["total_read_time_sec"] + 
		metrics["total_transform_time_sec"] + 
		metrics["total_write_time_sec"]
	)
	metrics["total_pipeline_time_sec"] = total_pipeline_time

	# 결과를 JSON 파일로 저장 (작성해두신 변수 활용)
	with open(BENCHMARK_OUTPUT_DIR / f"v0.3_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 'w', encoding='utf-8') as f:
		json.dump(metrics, f, indent=4, ensure_ascii=False)
		
	print(f"✅ 벤치마크 완료! 결과가 저장되었습니다.")	
if __name__ == "__main__":
	import gc
	for i in range(2):
		gc.disable()
		run_stream_pipeline_v2_with_metrics()
		gc.enable()
		gc.disable()
		run_stream_pipeline_v3_with_metrics()
		gc.enable()
	# zip_path = Path("/home/lys/my-project/food-classification/tests/data/benchmarks/tmp/webp_384_sample_val_302.zip")
	# with zipfile.ZipFile(zip_path, 'r') as z:
	# 	for info in z.infolist():
			# print(info.filename)
