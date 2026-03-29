<<<<<<< HEAD
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
=======
import sys
import shutil
import zipfile
>>>>>>> 970d5df (feat: apply multiprocessing and configuration & update roadmap)
import cv2
import numpy as np
from pathlib import Path
from typing import Iterator
<<<<<<< HEAD
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
=======

# 프레임워크 임포트
from benchmark_framework import BenchmarkConfig, ResourceMonitor, BenchmarkRunner
>>>>>>> 970d5df (feat: apply multiprocessing and configuration & update roadmap)

# 기존 모듈 임포트 경로 설정
sys.path.append(str(Path(__file__).parent.parent / "image_pipeline"))
import preprocessor
import benchmark_pipeline


# --- Helper Functions (Stream 전용) ---
def stream_zip_data(zip_path: Path) -> Iterator[tuple[str, bytes]]:
    with zipfile.ZipFile(zip_path, 'r') as z:
        img_names = [n for n in z.namelist()
                    if n.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
        for name in img_names:
            yield name, z.read(name)

def resize_image_buffer(image_src_bytes: bytes, config: BenchmarkConfig) -> bytes:
    img_array = np.frombuffer(image_src_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Image decoding error")

    img = cv2.resize(img, (config.target_size, config.target_size), interpolation=cv2.INTER_AREA)
    is_success, buffer = cv2.imencode(f".{config.extension}", img,
                                     [cv2.IMWRITE_WEBP_QUALITY, config.quality])
    if not is_success:
        raise ValueError("Image encoding error")
    return buffer.tobytes()


# --- Pipeline Functions ---

def run_disk_pipeline(config: BenchmarkConfig, monitor: ResourceMonitor) -> dict:
    """v2: 디스크 기반 파이프라인 (압축해제 -> 변환 -> 압축)"""

    # 0. 초기화
    shutil.rmtree(config.extract_dst, ignore_errors=True)
    shutil.rmtree(config.transform_dst, ignore_errors=True)
    config.extract_dst.mkdir(parents=True, exist_ok=True)
    config.transform_dst.mkdir(parents=True, exist_ok=True)

    # 1. READ (압축 해제)
    monitor.mark("read")
    image_path_list = preprocessor.extract_archive(config.zip_path, config.extract_dst)

    # 2. TRANSFORM (이미지 변환)
    monitor.mark("transform")
    benchmark_pipeline.transform_images(
        file_key="sample",
        image_path_list=image_path_list,
        src_root=config.extract_dst,
        dst_root=config.transform_dst,
        target_size=config.target_size,
        extension=config.extension,
        quality=config.quality
    )

    # 3. WRITE (재압축)
    monitor.mark("write")
    preprocessor.make_archive(
        "sample.zip",
        config.transform_dst,
        config.tmp_dir,
        config.target_size,
        config.extension
    )

    metrics = monitor.to_summary()
    metrics["total_images_processed"] = len(image_path_list)
    return metrics


def run_stream_pipeline(config: BenchmarkConfig, monitor: ResourceMonitor) -> dict:
    """v3: 메모리 스트리밍 기반 파이프라인 (In-memory)"""
    image_count = 0

    zip_dst_path = config.tmp_dir / f"stream_{config.extension}_{config.target_size}_{config.zip_path.name}"

    # 1. READ (zip → 메모리)
    monitor.mark("read")
    image_data = list(stream_zip_data(config.zip_path))

    # 2. TRANSFORM (메모리 내 이미지 변환)
    monitor.mark("transform")
    transformed = []
    for image_name, image_bytes in image_data:
        resized_bytes = resize_image_buffer(image_bytes, config)
        new_name = Path(image_name).with_suffix(f'.{config.extension}').name
        transformed.append((new_name, resized_bytes))

    # 3. WRITE (메모리 → zip)
    monitor.mark("write")
    with zipfile.ZipFile(zip_dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
        for name, data in transformed:
            z_out.writestr(name, data)
            image_count += 1

    metrics = monitor.to_summary()
    metrics["total_images_processed"] = image_count
    return metrics


if __name__ == "__main__":
<<<<<<< HEAD
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
=======
    root_dir = Path(__file__).parent
    bench_data_dir = root_dir / "data" / "benchmarks"

    config = BenchmarkConfig(
        zip_path=bench_data_dir / "sample_val_302.zip",
        extract_dst=bench_data_dir / "extracted",
        transform_dst=bench_data_dir / "transformed",
        archive_dst=bench_data_dir / "archive",
        tmp_dir=bench_data_dir / "tmp",
        results_dir=root_dir / "data" / "results",
        rounds=2
    )

    runner = BenchmarkRunner(config)

    runner.run_strategy("Disk_v2", run_disk_pipeline)
    runner.run_strategy("Stream_v3", run_stream_pipeline)

    runner.save_results(version_tag="unified_v0.2")
>>>>>>> 970d5df (feat: apply multiprocessing and configuration & update roadmap)
