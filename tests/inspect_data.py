import zipfile
import json

zip_json = '/home/lys/my-project/food-classification/tests/data/benchmarks/sample_val_302_json.zip'
zip_img = '/home/lys/my-project/food-classification/tests/data/benchmarks/tmp/INTER_LINEAR_webp_384_sample_val_302.zip'

print("Inspecting JSON...")
with zipfile.ZipFile(zip_json, 'r') as zf:
    json_names = [n for n in zf.namelist() if n.endswith('.json')]
    if json_names:
        print('Sample JSON file:', json_names[0])
        data = json.loads(zf.read(json_names[0]))
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])

print("\nInspecting Images...")
with zipfile.ZipFile(zip_img, 'r') as zf:
    img_names = [n for n in zf.namelist() if n.endswith('.webp')]
    if img_names:
        print('Sample Image file:', img_names[0])
