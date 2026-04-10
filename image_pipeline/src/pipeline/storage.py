import zipfile
import io
from pathlib import Path
from google.cloud import storage
from contextlib import contextmanager

class LocalZipAdapter:
    """로컬 ZIP 저장을 담당하는 어댑터"""
    def __init__(self, output_path):
        self.output_path = output_path
        self.zip_file = None

    # 파이썬의 with 문을 지원하기 위한 매직 메서드
    def __enter__(self):
        self.zip_file = zipfile.ZipFile(self.output_path, 'w', compression=zipfile.ZIP_STORED)
        return self

    def convert_to_yolo_format(self, label):
        yolo_label = []
        for bbox in label:
            cls_id = bbox['class_id']
            x_center = round(float(bbox['x_center']), 6)
            y_center = round(float(bbox['y_center']), 6)
            width = round(float(bbox['width']), 6)
            height = round(float(bbox['height']), 6)
            yolo_label.append(f"{cls_id} {x_center} {y_center} {width} {height}")
        return "\n".join(yolo_label)
    
    def write(self, processed_result: tuple[str, bytes, list[dict]]):
        file_name, data, label = processed_result

        image_path = str(Path("images") / Path(file_name).name)
        self.zip_file.writestr(image_path, data)

        if label:
            label_path = str(Path("labels") / Path(file_name).with_suffix(".txt").name)
            yolo_label = self.convert_to_yolo_format(label)
            self.zip_file.writestr(label_path, yolo_label)
        return 1
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.zip_file:
            self.zip_file.close()
            
class GCSAdapter:
    """GCS 직접 업로드를 담당하는 어댑터"""
    def __init__(self, bucket_name, prefix=""):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.prefix = prefix
        self.zip_buffer = io.BytesIO()
        self.zip_file = zipfile.ZipFile(self.zip_buffer, 'w', compression=zipfile.ZIP_STORED)

    def __enter__(self):
        # GCS는 연결 유지가 필요 없지만 인터페이스 통일을 위해 구현
        self.zip_file = zipfile.ZipFile(self.zip_buffer, 'w', compression=zipfile.ZIP_STORED)
        return self

    def convert_to_yolo_format(self, label):
        yolo_label = []
        for info in label:
            cls_id, x_c, y_c, w, h = info
            x_center = round(float(x_c), 6)
            y_center = round(float(y_c), 6)
            width = round(float(w), 6)
            height = round(float(h), 6)
            yolo_label.append(f"{cls_id} {x_center} {y_center} {width} {height}")
        return "\n".join(yolo_label)

    def write(self, processed_result: tuple[str, bytes, list[dict]]):
        file_name, data, label = processed_result
        # print(processed_result)
        image_path = str(Path("images") / Path(file_name).name)
        self.zip_file.writestr(image_path, data)

        if label:
            label_path = str(Path("labels") / Path(file_name).with_suffix(".txt").name)
            yolo_label = self.convert_to_yolo_format(label)
            self.zip_file.writestr(label_path, yolo_label)
        
        self.zip_buffer.seek(0)
        blob_name = 
        blob = self.bucket.blob(f"{self.prefix}{file_name}")
        blob.upload_from_file(self.zip_buffer, content_type='application/zip')
        print(f"✅ {file_name} 업로드 완료: gs://{self.bucket.name}/{self.prefix}{file_name}")
        return 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.zip_file:
            self.zip_file.close()