import zipfile
from pathlib import Path

def test_stream_zip_data(zip_path: Path, chunk_size: int = 50):
	with zipfile.ZipFile(zip_path, 'r') as z:
        # 이미지 파일 이름 인코딩 (cp949, cp437) 순서로 저장
		names = [
            (n.encode('cp437').decode('cp949'), n) for n in z.namelist()
			if n.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
		chunk = []
		for decoded_name, name in names:
		    chunk.append((decoded_name, z.read(name)))
		    if len(chunk) == chunk_size:
			    yield chunk
			    chunk = []
		if chunk:
		    yield chunk

if __name__ == "__main__":
    root_dir = Path(__file__).parent
    bench_data_dir = root_dir / "data" / "benchmarks"
    zip_path = bench_data_dir / "sample_val_302.zip"
    for chunk in test_stream_zip_data(zip_path):
        print(chunk[0][0])
        break