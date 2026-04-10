import os
import time
import threading
import psutil
from pathlib import Path
from typing import Optional

class ResourceMonitor:
    """백그라운드 스레드로 CPU/메모리를 폴링하고, mark()로 stage 구간을 기록"""

    def __init__(self, interval: float = 0.1):
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        # Target processes {name: psutil.Process}
        self._targets: dict[str, psutil.Process] = {}

        # Time series data
        self._samples: list[dict] = []  # {"t": float, "cpu": {이름: %}, "mem_mb": {이름: MB}}
        self._events: list[tuple[str, float]] = []             # (stage명, 시작시간)
        self._base_time: float = 0.0

    def register_process(self, name: str, pid: int):
        """감시할 자식 프로세스를 이름표와 함께 등록합니다."""
        try:
            proc = psutil.Process(pid)
            proc.cpu_percent(interval=None) # CPU 측정을 위한 영점(Baseline) 세팅
            self._targets[name] = proc
            print(f"[Monitor] '{name}' (PID: {pid}) registered.")
        except psutil.NoSuchProcess:
            print(f"[Monitor] Error: PID {pid} ({name}) not found.")

    def start(self):
        """폴링 스레드 시작"""
        self._samples.clear()
        self._events.clear()
        self._stop_event.clear()

        # Register main process
        if "Main" not in self._targets:
            self.register_process("Main", os.getpid())

        self._base_time = time.perf_counter()
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self):
        """폴링 스레드 종료 대기"""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def mark(self, stage_name: str):
        """현재 시간을 stage 시작점으로 기록"""
        elapsed = time.perf_counter() - self._base_time
        self._events.append((stage_name, elapsed))

    def _poll(self):
        """스레드 내부 루프: interval마다 CPU/메모리 샘플링"""
        while not self._stop_event.is_set():
            elapsed = time.perf_counter() - self._base_time

            current_cpu = {}
            current_mem = {}

            # Runtime 중 targets 변경 대비 list()로 복사 후 순회
            for name, proc in list(self._targets.items()):
                try:
                    if proc.is_running():
                        current_cpu[name] = proc.cpu_percent(interval=None)
                        mem_info = proc.memory_full_info()
                        mem_mb = (mem_info.uss if hasattr(mem_info, 'uss') else mem_info.rss) / (1024 ** 2)
                        current_mem[name] = mem_mb
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            self._samples.append({
                "t": elapsed,
                "cpu": current_cpu,
                "mem": current_mem
            })
            # Event.wait → sleep 대신 사용, stop 시 즉시 깨어남
            self._stop_event.wait(timeout=self._interval)