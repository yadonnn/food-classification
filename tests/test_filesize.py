import cv2
import numpy as np
from pathlib import Path
import multiprocessing as mp
from typing import Literal
def resize_image_buffer(name: str,
						image_src_bytes: bytes,
						extension: Literal["webp", "jpg"],
						interpolation: str="INTER_AREA",
						quality: int=85) -> tuple[str, bytes]:
	"""
	이미지 버퍼를 리사이즈하여 반환
	"""
	
	interpolation_map = {
		"INTER_AREA": cv2.INTER_AREA,
		"INTER_LINEAR": cv2.INTER_LINEAR,
		"INTER_CUBIC": cv2.INTER_CUBIC,
		"INTER_NEAREST": cv2.INTER_NEAREST,
		"INTER_LANCZOS4": cv2.INTER_LANCZOS4,
	}
	interpolation = interpolation_map[str.upper(interpolation)]
	if extension == "webp":
		cv2_flag = cv2.IMWRITE_WEBP_QUALITY
	elif extension == "jpg":
		cv2_flag = cv2.IMWRITE_JPEG_QUALITY
	else:
		raise ValueError("Unsupported extension")
	cv2_quality = [cv2_flag, quality]

	img_array = np.frombuffer(image_src_bytes, dtype=np.uint8)
	img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
	if img is None:
		raise ValueError("Image decoding error")

	img = cv2.resize(img, (384, 384), interpolation=interpolation)
	is_success, buffer = cv2.imencode(f".{extension}", img, cv2_quality)
	if not is_success:
		raise ValueError("Image encoding error")

	new_name = str(Path(name).with_suffix(f".{extension}"))
	return new_name, buffer.tobytes()


def process_chunk_multi(chunk: list[tuple[str, bytes]], extension: str, interpolation: str) -> list[tuple[str, bytes]]:
	return [resize_image_buffer(n,b, extension, interpolation) for n, b in chunk]
from benchmark_parallel import BenchmarkConfig, ResourceMonitor, BenchmarkRunner
from benchmark_parallel import producer, consumer, writer

def run_queue_arch(config: BenchmarkConfig, monitor: ResourceMonitor, chunk_size: int, num_consumers: int, func: callable) -> dict:
	import os
	manager = mp.Manager()
	metrics = manager.dict()

	in_queue = mp.Queue(maxsize=num_consumers * 2)
	out_queue = mp.Queue(maxsize=num_consumers * 2)

	# --- writer process ---
	writer_proc = mp.Process(target=writer, args=(config, out_queue, num_consumers, metrics))
	writer_proc.start()
	monitor.register_process("Writer", writer_proc.pid)
	# --- consumers ---
	consumers = []
	for i in range(num_consumers):
		c_proc = mp.Process(target=consumer, args=(i, func, config, in_queue, out_queue, metrics))
		c_proc.start()
		monitor.register_process(f"Consumer {i}", c_proc.pid)
		consumers.append(c_proc)

	# --- producer process ---
	producer_proc = mp.Process(target=producer, args=(config, in_queue, num_consumers, chunk_size, metrics))
	producer_proc.start()
	monitor.register_process("Producer", producer_proc.pid)

	monitor.mark("pipeline_running")
	# --- join processes ---
	producer_proc.join()
	print("[Producer] 종료")
	for p in consumers:
		p.join()
	print("[Consumer] 종료")

	writer_proc.join()
	print("[Writer] 종료")

	print("[Main] 모든 프로세스가 종료되었습니다.")
	consumer_metrics = {}
	for key, value in metrics.items():
		if 'consumer' in key:
			consumer_metrics[key] = metrics.get(key, 0.00)

	summary_metrics = {
		"producer_time_sec": metrics.get("producer_time", 0.00),
		"writer_time_sec": metrics.get("writer_time", 0.00),
		**consumer_metrics,
		"raw_image_count": metrics.get("raw_image_count", 0),
		"total_images_processed": metrics.get("total_images_processed", 0),
	}
	return summary_metrics



def main():
	import os
	root_dir = Path(__file__).parent
	bench_data_dir = root_dir / "data" / "benchmarks"

	config = BenchmarkConfig(
		zip_path=bench_data_dir / "sample_val_302.zip",
		extract_dst=bench_data_dir / "extracted",
		transform_dst=bench_data_dir / "transformed",
		archive_dst=bench_data_dir / "archive",
		tmp_dir=bench_data_dir / "tmp",
		results_dir=root_dir / "data" / "results",
		extension="webp",
		interpolation="INTER_AREA",
		rounds=1,
	)
	extensions = ["webp", "jpg"]
	interpolations = ["INTER_AREA", "INTER_LINEAR"]
	for extension in extensions:
		for interpolation in interpolations:
			config.extension = extension
			config.interpolation = interpolation
			runner = BenchmarkRunner(config)
			runner.run_strategy("producer_consumer", run_queue_arch, 32, num_consumers=8, func=process_chunk_multi)
			runner.save_results(version_tag=f"queue_v0.1_{extension}_{interpolation}")
	
if __name__ == "__main__":
    main()