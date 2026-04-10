import csv
import argparse
import json
import yaml
import pandas as pd
from pathlib import Path
from src.orchestrator import run_pipeline
from configs.config import AppConfig
from src.utils.logger import setup_pipeline_logger
from src.utils.monitor import ResourceMonitor

def parse_args() -> argparse.Namespace:
    """터미널 인자를 파싱하여 알맞은 Config 객체를 생성 및 반환합니다."""
    parser = argparse.ArgumentParser(description="AIHub 데이터 파이프라인")
    
    # parser.add_argument("--source", type=str, default="aihub", 
    #                     choices=["aihub", "url"], 
    #                     help="데이터를 가져올 소스 (기본: aihub)")
    parser.add_argument("--loader", type=str, default=None, 
                        choices=["local", "gcs"], 
                        help="데이터를 저장할 목적지 (기본: local)")
    parser.add_argument("--chunk-size", type=int, default=None, 
                        help="청크 크기")
    parser.add_argument("--consumers", type=int, default=None, 
                        help="컨슈머 개수")
    parser.add_argument("--file-key", type=str, default=None, 
                        help="특정 파일 키만 처리")

    parser.add_argument("--debug", action="store_true", 
                        help="디버그 모드")
    parser.add_argument("--config", type=str, default="configs/base.yaml", 
                        help="기본 설정 파일 경로")
    return parser.parse_args()

def pair_manifest_data(raw_data: list[tuple]) -> list[dict]:
    """
    [('파일명', '용량', '파일키'), ...] 형태의 데이터를 받아
    이미지와 라벨을 짝지어 딕셔너리 리스트로 반환합니다.
    """
    images = {}
    labels = {}
    
    # 1. 데이터를 순회하며 공통 키를 기준으로 이미지/라벨 분리
    for file_name, size, file_key in raw_data:
        # 예외 처리: 쌍이 없는 메타데이터 파일은 무시 (필요시 별도 처리)
        if file_name == '식품영양성분DB.zip':
            continue
            
        if file_name.endswith('_json.zip'):
            # 라벨: '음식101_Val_json.zip' -> '음식101_Val'
            base_name = file_name.replace('_json.zip', '')
            labels[base_name] = file_key
        else:
            # 이미지: '음식101_Val.zip' -> '음식101_Val'
            base_name = file_name.replace('.zip', '')
            images[base_name] = file_key

    # 2. 짝 맞추기
    paired_tasks = []
    
    # 정렬해서 처리하기 위해 natsort나 파이썬 기본 정렬 사용
    for base_name in sorted(images.keys()):
        if base_name in labels:
            paired_tasks.append({
                "base_name": base_name,          # 예: 음식202_Val
                "image_key": images[base_name],  # 예: 49522
                "label_key": labels[base_name]   # 예: 49593
            })
        else:
            print(f"⚠️ 경고: '{base_name}'의 라벨 파일이 없습니다. 스킵합니다.")

    return paired_tasks

def setup_directories(config):
    config.pipeline.source.raw_dir.mkdir(parents=True, exist_ok=True)
    config.pipeline.source.processed_dir.mkdir(parents=True, exist_ok=True)
    config.system.monitor.metrics_dir.mkdir(parents=True, exist_ok=True)
    config.system.logging.log_dir.mkdir(parents=True, exist_ok=True)
    if config.pipeline.loader.storage_type == "local":
        config.pipeline.loader.local.dst_dir.mkdir(parents=True, exist_ok=True)
    
def main():
    monitor = ResourceMonitor()
    # 1. parse args
    args = parse_args()

    # 2. load yaml(debug or base)
    yaml_path = "configs/debug.yaml" if args.debug else args.config
    config = AppConfig.load_yaml(yaml_path)
    setup_directories(config)
    pipeline_logger = setup_pipeline_logger(config.system.logging.log_dir)

    # 3. override
    if args.loader is not None:
        config.pipeline.loader.storage_type = args.loader
    if args.chunk_size is not None:
        config.pipeline.chunk_size = args.chunk_size
    if args.consumers is not None:
        config.pipeline.num_consumers = args.consumers
    if args.file_key is not None:
        config.pipeline.source.aihub.file_key = args.file_key
        
    # Source type별 Task 설정
    if config.pipeline.source.source_type == "aihub":
        with open(config.pipeline.source.aihub.manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            raw_data = [(name, size, key) for name, size, key in reader]
        paired_tasks = pair_manifest_data(raw_data)
        
        # 지정된 file_key(들)이 있다면 해당 키를 가진 쌍만 필터링
        target_keys = config.pipeline.source.aihub.file_key
        if target_keys:
            if isinstance(target_keys, str):
                target_keys = [k.strip() for k in target_keys.split(",")]
            
            set_keys = set(target_keys)
            paired_tasks = [
                task for task in paired_tasks
                if task["image_key"] in set_keys or task["label_key"] in set_keys
            ]
            print(f"[System] 특정 file_key 값({list(set_keys)})에 해당하는 {len(paired_tasks)}개의 데이터셋만 처리합니다.")
    elif config.pipeline.source.source_type == "local":
        src_zip = config.pipeline.source.local.src_zip_path
        paired_tasks = [{
            "base_name": Path(src_zip).stem,
            "image_key": None,
            "label_key": None,
        }]

    failed_list = []
    for task in paired_tasks:
        metrics = None
        try:
            metrics = run_pipeline(task, config.pipeline, monitor)
        except Exception as e:
            pipeline_logger.error(f"[{task['base_name']}] pipeline error: {e}")
            failed_list.append(task)
            break
        finally:
            # save metrics
            import multiprocessing

            monitor.stop()
            for p in multiprocessing.active_children():
                print(f"[System] {p.name} process end...")
                p.terminate()
                p.join()

            if metrics is not None:
                with open(config.system.monitor.metrics_dir / f"{task['base_name']}.json", "w") as f:
                    json.dump(metrics, f, indent=4, ensure_ascii=False)
                    print(f"[System] {task['base_name']} metrics saved...")
    print("pipeline end...")
    
    # # retry
    # retry = False
    # if retry == True:
    #     for failed_task in failed_list:
    #         try:
    #             run_pipeline(failed_task, pipe_conf, sys_conf)
    #         except Exception as e:
    #             pipeline_logger.error(f"[{failed_task['base_name']}] pipeline error: {e}")
if __name__ == "__main__":
    main()