import multiprocessing as mp
from functools import partial
from src.context import PipelineContext
from src.workers import extractor, transformer, loader
from src.utils.timer import StageTimer
from src.pipeline.storage import LocalZipAdapter, GCSAdapter
from src.pipeline.preprocessor import process_chunk
from src.pipeline.stream import extractor_task
from src.utils.monitor import ResourceMonitor

def run_pipeline(task, pipe_conf, monitor: ResourceMonitor):
	"""파일별 다운로드 -> 압축 해제 -> 변환 -> 적재 -> 정리 루프"""
	manager = mp.Manager()
	metrics_dict = manager.dict()
	
	raw_q = mp.Queue(maxsize=pipe_conf.num_consumers * 2)
	processed_q = mp.Queue(maxsize=pipe_conf.num_consumers * 2)

	monitor.start()
	
	# Loader
	if pipe_conf.loader.storage_type == "local":
		dst_path = pipe_conf.loader.local.dst_dir / f"{task['base_name']}.zip"
		dst_adapter = LocalZipAdapter(dst_path)
	elif pipe_conf.loader.storage_type == "gcs":
		dst_adapter = GCSAdapter(
			bucket_name=pipe_conf.loader.gcs.bucket_name,
			prefix=pipe_conf.loader.gcs.upload_src_dir
		)
	else:
		raise ValueError(f"Invalid storage type: {pipe_conf.loader.storage_type}")

	load_ctx = PipelineContext(
		worker_id="loader",
		raw_q=None,
		processed_q=processed_q,
		metrics_dict=metrics_dict
	)
		
	load_proc = mp.Process(
		target=loader,
		args=(load_ctx, dst_adapter, pipe_conf.num_consumers)
	)
	load_proc.start()
	monitor.register_process(f"Writer: {pipe_conf.loader.storage_type}", load_proc.pid)
	# Transformer
	transform_task = partial(process_chunk,
		t_conf = pipe_conf.transform)

	transform_procs = []
	for i in range(pipe_conf.num_consumers):
		transform_ctx = PipelineContext(
			worker_id=f"transformer_{i}",
			raw_q=raw_q,
			processed_q=processed_q,
			metrics_dict=metrics_dict
		)
		transform_proc = mp.Process(
			target=transformer,
			args=(transform_ctx, transform_task)
		)
		transform_proc.start()
		transform_procs.append(transform_proc)
		monitor.register_process(f"Transformer: {i}", transform_proc.pid)

	# Extractor
	extract_task = partial(
		extractor_task,
		file_keys=[task['image_key'], task['label_key']],
		base_name=task['base_name'],
		src_conf=pipe_conf.source,
		chunk_size=pipe_conf.chunk_size
	)
	
	extract_ctx = PipelineContext(
		worker_id="extractor",
		raw_q=raw_q,
		processed_q=None,
		metrics_dict=metrics_dict
	)
	
	extract_proc = mp.Process(
		target=extractor,
		args=(extract_ctx, extract_task, pipe_conf.num_consumers)
	)
	extract_proc.start()
	monitor.register_process(f"Extractor: {pipe_conf.source.source_type}", extract_proc.pid)
	
	monitor.mark("Running")
	
	# Join
	extract_proc.join()
	for p in transform_procs:
		p.join()
	load_proc.join()

	return dict(metrics_dict)