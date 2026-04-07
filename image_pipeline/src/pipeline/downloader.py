'''
aihubshell 이용 가이드: https://www.aihub.or.kr/devsport/apishell/list.do
'''
import subprocess
from pathlib import Path

def download_file(
        file_keys: str | int | list,
        base_name: str,
        api_key: str,
        project_key: str,
        download_dir: Path) -> Path:

    # file_keys가 리스트인 경우, 콤마로 연결해서 다중 다운로드
    if isinstance(file_keys, (str, int)):
        key_args = str(file_keys)
    else:
        key_args = ",".join(str(k) for k in file_keys if k)
        
    command = [
        "aihubshell",
        "-mode", "d",
        "-datasetkey", str(project_key),
        "-filekey", key_args,
        "-aihubapikey", str(api_key)
    ]
    subprocess.run(command, cwd=download_dir, check=True)

    # 해당 키로 다운로드된 .zip 파일을 찾습니다.
    image_path = next(download_dir.rglob(f"{base_name}.zip"), None)
    label_path = next(download_dir.rglob(f"{base_name}_json.zip"), None)
    if not image_path:
        raise FileNotFoundError(f"Missing image zip file: {base_name}.zip")
    if not label_path:
        print(f"[Warning] Missing label zip file: {base_name}_json.zip")

    return image_path, label_path