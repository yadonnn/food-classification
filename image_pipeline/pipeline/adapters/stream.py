import zipfile
import json
from pathlib import Path
from typing import Iterator
from pipeline.adapters.downloader import download_file

def get_valid_pairs(image_zip_obj, label_zip_obj) -> tuple[list[tuple[str, str]], dict]:
		
		# extract files list with size > 0 & valid extension
		img_map = {}
		empty_imgs = set()
		for info in image_zip_obj.infolist():
			if info.is_dir():
				continue

			name = info.filename
			if name.lower().endswith(('jpg', 'webp', 'png')):
				stem = Path(name).stem
				if info.file_size > 0:
					img_map[stem] = name
				else:
					empty_imgs.add(stem)
		
		lbl_map = {}
		empty_lbls = set()
		for info in label_zip_obj.infolist():
			if info.is_dir():
				continue
			
			name = info.filename
			if name.lower().endswith('json'):
				stem = Path(name).stem
				if info.file_size > 0:
					lbl_map[stem] = name
				else:
					empty_lbls.add(stem)
		
		img_set = set(img_map.keys())
		lbl_set = set(lbl_map.keys())
		
		# set logic
		pair_keys = img_set & lbl_set
		only_img = img_set - lbl_set
		only_lbl = lbl_set - img_set
		
		# result
		result = [(img_map[k], lbl_map[k]) for k in pair_keys]

		isolation_report = {
			"missing_label": [lbl_map[k] for k in only_lbl],
			"missing_image": [img_map[k] for k in only_img],
			"empty_image": list(empty_imgs),
			"empty_label": list(empty_lbls),
		}
		
		return result, isolation_report

def parse_bbox(lbl_bytes: bytes) -> list[dict]:
	data = json.loads(lbl_bytes)
	labels = []
	for l in data:
		label = {
			"code_name" : l['Code Name'],
			"x_center" : float(l['Point(x,y)'].split(",")[0]),
			"y_center" : float(l['Point(x,y)'].split(",")[1]),
			"width" : float(l['W']),
			"height" : float(l['H'])
		}
		labels.append(label)
	return labels

def decode_filename(name: str) -> str:
	return name.encode('cp437').decode('cp949')

def data_generator(pairs, img_zip_obj, lbl_zip_obj, chunk_size):
	chunk = []
	for img_path, lbl_path in pairs:
		file_name = decode_path(img_path)
		img_bytes = img_zip_obj.read(img_path)
		label = parse_bbox(lbl_zip_obj.read(lbl_path))

		chunk.append((file_name, img_bytes, label))
		if len(chunk) >= chunk_size:
			yield chunk
			chunk = []
	if chunk:
		yield chunk

# ====== combine image and label ======
def extractor_task(file_keys, base_name, pipe_conf, sys_conf) -> Iterator[tuple[str, bytes]]:

	image_zip_path, label_zip_path = download_file(
		file_keys=file_keys,
		base_name=base_name,
		api_key=pipe_conf.source.aihub.api_key,
		project_key=pipe_conf.source.aihub.project_key,
		download_dir=sys_conf.download_dir
	)

	with zipfile.ZipFile(image_zip_path, "r") as img_z, \
		zipfile.ZipFile(label_zip_path, "r") as lbl_z:
		pairs, report = get_valid_pairs(img_z, lbl_z)

		try:
			yield from data_generator(pairs, img_z, lbl_z, pipe_conf.chunk_size)
		finally:
			if image_zip_path and image_zip_path.exists():
				image_zip_path.unlink()
			if label_zip_path and label_zip_path.exists():
				label_zip_path.unlink()