"""
디스크 I/O 전용 벤치마크 (이미지 처리 제외)
- Disk: zip 해제(디스크 저장) → 디스크에서 읽기 → zip 재압축
- Stream: zip에서 메모리로 읽기 → 메모리에서 zip에 쓰기
"""
import sys
import shutil
import zipfile
from pathlib import Path

from benchmark_framework import BenchmarkConfig, ResourceMonitor, BenchmarkRunner

sys.path.append(str(Path(__file__).parent.parent / "image_pipeline"))
import preprocessor


def run_disk_io(config: BenchmarkConfig, monitor: ResourceMonitor) -> dict:
    """디스크 기반 I/O 측정: zip 해제 → 파일 읽기 → zip 재압축"""

    # 초기화
    shutil.rmtree(config.extract_dst, ignore_errors=True)
    config.extract_dst.mkdir(parents=True, exist_ok=True)

    # 1. READ — zip 해제 (디스크에 파일 쓰기)
    monitor.mark("read")
    image_path_list = preprocessor.extract_archive(config.zip_path, config.extract_dst)

    # 2. WRITE — 해제된 파일을 그대로 다시 zip으로 압축
    monitor.mark("write")
    zip_dst_path = config.tmp_dir / f"disk_io_{config.zip_path.name}"
    with zipfile.ZipFile(zip_dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
        for file_path in image_path_list:
            arcname = file_path.relative_to(config.extract_dst)
            z_out.write(file_path, arcname)

    metrics = monitor.to_summary()
    metrics["total_images_processed"] = len(image_path_list)
    return metrics


def run_stream_io(config: BenchmarkConfig, monitor: ResourceMonitor) -> dict:
    """스트리밍 기반 I/O 측정: zip → 메모리 → zip (디스크 미사용)"""
    image_count = 0

    zip_dst_path = config.tmp_dir / f"stream_io_{config.zip_path.name}"

    with zipfile.ZipFile(zip_dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
        with zipfile.ZipFile(config.zip_path, 'r') as z_in:
            img_names = [
                n for n in z_in.namelist()
                if n.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))
            ]

            # 1. READ — zip에서 메모리로 읽기
            monitor.mark("read")
            buffers = []
            for name in img_names:
                buffers.append((name, z_in.read(name)))

            # 2. WRITE — 메모리에서 바로 zip에 쓰기
            monitor.mark("write")
            for name, image_bytes in buffers:
                z_out.writestr(name, image_bytes)
                image_count += 1

    metrics = monitor.to_summary()
    metrics["total_images_processed"] = image_count
    return metrics


if __name__ == "__main__":
    root_dir = Path(__file__).parent
    bench_data_dir = root_dir / "data" / "benchmarks"

    config = BenchmarkConfig(
        zip_path=bench_data_dir / "sample_val_302.zip",
        extract_dst=bench_data_dir / "extracted",
        transform_dst=bench_data_dir / "transformed",
        archive_dst=bench_data_dir / "archive",
        tmp_dir=bench_data_dir / "tmp",
        results_dir=root_dir / "data" / "results",
        rounds=3,
    )

    runner = BenchmarkRunner(config)

    runner.run_strategy("Disk_IO", run_disk_io)
    runner.run_strategy("Stream_IO", run_stream_io)

    runner.save_results(version_tag="disk_stream_io_v0.2")