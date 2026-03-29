import zipfile
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

def visualize_bbox(json_zip_path: str, img_zip_path: str, output_dir: str):
    """
    Reads a label JSON and its corresponding Image from zip files,
    draws the bounding boxes, and saves the output.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(json_zip_path, 'r') as zf_json:
        json_names = [n for n in zf_json.namelist() if n.endswith('.json')]
        if not json_names:
            print("No JSON found.")
            return
            
        sample_json_name = json_names[0]
        data = json.loads(zf_json.read(sample_json_name))
        
        base_name = Path(sample_json_name).stem
        print(f"Loaded label for: {base_name}")
        
    with zipfile.ZipFile(img_zip_path, 'r') as zf_img:
        img_names = [n for n in zf_img.namelist() if Path(n).stem == base_name]
        if not img_names:
            print(f"No corresponding image found for {base_name}.")
            return
            
        sample_img_name = img_names[0]
        with zf_img.open(sample_img_name) as file:
            img = Image.open(file)
            img = img.convert('RGB')
            draw = ImageDraw.Draw(img)
            
            img_w, img_h = img.size
            
            for item in data:
                point_str = item.get("Point(x,y)", "0,0")
                try:
                    x_norm, y_norm = map(float, point_str.split(','))
                    w_norm = float(item.get("W", "0"))
                    h_norm = float(item.get("H", "0"))
                except ValueError:
                    continue
                
                # Convert normalized coordinates to pixel values
                # If Point(x,y) represents the top-left coordinate:
                x1 = x_norm * img_w
                y1 = y_norm * img_h
                x2 = (x_norm + w_norm) * img_w
                y2 = (y_norm + h_norm) * img_h
                
                # Draw rectangle and label text
                draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
                label_name = item.get("Name", "Unknown")
                draw.text((x1, max(y1-15, 0)), label_name, fill="red")
            
            out_path = Path(output_dir) / f"{base_name}_visualized.jpg"
            img.save(out_path)
            print(f"Saved visualization to {out_path}")

def test_visualize_bbox():
    json_zip = '/home/lys/my-project/food-classification/tests/data/benchmarks/sample_val_302_json.zip'
    img_zip = '/home/lys/my-project/food-classification/tests/data/benchmarks/tmp/INTER_LINEAR_webp_384_sample_val_302.zip'
    out_dir = '/home/lys/my-project/food-classification/tests/output'
    
    visualize_bbox(json_zip, img_zip, out_dir)

if __name__ == "__main__":
    test_visualize_bbox()
