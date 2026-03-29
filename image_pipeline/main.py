import csv
import argparse
import json
from pathlib import Path
from pipeline.orchestrator import run_pipeline
from config import PipelineConfig, SystemConfig, SourceConfig, LoaderConfig
from pipeline.utils.logger import pipeline_logger
def get_parsed_configs() -> tuple[SystemConfig, PipelineConfig]:
    """터미널 인자를 파싱하여 알맞은 Config 객체를 생성 및 반환합니다."""
    parser = argparse.ArgumentParser(description="AIHub 데이터 파이프라인")
    
    # parser.add_argument("--source", type=str, default="aihub", 
    #                     choices=["aihub", "url"], 
    #                     help="데이터를 가져올 소스 (기본: aihub)")
    parser.add_argument("--loader", type=str, default="local", 
                        choices=["local", "gcs"], 
                        help="데이터를 저장할 목적지 (기본: local)")
    parser.add_argument("--chunk-size", type=int, default=50, 
                        help="청크 크기")
    parser.add_argument("--consumers", type=int, default=4, 
                        help="컨슈머 개수")
    parser.add_argument("--file-key", type=str, default=None, 
                        help="특정 파일 키만 처리")
    args = parser.parse_args()

    # 1. 입력받은 문자열(str)로 하위 Config들을 먼저 생성합니다.
    # custom_source = SourceConfig(source_type=args.source)
    from dataclasses import replace
    custom_source = SourceConfig(source_type="aihub")
    custom_loader = LoaderConfig(storage_type=args.loader)
    if args.file_key:
        custom_source = replace(custom_source, aihub=replace(custom_source.aihub, file_key=args.file_key))
    # PipelineConfig inject source and loader
    pipe_conf = PipelineConfig(
        source=custom_source,
        loader=custom_loader,
        chunk_size=args.chunk_size,
        num_consumers=args.consumers
    )
    sys_conf = SystemConfig()
    return sys_conf, pipe_conf

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

def setup_directories(sys_conf: SystemConfig):
    sys_conf.download_dir.mkdir(parents=True, exist_ok=True)
    sys_conf.archive_dst.mkdir(parents=True, exist_ok=True)
    
def main():
    sys_conf, pipe_conf = get_parsed_configs()
    setup_directories(sys_conf)

    with open(pipe_conf.source.aihub.manifest_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        manifests = [(row['file_name'], row['size'], row['file_key'])
            for row in reader]
    if pipe_conf.source.aihub.file_key:
        paired_tasks = [{
            "base_name": "음식302_Val",
            "image_key": pipe_conf.source.aihub.file_key,
            "label_key": "49596"
        }]
    else:
        paired_tasks = pair_manifest_data(manifests)

    failed_list = []
    for task in paired_tasks:
        try:
            metrics = run_pipeline(task, pipe_conf, sys_conf)
        except Exception as e:
            pipeline_logger.error(f"[{task['base_name']}] pipeline error: {e}")
            failed_list.append(task)
            break
        finally:
            # save metrics
            import multiprocessing
            for p in multiprocessing.active_children():
                print(f"[System] {p.name} process end...")
                p.terminate()
                p.join()

            with open(sys_conf.monitor.metrics_dir / f"{task['base_name']}.json", "w") as f:
                json.dump(metrics, f, indent=4, ensure_ascii=False)
                print(f"[System] {task['base_name']} metrics saved...")
    print("pipeline end...")
    
    # retry
    retry = False
    if retry == True:
        for failed_task in failed_list:
            try:
                run_pipeline(failed_task, pipe_conf, sys_conf)
            except Exception as e:
                pipeline_logger.error(f"[{failed_task['base_name']}] pipeline error: {e}")
if __name__ == "__main__":
    main()