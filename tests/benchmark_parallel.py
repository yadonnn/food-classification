import sys
import shutil
import zipfile
import cv2
import numpy as np
from pathlib import Path
from typing import Iterator
import zipfile
# 프레임워크 임포트
from benchmark_framework import BenchmarkConfig, ResourceMonitor, BenchmarkRunner

# --- Helper Functions (Stream 전용) ---
def stream_zip_data(zip_path: Path, chunk_size: int = 50) -> Iterator[tuple[str, bytes]]:
	with zipfile.ZipFile(zip_path, 'r') as z:
        # 이미지 파일 이름 인코딩 (cp949, cp437) 순서로 저장
		names = [
            (n.encode('cp437').decode('cp949'), n) for n in z.namelist()
			if n.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
		chunk = []
		for decoded_name, name in names:
		    chunk.append((decoded_name, z.read(name)))
		    if len(chunk) == chunk_size:
			    yield chunk
			    chunk = []
		if chunk:
		    yield chunk

def resize_image_buffer(name: str,
						image_src_bytes: bytes,
						target_size: int,
						interpolation: str,
						extension: str) -> tuple[str, bytes]:
    img_array = np.frombuffer(image_src_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Image decoding error")

    img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_AREA)
    is_success, buffer = cv2.imencode(f".{extension}", img,
                                     [cv2.IMWRITE_WEBP_QUALITY, 85])
    if not is_success:
        raise ValueError("Image encoding error")
    return name, buffer.tobytes()

def process_chunk(chunk: list[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    return [resize_image_buffer(n,b) for n, b in chunk]
# --- Pipeline Functions ---	
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed, wait
import concurrent.futures
def run_pool_benchmark(config: BenchmarkConfig, monitor: ResourceMonitor, chunk_size: int) -> dict:
	output_zip = config.tmp_dir / f"pool_{config.extension}_{config.target_size}_{config.zip_path.name}"
	out_z_context = zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_DEFLATED)

	metrics = {}
	image_count = 0
	# 1. READ (zip → 메모리)
	img_gen = stream_zip_data(config.zip_path, chunk_size)

	with ProcessPoolExecutor(max_workers=4) as executor:
		active_futures = set()
		# 핵심: 큐에 대기시킬 최대 청크 개수 (워커 수의 1.5~2배가 적당)
		MAX_QUEUE_SIZE = 8
		# 1.1 worker process 비동기 전송
		for chunk in img_gen:
			if len(active_futures) >= MAX_QUEUE_SIZE:
				done, active_futures = wait(active_futures,
					return_when=concurrent.futures.FIRST_COMPLETED)
				
				# 2. TRANSFORM (메모리 내 이미지 변환) 
				for future in done:
					try:
						processed_results = future.result()
						for file_name, processed_bytes in processed_results:
							if processed_bytes:
								out_z_context.writestr(file_name, processed_bytes)
								image_count += 1
					except Exception as e:
						print(f"Error processing chunk: {e}")
			
			future_to_chunk = executor.submit(process_chunk, chunk)
			active_futures.add(future_to_chunk)
				
		metrics["total_images_processed"] = image_count
		return metrics

# --- Producer-Consumer ---
import time
def producer(config: BenchmarkConfig, in_queue: mp.Queue, num_consumers: int, chunk_size: int, metrics_dict: dict):
	start_time = time.perf_counter()
	image_count = 0
	chunks = stream_zip_data(config.zip_path, chunk_size=chunk_size)
	for chunk in chunks:
		print("[Producer] in_queue.put(chunk)")
		in_queue.put(chunk)
		image_count += len(chunk)

	for _ in range(num_consumers):
		print("[Producer] in_queue.put(None)")
		in_queue.put(None)
	
	metrics_dict['producer_time'] = time.perf_counter() - start_time
	metrics_dict['raw_image_count'] = image_count

def consumer(worker_id: int, func: callable, config: BenchmarkConfig, in_queue: mp.Queue, out_queue: mp.Queue, metrics_dict: dict):
	start_time = time.perf_counter()
	print(f"[Consumer {worker_id}] waiting...")
	metrics = {}
	image_count = 0
	while True:
		processed_results_stage = []
		chunk = in_queue.get()
		print(f"[Consumer {worker_id}] in_queue.get() : {len(chunk) if chunk is not None else None} images")
		if chunk is None:
			out_queue.put(None)
			print(f"[Consumer] {worker_id} close...")
			break
		processed_results = func(chunk, config.extension, config.interpolation)
		for file_name, processed_bytes in processed_results:
			if processed_bytes:
				processed_results_stage.append((transformed_name, processed_bytes))
				image_count += 1
		
		out_queue.put(processed_results_stage)
		try: print(f"[Consumer {worker_id}] out_queue.put() : {len(processed_results_stage)} images")
		except: print(f"[Consumer {worker_id}] out_queue.put() : None")
	
	metrics_dict[f'consumer_{worker_id}_time'] = time.perf_counter() - start_time

def writer(config: BenchmarkConfig, out_queue: mp.Queue, num_consumers: int, metrics_dict: dict):
	start_time = time.perf_counter()
	print("[Writer] 기록 준비 완료")
	finished_consumers = 0
	processed_image_count = 0
	output_zip = config.tmp_dir / f"{config.interpolation}_{config.extension}_{config.target_size}_{config.zip_path.name}"

	with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_STORED) as out_z:
		while True:
			processed_results = out_queue.get()

			if processed_results is None:
				finished_consumers += 1
				if finished_consumers == num_consumers:
					print("[Writer] 기록 종료")
					break
				continue
			
			for file_name, processed_bytes in processed_results:
				out_z.writestr(file_name, processed_bytes)
				processed_image_count += 1
			print(f"[Writer] {processed_image_count} images 기록 완료")
	
	metrics_dict['writer_time'] = time.perf_counter() - start_time
	metrics_dict['total_images_processed'] = processed_image_count
	

def run_queue_arch(config: BenchmarkConfig, monitor: ResourceMonitor, chunk_size: int, num_consumers: int) -> dict:
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
	func = process_chunk
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
		rounds=2,
	)

	runner = BenchmarkRunner(config)
	runner.run_strategy("producer_consumer", run_queue_arch, 32, num_consumers=1)
	runner.run_strategy("producer_consumer", run_queue_arch, 32, num_consumers=4)
	runner.run_strategy("producer_consumer", run_queue_arch, 32, num_consumers=8)
	runner.run_strategy("producer_consumer", run_queue_arch, 32, num_consumers=16)
	runner.save_results(version_tag="queue_v0.1")
	
if __name__ == "__main__":
    main()