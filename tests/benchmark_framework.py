import os
import time
import json
import gc
import threading
import psutil
from statistics import mean
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Callable


@dataclass
class BenchmarkConfig:
    zip_path: Path
    extract_dst: Path
    transform_dst: Path
    archive_dst: Path
    tmp_dir: Path
    results_dir: Path
    target_size: int = 384
    extension: str = "webp"
    interpolation: str = "INTER_AREA"
    quality: int = 90
    rounds: int = 1
    

    def __post_init__(self):
        for d in [self.extract_dst, self.transform_dst, self.archive_dst, self.tmp_dir, self.results_dir]:
            d.mkdir(parents=True, exist_ok=True)


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

    def to_raw(self) -> dict:
        """시계열 원본 데이터 반환 (시각화용)"""
        return {
            "samples": [
                {
                    "t": round(s["t"], 4),
                    "cpu": {k: round(v, 1) for k, v in s["cpu"].items()},
                    "mem_mb": {k: round(v, 1) for k, v in s["mem"].items()}
                }
                for s in self._samples
            ],
            "events": [
                {
                    "stage": name,
                    "start_time": round(t, 4)
                }
                for name, t in self._events
            ],
        }

    def to_summary(self) -> dict:
        """stage 구간별 + 프로세스별 집계"""
        if not self._events or not self._samples:
            return {}

        end_time = self._samples[-1]["t"] if self._samples else 0.0
        result = {}

        for i, (stage_name, start_t) in enumerate(self._events):
            if i + 1 < len(self._events):
                end_t = self._events[i + 1]["t"]
            else:
                end_t = end_time

            stage_samples = [s for s in self._samples if start_t <= s["t"] < end_t]

            duration = end_t - start_t
            result[f"{stage_name}_time_sec"] = duration

            process_names = self._targets.keys()

            for name in process_names:
                if stage_samples:
                    cpu_values = [s["cpu"][name] for s in stage_samples if name in s["cpu"]]
                    mem_values = [s["mem"][name] for s in stage_samples if name in s["mem"]]

                    prefix = f"{stage_name}_{name}"
                    if cpu_values:
                        result[f"{prefix}_cpu_avg_percent"] = round(mean(cpu_values), 1)
                        result[f"{prefix}_cpu_max_percent"] = round(max(cpu_values), 1)
                        result[f"{prefix}_memory_peak_mb"] = round(max(mem_values), 1)
                        result[f"{prefix}_sample_count"] = len(stage_samples)
                    else:
                        prefix = f"{stage_name}_{name}"
                        result[f"{prefix}_cpu_avg_percent"] = 0.0
                        result[f"{prefix}_cpu_max_percent"] = 0.0
                        result[f"{prefix}_memory_peak_mb"] = 0.0
                        result[f"{prefix}_sample_count"] = 0

        return result


class BenchmarkRunner:
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results = []

    def run_strategy(self, strategy_name: str, pipeline_fn: Callable, *args, **kwargs):
        print(f"🚀 Starting Benchmark: {strategy_name}")

        for r in range(self.config.rounds):
            print(f"  Round {r+1}/{self.config.rounds}...", end="", flush=True)

            gc.collect()
            time.sleep(2)

            monitor = ResourceMonitor()
            monitor.start()
            start_total = time.perf_counter()
            try:
                stage_metrics = pipeline_fn(self.config, monitor, *args, **kwargs)
            finally:
                end_total = time.perf_counter()
                monitor.stop()
                monitor.to_summary()
            total_time = end_total - start_total
            print(f" Done ({total_time:.3f}s)")

            metrics = {
                "strategy": strategy_name,
                "round": r + 1,
                "total_pipeline_time_sec": total_time,
                **stage_metrics,
                "raw": monitor.to_raw(),
            }
            self.results.append(metrics)

    def save_results(self, version_tag: str = "v1.0"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_path = self.config.results_dir / f"{version_tag}_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=4, ensure_ascii=False)

        print(f"✅ Benchmark results saved to: {output_path}")
        return output_path
