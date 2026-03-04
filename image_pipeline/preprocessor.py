"""
OpenCV 기반 이미지 변환 로직
"""
import cv2
import numpy as np
import os
import zipfile
from pathlib import Path
from config import *

def resize_image(image_src_path: Path,
                 src_root: Path = TRANSFORM_SRC_DIR,
                 dst_root: Path = TRANSFORM_DST_DIR,
                 target_size: int = TARGET_SIZE,
                 extension: str = TRANSFORM_EXTENSION,
                 quality: int = 90) -> Path:
    img = cv2.imread(image_src_path)
    if img is None:
        raise ValueError(f"Image not found at {image_src_path}")

    img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_AREA)

    relative_path = image_src_path.relative_to(src_root)
    save_path = dst_root / relative_path
    save_path = save_path.with_suffix(f".{extension}")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(save_path, img, [cv2.IMWRITE_WEBP_QUALITY, quality])
    return save_path

# ====================================================
# --- 압축 함수 ---
# ====================================================
def extract_archive(src_root: Path = TRANSFORM_SRC_DIR,
                    dst_root: Path = TRANSFORM_DST_DIR) -> list[zipfile.ZipInfo]:
    """압축을 해제하고, ZipInfo 리스트 반환"""
    with zipfile.ZipFile(src_root, 'r') as z:
        info_list = []
        for info in z.infolist():
            try:
                if info.is_dir():
                    continue
                info.filename = info.filename.encode('cp437').decode('cp949')
                info_list.append(info)
            except:
                info.filename = info.filename
                info_list.append(info)            
            z.extract(info.filename, dst_root)

    return info_list

def make_archive(src_root: Path = ARCHIVE_SRC_DIR, dst_root: Path = ARCHIVE_DST_DIR) -> list[zipfile.ZipInfo]:
    """디렉토리를 zip으로 압축하고, ZipInfo 리스트 반환"""
    zip_dst_path = dst_root / f"{src_root.name}.zip"
    with zipfile.ZipFile(zip_dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for file in src_root.rglob('*'):
            if file.is_file():
                arcname = file.relative_to(src_root) # zip 내부 상대경로
                z.write(file, arcname)
        info_list = z.infolist()
    return info_list

