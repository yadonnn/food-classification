import cv2
import numpy as np
import os
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from config import *
from utils.logger import with_logging, pipeline_logger

def get_dir_size_bytes(path):
    """폴더의 전체 용량을 Byte 단위로 계산 (정밀도 유지)"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size_bytes(entry.path)
    except Exception:
        pass
    return total

def print_summary_report(start_time, end_time, processed_count, dst_root, skipped_count=None):
    duration = end_time - start_time
    final_size_bytes = get_dir_size_bytes(dst_root)
    final_size_gb = final_size_bytes / (1024 ** 3)
    final_size_mb = final_size_bytes / (1024 ** 2)
    avg_speed = processed_count / duration if duration > 0 else 0
    avg_size_kb = (final_size_bytes / processed_count) / 1024 if processed_count > 0 else 0

    print("\n" + "="*50)
    print("📋 [작업 완료 요약 리포트]")
    print("="*50)
    print(f"✅ 총 처리 이미지: {processed_count:,} 장")
    if skipped_count is not None:
        print(f"⏭️ 스킵 이미지: {skipped_count:,} 장")
    print(f"📦 전체 저장 용량: {final_size_gb:.2f} GB ({final_size_mb:.2f} MB)")
    print(f"🖼️ 장당 평균 용량: {avg_size_kb:.2f} KB")
    print(f"⏱️ 총 소요 시간  : {duration/60:.1f} 분")
    print(f"⚡ 평균 처리 속도: {avg_speed:.2f} img/s")
    print("="*50)


def resize_with_padding(image_path: Path,
                        src_root: Path = TRANSFORM_SRC_DIR,
                        dst_root: Path = TRANSFORM_DST_DIR,
                        target_size: int = TARGET_SIZE):
    """이미지 리사이징 및 저장 핵심 로직"""
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    h, w = img.shape[:2]
    ratio = target_size / max(h, w)
    new_h, new_w = int(h * ratio), int(w * ratio)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
    canvas[(target_size-new_h)//2:(target_size-new_h)//2+new_h, 
            (target_size-new_w)//2:(target_size-new_w)//2+new_w] = resized
    
    relative_path = image_path.relative_to(src_root)
    save_path = dst_root / relative_path.with_suffix('.webp')
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    cv2.imwrite(str(save_path), canvas, [cv2.IMWRITE_WEBP_QUALITY, 90])
    return relative_path

@with_logging
def run_transform_for_chunk(src_root: Path = TRANSFORM_SRC_DIR, dst_root: Path = TRANSFORM_DST_DIR):
    """지정된 청크(파일/폴더 등) 단위로 이미지 변환을 수행하는 함수.
       현재는 전체 폴더를 한 번에 변환하도록 구성되어 있으므로 chunk_key="all_images" 형태로 호출 가능합니다."""
    
    # 🚀 JSON 및 이미지 파일 목록 가져오기
    src_path = Path(src_root)
    dst_path = Path(dst_root)
    
    # rglob을 사용하여 하위 폴더까지 모든 이미지와 JSON 파일을 찾습니다.
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    image_files = [f for f in src_path.rglob('*') if f.suffix.lower() in image_extensions]
    json_files = list(src_path.rglob('*.json'))
    total_images = len(image_files)
    
    # 🚀 JSON 등 메타데이터 라벨 파일 복사 처리
    import shutil
    for j_file in json_files:
        relative_path = j_file.relative_to(src_path)
        save_path = dst_path / relative_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(j_file), str(save_path))
            
    actual_images = 0
    start_time = time.time()
    
    # =========================================================================
    # ⚙️ ProcessPoolExecutor 가이드 (멀티프로세싱)
    # =========================================================================
    # 1. 목적: CPU 집약적인 작업(이미지 리사이징, 연산 등)을 여러 CPU 코어에 분산시켜 병렬로 처리합니다.
    # 2. 동작 방식:
    #    - 각 이미지 처리를 별도의 '프로세스'로 생성하여 독립된 메모리 공간에서 실행합니다.
    #    - 파이썬의 GIL(Global Interpreter Lock)을 우회하여 실질적인 병렬 처리를 가능케 합니다.
    # 3. 주요 구성 요소:
    #    - max_workers: 동시에 실행할 프로세스 수 (기본값은 CPU 코어 수).
    #    - executor.map(func, iterable): func 함수에 iterable의 각 요소를 하나씩 전달하며 병렬로 실행합니다.
    #    - partial: 고정된 인자(src_root, dst_root 등)를 미리 채워 넣은 새로운 함수를 만드는 데 사용됩니다.
    # =========================================================================
    
    with ProcessPoolExecutor() as executor:
        # 고정 인자를 미리 설정한 partial 함수 생성
        func = partial(resize_with_padding, src_root=src_path, dst_root=dst_path)
        
        # 병렬 실행 시작
        for res in executor.map(func, image_files):
            if res:
                actual_images += 1
                
    end_time = time.time() # 종료 시간 기록

    # --- 📊 최종 리포트 계산 및 출력 ---
    print_summary_report(start_time, end_time, actual_images, dst_path)
    target_success = (actual_images == total_images)
    return target_success
