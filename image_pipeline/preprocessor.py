"""
OpenCV 기반 이미지 변환 로직
압축 관련 로직
파일 이동 로직
"""
import cv2
import numpy as np
import os
import zipfile
from pathlib import Path
from config import *
from logger import time_logger, pipeline_logger

def resize_image(image_src_path: Path,
                 src_root: Path = TRANSFORM_SRC_DIR,
                 dst_root: Path = TRANSFORM_DST_DIR,
                 target_size: int = TARGET_SIZE,
                 extension: str = TRANSFORM_EXTENSION,
                 quality: int = IMAGE_QUALITY) -> Path:
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

@time_logger
def transform_images(file_key: str,
						image_path_list: list[Path]):
    """"""
    total_images = len(image_path_list)

    pipeline_logger.info(f"[{file_key}] {total_images} images transforming...")
    for i, image_path in enumerate(image_path_list):
        try:
            resize_image(image_path)
            if (i+1) % (total_images//10) == 0:
                pipeline_logger.info(f"[{file_key}] {i+1}/{total_images} images transformed ")

        except Exception as e:
            pipeline_logger.error(f"[{file_key}] {image_path} image transforming error: {e}")
    
    pipeline_logger.info(f"[{file_key}] {total_images} images transformed")
    
    return total_images
# ====================================================
# --- 압축 함수 ---
# ====================================================
@time_logger
def extract_archive(src_path: Path,
                    dst_root: Path = EXTRACT_DST_DIR) -> list[Path]:
    """압축을 해제하고, ZipInfo 리스트 반환"""
    with zipfile.ZipFile(src_path, 'r') as z:
        path_list = []
        for info in z.infolist():
            try:
                if info.is_dir():
                    continue
                fixed_name = info.filename.encode('cp437').decode('cp949')
            except:
                fixed_name = info.filename
            
            target_path = dst_root / fixed_name 
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'wb') as f:
                f.write(z.read(info))
            path_list.append(target_path)

    return path_list

@time_logger
def make_archive(file_name: str,
                 src_root: Path = ARCHIVE_SRC_DIR,
                 dst_root: Path = ARCHIVE_DST_DIR,
                 target_size: int = TARGET_SIZE,
                 extension: str = TRANSFORM_EXTENSION) -> list[zipfile.ZipInfo]:
    """디렉토리를 zip으로 압축하고, ZipInfo 리스트 반환"""
    zip_dst_path = dst_root / f"{extension}_{str(target_size)}_{file_name}"
    with zipfile.ZipFile(zip_dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for file in src_root.rglob('*'):
            if file.is_file():
                arcname = file.relative_to(src_root) # zip 내부 상대경로
                z.write(file, arcname)
        info_list = z.infolist()
    return info_list

@time_logger
def move_file(src_path: Path,
              dst_root: Path = ARCHIVE_DST_DIR) -> Path:
    """src_path를 dst_root로 이동하고 이동한 파일 경로 반환"""
    dst_path = dst_root / src_path.name
    src_path.replace(dst_path)
    return dst_path