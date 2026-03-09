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
from datetime import datetime
# 경로 설정
# 현재 파일 기준으로 상대 경로 고정
BENCHMARK_DIR = Path(__file__).parent / "data" / "benchmarks"
BENCHMARK_ZIP_PATH     = BENCHMARK_DIR / "sample_val_302.zip"
BENCHMARK_EXTRACT_DST_DIR = BENCHMARK_DIR / "extracted"
BENCHMARK_TRANSFORM_DST_DIR = BENCHMARK_DIR / "transformed"
BENCHMARK_ARCHIVE_DST_DIR = BENCHMARK_DIR / "archive"
BENCHMARK_TMP_DIR = BENCHMARK_DIR / "tmp"
BENCHMARK_OUTPUT_JSON = Path(__file__).parent / "results" / f"benchmark_output_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
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
