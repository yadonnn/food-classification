import cv2
import numpy as np
import os
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from tqdm import tqdm

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

def resize_with_padding(image_path, src_root, dst_root, target_size=384):
    """이미지 리사이징 및 저장 핵심 로직"""
    try:
        img = cv2.imread(str(image_path))
        if img is None: return None
        
        h, w = img.shape[:2]
        ratio = target_size / max(h, w)
        new_h, new_w = int(h * ratio), int(w * ratio)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        canvas[(target_size-new_h)//2:(target_size-new_h)//2+new_h, 
               (target_size-new_w)//2:(target_size-new_w)//2+new_w] = resized
        
        relative_path = image_path.relative_to(src_root)
        save_path = Path(dst_root) / relative_path.with_suffix('.webp')
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        cv2.imwrite(str(save_path), canvas, [cv2.IMWRITE_WEBP_QUALITY, 90])
        return relative_path
    except Exception:
        return None


def transform_consumer(queue, src_root='data/extracted', dst_root='data/resized_384_webp', target_size=384):
    src_root_path = Path(src_root)
    os.makedirs(dst_root, exist_ok=True)

    processed = 0
    skipped = 0
    seen = set()
    start_time = time.time()

    while True:
        item = queue.get()
        if item is None:
            break

        image_path = Path(item).resolve()
        if image_path in seen:
            continue
        seen.add(image_path)

        if not image_path.exists():
            skipped += 1
            continue

        result = resize_with_padding(image_path, src_root_path, dst_root, target_size=target_size)
        if result is None:
            skipped += 1
            continue

        processed += 1
        if processed % 200 == 0:
            print(f"🧩 transform 진행: {processed}장")

    end_time = time.time()
    duration = end_time - start_time
    final_size_bytes = get_dir_size_bytes(dst_root)
    final_size_gb = final_size_bytes / (1024 ** 3)
    final_size_mb = final_size_bytes / (1024 ** 2)
    avg_speed = processed / duration if duration > 0 else 0
    avg_size_kb = (final_size_bytes / processed) / 1024 if processed > 0 else 0

    print("\n" + "="*50)
    print("📋 [실시간 변환 완료 요약 리포트]")
    print("="*50)
    print(f"✅ 총 처리 이미지: {processed:,} 장")
    print(f"⏭️ 스킵 이미지: {skipped:,} 장")
    print(f"📦 전체 저장 용량: {final_size_gb:.2f} GB ({final_size_mb:.2f} MB)")
    print(f"🖼️ 장당 평균 용량: {avg_size_kb:.2f} KB")
    print(f"⏱️ 총 소요 시간  : {duration/60:.1f} 분")
    print(f"⚡ 평균 처리 속도: {avg_speed:.2f} img/s")
    print("="*50)

def run_transform():
    SRC = 'data/extracted'
    DST = 'data/resized_384_webp'
    
    files = sorted([f for f in Path(SRC).rglob('*') if f.suffix.lower() in ('.jpg', '.png', '.webp')])
    total_files = len(files)
    
    start_time = time.time() # 시작 시간 기록
    
    # 🚀 tqdm 진행바 시작
    pbar = tqdm(total=total_files, desc="🚀 Resizing", unit="img", colour='green')
    current_class = ""
    
    with ProcessPoolExecutor() as executor:
        func = partial(resize_with_padding, src_root=Path(SRC), dst_root=DST)
        for res in executor.map(func, files):
            if res:
                pbar.set_postfix(class_name=res.parent.name)
            pbar.update(1)
            
    pbar.close()
    end_time = time.time() # 종료 시간 기록

    # --- 📊 최종 리포트 계산 ---
    print("\n" + "="*50)
    print("📋 [작업 완료 요약 리포트]")
    print("="*50)
    
    # 1. 용량 계산
    final_size_bytes = get_dir_size_bytes(DST)
    final_size_gb = final_size_bytes / (1024 ** 3)
    final_size_mb = final_size_bytes / (1024 ** 2)
    
    # 2. 통계 계산
    duration = end_time - start_time
    avg_speed = total_files / duration if duration > 0 else 0
    avg_size_kb = (final_size_bytes / total_files) / 1024 if total_files > 0 else 0

    # 3. 출력
    print(f"✅ 총 처리 이미지: {total_files:,} 장")
    print(f"📦 전체 저장 용량: {final_size_gb:.2f} GB ({final_size_mb:.2f} MB)")
    print(f"🖼️ 장당 평균 용량: {avg_size_kb:.2f} KB")
    print(f"⏱️ 총 소요 시간  : {duration/60:.1f} 분")
    print(f"⚡ 평균 처리 속도: {avg_speed:.2f} img/s")
    print("="*50)

if __name__ == "__main__":
    run_transform()
