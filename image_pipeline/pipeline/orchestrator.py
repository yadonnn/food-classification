import multiprocessing as mp
from context import PipelineContext
from functools import partial
from pipeline.workers import extractor, transformer, loader
from pipeline.utils.timer import StageTimer
from pipeline.adapters.storage import LocalZipAdapter, GCSAdapter
from pipeline.domain.preprocessor import process_chunk
from pipeline.adapters.stream import extractor_task

def run_pipeline(task, pipe_conf, sys_conf):
	"""파일별 다운로드 -> 압축 해제 -> 변환 -> 적재 -> 정리 루프"""
	manager = mp.Manager()
	metrics_dict = manager.dict()
	
	raw_q = mp.Queue(maxsize=pipe_conf.num_consumers * 2)
	processed_q = mp.Queue(maxsize=pipe_conf.num_consumers * 2)

	
	# Loader
	if pipe_conf.loader.storage_type == "local":
		dst_path = sys_conf.archive_dst / f"{task['base_name']}.zip"
		dst_adapter = LocalZipAdapter(dst_path)
	elif pipe_conf.loader.storage_type == "gcs":
		dst_adapter = GCSZipAdapter(
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

	# Transformer
	transform_task = partial(process_chunk,
		t_conf = pipe_conf.transform_conf)

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

	# Extractor
	extract_task = partial(
		extractor_task,
		file_keys=[task['image_key'], task['label_key']],
		base_name=task['base_name'],
		pipe_conf=pipe_conf,
		sys_conf=sys_conf
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
	
	# Join
	extract_proc.join()
	for p in transform_procs:
		p.join()
	load_proc.join()

	return dict(metrics_dict)