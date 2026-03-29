import sys
import shutil
import zipfile
import cv2
import numpy as np
from pathlib import Path
from typing import Iterator

# 프레임워크 임포트
from benchmark_framework import BenchmarkConfig, ResourceMonitor, BenchmarkRunner


def stream_zip_data(zip_path: Path, chunk_size: int = 10) -> Iterator[tuple[str, bytes]]:
    with zipfile.ZipFile(zip_path, 'r') as z:
        img_names = [n for n in z.namelist()
                    if n.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
        chunk = []
        for name in img_names:
            chunk.append((name, z.read(name)))
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

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

def run_chunksize_benchmark(config: BenchmarkConfig, monitor: ResourceMonitor, chunk_size: int) -> dict:
	zip_dst_path = config.tmp_dir / f"chunksize_{chunk_size}_{config.zip_path.name}"
	chunk = stream_zip_data(config.zip_path, chunk_size)
	image_count = 0
	with zipfile.ZipFile(zip_dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:	
		while True:
			try:
				monitor.mark("read")
				current_chunk = next(chunk)
				
				monitor.mark("transform")
				transformed_chunk = []
				for name, data in current_chunk:
					transformed_data = resize_image_buffer(data, config)
					transformed_chunk.append((name, transformed_data))
				
				monitor.mark("write")
				for name, t_data in transformed_chunk:
					z_out.writestr(name, t_data)
					image_count += 1
			except StopIteration:
				break
			
	metrics = monitor.to_summary()
	metrics["total_images_processed"] = image_count
	return metrics		

def main():
	root_dir = Path(__file__).parent
	bench_data_dir = root_dir / "data" / "benchmarks"

	config = BenchmarkConfig(
		zip_path=bench_data_dir / "sample_val_302.zip",
		extract_dst=bench_data_dir / "extracted",
		transform_dst=bench_data_dir / "transformed",
		archive_dst=bench_data_dir / "archive",
		tmp_dir=bench_data_dir / "tmp",
		results_dir=root_dir / "data" / "results",
		rounds=2,
	)

	runner = BenchmarkRunner(config)
	runner.run_strategy("ChunkSize_1", run_chunksize_benchmark, 1)
	runner.run_strategy("ChunkSize_10", run_chunksize_benchmark, 10)
	runner.run_strategy("ChunkSize_100", run_chunksize_benchmark, 100)
	runner.run_strategy("ChunkSize_1000", run_chunksize_benchmark, 1000)
	runner.save_results(version_tag="chunksize_v0.1")
	
if __name__ == "__main__":
    main()