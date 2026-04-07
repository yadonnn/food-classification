from contextlib import contextmanager
from collections import defaultdict
import time

class StageTimer:
	def __init__(self):
		self.stats = defaultdict(float)
	
	@contextmanager
	def record(self, name):
		start = time.perf_counter()
		try:
			yield
		finally:
			elapsed = time.perf_counter() - start
			self.stats[name] += elapsed
	
	def get_summary(self):
		return self.stats