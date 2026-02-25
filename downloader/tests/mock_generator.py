import os
import zipfile
import PIL.Image
import io

def create_mock_zip(target_path, num_images=5):
    """
    테스트를 위한 가짜 ZIP 파일을 생성합니다.
    내부에는 소량의 더미 이미지와 텍스트 파일이 포함됩니다.
    """
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    with zipfile.ZipFile(target_path, 'w') as zf:
        for i in range(num_images):
            # 10x10 사이즈의 더미 이미지 생성
            img = PIL.Image.new('RGB', (10, 10), color=(i*40, 100, 200))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            
            # ZIP 내부에 저장 (폴더 구조 포함)
            img_name = f"샘플/test_image_{i}.jpg"
            zf.writestr(img_name, img_byte_arr.getvalue())
            
        zf.writestr("샘플/metadata.json", '{"status": "mock"}')
        
    print(f"🎨 Mock ZIP 생성 완료: {target_path}")
    return target_path

if __name__ == "__main__":
    create_mock_zip("downloader/data/tmp/src/test.zip")