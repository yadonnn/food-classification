import zipfile
import json
from pathlib import Path
from typing import Iterator
from src.pipeline.downloader import download_file

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

def parse_aihub_label(json_bytes: bytes) -> list[dict]:
	raw_data = json.loads(json_bytes)
	objects = []
	for item in raw_data:
		point = item['Point(x,y)'].split(",")
		objects.append({
			"code_name": item['Code Name'],
			"class_name": item['Name'],
			"x_center": float(point[0]),
			"y_center": float(point[1]),
			"width": float(item['W']),
			"height": float(item['H'])
		})
	return objects

def decode_filename(name: str) -> str:
	return name.encode('cp437').decode('cp949')

def data_generator(tasks, img_zip_obj, lbl_zip_obj, chunk_size):
	chunk = []
	for img_path, label in tasks:
		img_bytes = img_zip_obj.read(img_path)
		objects = parse_aihub_label(lbl_zip_obj.read(label))

		chunk.append((img_bytes, objects))
		if len(chunk) >= chunk_size:
			yield chunk
			chunk = []
	if chunk:
		yield chunk

# ====== combine image and label ======
def extractor_task(file_keys, base_name, src_conf) -> Iterator[tuple[str, bytes]]:
	if src_conf.source_type == "aihub":
		image_zip_path, label_zip_path = download_file(
			file_keys=file_keys,
			base_name=base_name,
			api_key=src_conf.aihub.api_key,
			project_key=src_conf.aihub.project_key,
			download_dir=src_conf.raw_dir
		)
		is_temp_file = True

	elif src_conf.source_type == "local":
		image_zip_path = src_conf.local.src_zip_path
		label_zip_path = src_conf.local.label_zip_path
		is_temp_file = False


	label_dict = {}
	tasks = []
	if label_zip_path:
		with zipfile.ZipFile(label_zip_path, "r") as lbl_z:
			for lbl_name in lbl_z.namelist():
				if lbl_name.endswith(".json"):
					label_data = parse_aihub_label(lbl_z.read(lbl_name))
					code_name = label_data[0]["code_name"]
					label_dict[code_name] = label_data
		
	with zipfile.ZipFile(image_zip_path, "r") as img_z:
		for img_name in img_z.namelist():
			if img_name.endswith((".jpg", ".png", ".webp")):
				if img_name in label_dict:
					tasks.append((img_name, label_dict[code_name]))
					
		try:
			yield from data_generator(tasks, img_z, lbl_z, pipe_conf.chunk_size)
		finally:
			if is_temp_file:
				if image_zip_path and image_zip_path.exists():
					image_zip_path.unlink()
				if label_zip_path and label_zip_path.exists():
					label_zip_path.unlink()