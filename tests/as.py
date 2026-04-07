"""
label collect
"""
import sys
import os
import csv
from pathlib import Path
import subprocess
import zipfile
import json
import random
import pickle
from collections import defaultdict, Counter
from dotenv import load_dotenv
sys.path.append(str(Path(__file__).parent.parent / "image_pipeline"))
load_dotenv(str(Path(__file__).parent.parent / "image_pipeline" / ".env"))

def download(file_keys, download_dir):
    subprocess.run(["aihubshell",
                    "-mode", "d", 
                    "-datasetkey", "242", 
                    "-filekey", file_keys, 
                    "-aihubapikey", str(os.getenv("AIHUB_API_KEY"))], 
                    cwd=download_dir, check=True)

def clean_class_name(class_name):
    class_name = class_name.replace("json", "")
    class_name = class_name.replace("/", "")
    class_name = class_name.replace("\'", "")
    class_name = class_name.replace(".", "")
    class_name = class_name.replace(" ", "")
    class_name = class_name.replace("{", "").replace("}", "")
    class_name = class_name.replace("라벨링데이터", "")
    class_name = class_name.replace("메쉬드포테이트", "메쉬드포테이토")
    class_name = class_name.strip()
    return class_name
def sampling(data, split_type, make_test:bool=False, max_size=1500):
    random.seed(42)

    if make_test:
        val_list = set()
        test_list = set()
    else:
        target_list = set()

    for cls, f_list in data[split_type].items():
        if len(f_list) > max_size:
            pool = random.sample(f_list, max_size)
        else:
            pool = f_list.copy()
            
        if make_test:
            random.shuffle(pool)

            half_idx = int(len(pool)//2)
            val_list.update(pool[:half_idx])
            test_list.update(pool[half_idx:])

        else:
            target_list.update(pool)
    
    if make_test:
        return val_list, test_list
    return target_list

def make_yolo_label(lbl_bytes: bytes) -> list[dict]:
	data = json.loads(lbl_bytes)
	labels = []
	for l in data:
		label = {
			"class_id" : 0,
			"x_center" : float(l['Point(x,y)'].split(",")[0]),
			"y_center" : float(l['Point(x,y)'].split(",")[1]),
			"width" : float(l['W']),
			"height" : float(l['H'])
		}
		labels.append(label)
	return labels

def make_dataset(label_path, label_bytes, split_type):
    yolo_label = make_yolo_label(label_bytes)
    file_name = Path(label_path).stem + ".txt"
    save_path = Path("labels") / split_type / file_name
    
    return save_path, yolo_label

def main():
    manifest_path = "./image_pipeline/manifests/download_list.csv"
    label_info = []
    with open(manifest_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if "json" in row[0]:
                label_info.append(row)
    full_size = 0
    file_keys = ",".join([row[2] for row in label_info])
    for file_name, size, file_key in label_info:
        size = int(size.replace(" MB", ""))
        full_size += size
    print(file_keys)

    # print(f"full_size: {full_size} MB")
    download_dir = Path(__file__).parent / "tmp" / "labels"
    download_dir.mkdir(parents=True, exist_ok=True)
    if not download_dir.exists():
        download(file_keys, download_dir)

    zip_paths = list(download_dir.rglob("*.zip"))
    
    class_names = set()
    label_info = {
        "train": defaultdict(int),
        "val": defaultdict(int)
    }
    zip_info = defaultdict(lambda: defaultdict(int))
    cls_to_files =  defaultdict(lambda: defaultdict(list))
    import os
    for zip_path in zip_paths:
        with zipfile.ZipFile(zip_path, 'r') as z:
            if "tra" in str(zip_path).lower():
                tra_or_val = "train"
            else:
                tra_or_val = "val"

            for i in z.infolist():
                if not i.is_dir():
                    name = i.filename.encode('cp437').decode('cp949')
                    dir_name, file_name = name.rsplit("/", 1)
                    class_name = clean_class_name(dir_name)
                    cls_to_files[tra_or_val][class_name].append(
                        (zip_path.name, i.filename)
                        )
                    label_info[tra_or_val][class_name] += 1
                    zip_info[zip_path.name][class_name] += 1
                    Cat_1 = file_name[1:3]
                    # category = dir_name.split("/")[-1]
                    print("Cat_1: ", file_name[1:3])
                    print("Cat_2: ", file_name[3:5])
                    print("Cat_3: ", file_name[5:7])
                    print("Cat_4: ", file_name[7:9])
    
    with open(Path("tests/output/cls_to_files.json"), "w") as f:
        json.dump(cls_to_files, f, indent=4, ensure_ascii=False)
    
    train_target_list = sampling(cls_to_files, "train", max_size=1500)
    val_target_list, test_target_list = sampling(cls_to_files, "val", make_test=True, max_size=300)

    train_set = []
    val_set = []
    test_set = []
    for zip_path in zip_paths:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for file_info in z.infolist():
                if file_info.is_dir():
                    continue
                
                identifier = (zip_path.name, file_info.filename)
                try:
                    if identifier in train_target_list:
                        train_set.append(make_dataset(file_info.filename,
                                                    z.read(file_info), 
                                                    "train"))
                    if identifier in val_target_list:
                        val_set.append(make_dataset(file_info.filename,
                                                    z.read(file_info), 
                                                    "val"))
                    if identifier in test_target_list:
                        test_set.append(make_dataset(file_info.filename,
                                                    z.read(file_info), 
                                                    "test"))
                except Exception as e:
                    error_list = {
                        "error": str(e),
                        "file_name": file_info.filename,
                        "zip_name": str(zip_path)
                    }
                    with open(Path("tests/output/error_list.json"), "a") as f:
                        json.dump(error_list, f, indent=4, ensure_ascii=False)
                    break
    
    with open(Path("tests/output/train_set.pkl"), "wb") as f:
        pickle.dump(train_set, f)
    with open(Path("tests/output/val_set.pkl"), "wb") as f:
        pickle.dump(val_set, f)
    with open(Path("tests/output/test_set.pkl"), "wb") as f:
        pickle.dump(test_set, f)
    with open(Path("tests/output/label_info.json"), "w") as f:
        json.dump(label_info, f, indent=4, ensure_ascii=False)
    with open(Path("tests/output/zip_info.json"), "w") as f:
        json.dump(zip_info, f, indent=4, ensure_ascii=False)
    # with open(Path("tests/output/label_info.csv"), "w") as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["total_n", "train_n", "val_n", "train_classes", "val_classes"])
    #     writer.writerow([label_info["total_n"], label_info["train_n"], label_info["val_n"], label_info["train_classes"], label_info["val_classes"]])
if __name__ == "__main__":
    # main()
    download("49596", Path("tests/tmp/labels"))