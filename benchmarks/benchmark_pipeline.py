import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "image_pipeline"))
import argparse
import csv
import config
import preprocessor
import zipfile
# def run_benchmark(version: str, out: Path):
#     results = []
#     # ... 측정 로직
    
#     with open(out, 'w', newline='') as f:
#         writer = csv.DictWriter(f, fieldnames=["version", "stage", "workers", "elapsed"])
#         writer.writeheader()
#         writer.writerows(results)
DATA
def run_benchmark(test_file: Path):
	import timeit
	start_time = timeit.default_timer()
	file_list = preprocessor.extract_archive(test_file)
	elapsed_time = timeit.default_timer() - start_time
	print(f"Extract elapsed time: {elapsed_time:.2f}s")
	for file in file_list:
		start_time = timeit.default_timer()
		preprocessor.resize_image(file)
	elapsed_time = timeit.default_timer() - start_time
	print(f"Transform elapsed time: {elapsed_time:.2f}s")
	
	start_time = timeit.default_timer()
	preprocessor.make_archive(file_list)
	elapsed_time = timeit.default_timer() - start_time
	print(f"Make archive elapsed time: {elapsed_time:.2f}s")
	end_time = timeit.default_timer()
	print(f"Total elapsed time: {end_time - start_time:.2f}s")
if __name__ == "__main__":
	ROOT_DIR = Path(__file__).parent.parent
	test_file = ROOT_DIR / "tests" / "fixtures" / "sample.zip"
	run_benchmark(test_file)
		
	#=============================
	# argparse
	#=============================
	
	# parser = argparse.ArgumentParser()
	# parser.add_argument("--version", required=True)
	# parser.add_argument("--out", type=Path, default=Path("benchmarks/results/result.csv"))
	# args = parser.parse_args()

	# run_benchmark(version=args.version, out=args.out)
