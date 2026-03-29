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
from config import TransformConfig

class ImageTransformer:
    def __init__(self, t_conf: TransformConfig):
        self.t_conf = t_conf
        self.target_size = t_conf.target_size
        # parse interpolation, extension, encode_params
        self._parse_config()

    def _parse_config(self):
        inter_map = {
            "linear": cv2.INTER_LINEAR,
            "area": cv2.INTER_AREA,
            "cubic": cv2.INTER_CUBIC,
            "nearest": cv2.INTER_NEAREST,
            "lanczos4": cv2.INTER_LANCZOS4
        }

        self.interpolation = inter_map.get(self.t_conf.interpolation.lower(), cv2.INTER_AREA)
        
        if self.t_conf.extension == "webp":
            self.cv2_flag = cv2.IMWRITE_WEBP_QUALITY
            self.extension = "webp"
        elif self.t_conf.extension == "jpg":
            self.cv2_flag = cv2.IMWRITE_JPEG_QUALITY
            self.extension = "jpg"
        else:
            print(f"Unsupported extension: {self.t_conf.extension}, use jpg")
            self.cv2_flag = cv2.IMWRITE_JPEG_QUALITY
            self.t_conf.extension = "jpg"
            self.extension = "jpg"
            
        self.encode_params = [self.cv2_flag, self.t_conf.quality]

    def decode(self, image_src_bytes: bytes) -> np.ndarray:
        img_array = np.frombuffer(image_src_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Image decoding error")
        return img
        
    def transform_only_resize(self, img):
        return cv2.resize(img, self.t_conf.target_size, interpolation=self.interpolation)

    def transform_letterbox_image_and_boxes(self, img, yolo_boxes):
        """
        비율을 유지하며 이미지를 리사이즈+패딩하고, YOLO 바운딩 박스 좌표를 보정합니다.
        :param img: 원본 이미지 (numpy array)
        :param yolo_boxes: 원본 YOLO 좌표 리스트 (예: [(class_id, x_c, y_c, w, h), ...])
        :param target_size: 최종 목표 해상도 (width, height)
        :return: 패딩된 이미지, 보정된 YOLO 좌표 리스트
        """
        h_orig, w_orig = img.shape[:2]
        target_w, target_h = self.t_conf.target_size

        # 1. 스케일 비율 계산 (가로, 세로 중 더 많이 줄어야 하는 쪽에 맞춤)
        scale = min(target_w / w_orig, target_h / h_orig)

        # 2. 비율에 맞춰 이미지 축소 (패딩 전)
        new_w = int(w_orig * scale)
        new_h = int(h_orig * scale)
        resized_img = cv2.resize(img, (new_w, new_h), interpolation=self.interpolation)

        # 3. 빈 공간(패딩) 크기 계산 (상하좌우 정중앙에 배치하기 위해 2로 나눔)
        pad_x = (target_w - new_w) / 2.0
        pad_y = (target_h - new_h) / 2.0

        # 4. 이미지에 회색(114) 패딩 추가 (YOLO 공식 권장 색상)
        top = int(pad_y)
        bottom = int(target_h - new_h - top)
        left = int(pad_x)
        right = int(target_w - new_w - left)

        padded_img = cv2.copyMakeBorder(
            resized_img, top, bottom, left, right,
            cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )
        # 5. YOLO 바운딩 박스 좌표 보정
        new_boxes = []
        for box in yolo_boxes:
            class_id = box['code_name']
            # class_id = self.get_class_id(c_name) # 이전에 만든 ID 변환 메소드 활용
            
            x_c = box['x_center']
            y_c = box['y_center']
            w = box['width']
            h = box['height']
            # (기존 정규화 좌표 * 원본 픽셀 길이 * 스케일 비율 + 추가된 패딩 픽셀) / 최종 목표 픽셀 길이
            new_x_c = ((x_c * w_orig) * scale + pad_x) / target_w
            new_y_c = ((y_c * h_orig) * scale + pad_y) / target_h

            # 너비와 높이는 이동(패딩)의 영향을 받지 않고 크기 비율만 변함
            new_w_box = ((w * w_orig) * scale) / target_w
            new_h_box = ((h * h_orig) * scale) / target_h

            new_boxes.append((
                class_id,
                new_x_c,
                new_y_c,
                new_w_box,
                new_h_box
            ))

        return padded_img, new_boxes

    def encode(self, img: np.ndarray) -> bytes:
        is_success, buffer = cv2.imencode(self.extension, img, self.encode_params)
        if not is_success:
            raise ValueError("Image encoding error")
        return buffer.tobytes()
    def add_label_info(self, name: str, label: list[dict]) -> list[dict]:
        korean_class_name = Path(name).parent
        for box in label:
            new_label ['korean_name'] = korean_class_name
        return label
    def process_full_cycle(self, name: str, image_src_bytes: bytes, label: list[dict]) -> tuple[str, bytes, list[dict]]:
        img = self.decode(image_src_bytes)
        if label:
            processed_img, processed_label = \
                self.transform_letterbox_image_and_boxes(img, label)
            processed_label = self.add_label_info(name, processed_label)
        else:
            processed_img = self.transform_only_resize(img)
            processed_label = label
        processed_bytes = self.encode(processed_img)
        new_name = str(Path(name).with_suffix(f".{self.extension}"))
        return new_name, processed_bytes, processed_label

def process_chunk(chunk: list[tuple[str, bytes]],
				t_conf: TransformConfig) -> list[tuple[str, bytes]]:
    transformer = ImageTransformer(t_conf)
    processed_chunk = []
    for name, image_src_bytes, label in chunk:
        result = transformer.process_full_cycle(name, image_src_bytes, label)
        processed_chunk.append(result)
    return processed_chunk
