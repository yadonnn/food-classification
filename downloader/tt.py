import re
import csv
import subprocess
# 1. 트리 기호를 무시하고 파일명/용량/키를 뽑는 정규식
# 한글 파일명과 언더바를 모두 잡기 위해 [^\s│├─└─]+ 패턴을 사용합니다.

def convert_tree_to_csv(input_file, output_file):
    pattern = re.compile(r'([^\s│├─└─]+\.zip)\s*\|\s*([0-9]+\s*[A-Z]+)\s*\|\s*([0-9]+)')
    matches = pattern.findall(input_file)
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['파일명', '용량', '파일키']) # 헤더
        writer.writerows(matches)
    
    print(f"✨ 변환 완료! 총 {len(matches)}개의 파일을 찾았습니다.")
if __name__ == "__main__":
    # capture_output=True를 추가하여 stdout을 변수에 담습니다.
    result = subprocess.run(f"aihubshell -mode l -datasetkey 242", shell=True, text=True, capture_output=True)
    output_file = "test.csv"
    if result.stdout:
        convert_tree_to_csv(result.stdout, output_file)
    else:
        print("❌ aihubshell 출력 결과가 없습니다.")