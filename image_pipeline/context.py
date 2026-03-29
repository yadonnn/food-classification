import multiprocessing as mp
from dataclasses import dataclass

@dataclass
class PipelineContext:
	"""멀티프로세싱 런타임 리소스"""
	worker_id: str | int
	raw_q: mp.Queue = None
	processed_q: mp.Queue = None
	metrics_dict: dict = None
