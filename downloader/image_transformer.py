import cv2
import numpy as np
import os
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from tqdm import tqdm
from logger import setup_logger

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


def transform_worker(folder_queue, upload_queue, src_root='data/extracted', dst_root='data/resized_384_webp', target_size=384):
    import shutil
    logger = setup_logger()
    src_root_path = Path(src_root).resolve()
    os.makedirs(dst_root, exist_ok=True)
    
    # 리소스 제한 (CPU 병목 방지를 위해 max_workers를 2명 정도로 제한)
    executor = ProcessPoolExecutor(max_workers=3)
    
    while True:
        item = folder_queue.get()
        if item is None:
            print("이미지 변환 워커: 종료 신호 수신")
            upload_queue.put(None)
            break
        folder_item, file_key = item
            
        folder_path = Path(folder_item).resolve()
        print(f"🔄 이미지 변환 시작: {folder_path} (filekey: {file_key})")
        
        if not folder_path.exists() or not folder_path.is_dir():
            print(f"⚠️ 폴더가 존재하지 않거나 디렉토리가 아닙니다: {folder_path}")
            continue
            
        files = sorted([f for f in folder_path.rglob('*') if f.suffix.lower() in ('.jpg', '.png', '.jpeg')])
        
        if not files:
            print(f"⚠️ 폴더에 이미지 파일이 없습니다: {folder_path}")
            # 이미지가 없더라도 폴더는 삭제
            try:
                shutil.rmtree(folder_path)
                print(f"🗑️ 빈 원본 폴더 삭제 완료: {folder_path}")
            except Exception as e:
                pass
            continue
            
        func = partial(resize_with_padding, src_root=src_root_path, dst_root=dst_root, target_size=target_size)
        
        processed_count = 0
        for res in executor.map(func, files):
            if res:
                # res는 src_root에 대한 상대 경로
                # 실제 저장된 절대/상대 경로를 만들어 upload_queue에 전달
                upload_item = (Path(dst_root) / res).with_suffix('.webp')
                upload_queue.put(str(upload_item))
                processed_count += 1
                
        print(f"✅ 이미지 변환 완료 ({processed_count}/{len(files)}장): {folder_path}")
        
        if processed_count != len(files):
            logger.error(f"❌ 무결성 검증 실패 (이미지 변환): 원본 {len(files)}장 != 변환 {processed_count}장 (filekey: {file_key}, folder: {folder_path})")
            print(f"❌ 무결성 검증 실패로 인해 원본 해제 폴더를 삭제하지 않습니다: {folder_path}")
        else:
            logger.info(f"✅ 무결성 검증 통과 (이미지 변환): 총 {processed_count}장 일치")
            
            # [중요] 삭제 로직 2: 리사이징 및 업로드 큐 적재가 정상 종료되면 원본 해제 폴더 삭제
            try:
                shutil.rmtree(folder_path)
                print(f"🗑️ 원본 해제 폴더 삭제 완료: {folder_path}")
            except Exception as e:
                print(f"❌ 원본 폴더 삭제 실패: {folder_path} ({e})")
            
    executor.shutdown(wait=True)

