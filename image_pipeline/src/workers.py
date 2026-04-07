from dataclasses import dataclass
from contextlib import contextmanager
from collections import defaultdict
from typing import Iterable, Callable
import multiprocessing as mp
import time
from src.context import PipelineContext
from src.utils.timer import StageTimer
	
# --- Producer-Consumer ---
def extractor(ctx: PipelineContext,
			stream_fn: Callable[[], Iterable],
			num_consumers: int
			) -> None:
	timer = StageTimer()
	image_count = 0
	with timer.record("extractor"):
		stream = stream_fn()
		for chunk in stream:
			print("[Producer] in_queue.put(chunk)")
			ctx.raw_q.put(chunk)
			image_count += len(chunk)

	for _ in range(num_consumers):
		print("[Producer] in_queue.put(None)")
		ctx.raw_q.put(None)
	
	ctx.metrics_dict['producer_time'] = timer.get_summary()
	ctx.metrics_dict['raw_image_count'] = image_count

def transformer(ctx: PipelineContext, func: callable) -> None:
	timer = StageTimer()
	print(f"[Consumer {ctx.worker_id}] waiting...")
	
	with timer.record("consumer"):
		while True:
			chunk = ctx.raw_q.get()
			print(f"[Consumer {ctx.worker_id}] in_queue.get() : {len(chunk) if chunk is not None else None} images")
			
			# Sentinel Value
			if chunk is None:
				ctx.processed_q.put(None)
				print(f"[Consumer] {ctx.worker_id} close...")
				break
			
			# Transform
			with timer.record("pure_transform"):
				processed_results = func(chunk)

			# Put processed results to out_queue
			if processed_results:
				ctx.processed_q.put(processed_results)
				print(f"[Consumer {ctx.worker_id}] out_queue.put() : {len(processed_results)} images")
	
	ctx.metrics_dict[f'consumer_{ctx.worker_id}_time'] = timer.get_summary()

def loader(ctx: PipelineContext, dst_adapter, num_consumers: int) -> None:
	timer = StageTimer()
	print("[Writer] 기록 준비 완료")
	finished_consumers = 0
	total_processed = 0

	with timer.record("loader"):
		with dst_adapter as writer:
			while True:
				# Get processed results from out_queue
				processed_results = ctx.processed_q.get()

				# Sentinel Value
				if processed_results is None:
					finished_consumers += 1
					if finished_consumers == num_consumers:
						print("[Writer] 기록 종료")
						break
					continue
				
				# Write processed results to dst_adapter
				for processed_result in processed_results:
					count = writer.write(processed_result)
					total_processed += count
			
			print(f"[Writer] {total_processed} images 기록 완료")
	
	ctx.metrics_dict['writer_time'] = timer.get_summary()
	ctx.metrics_dict['total_processed'] = total_processed