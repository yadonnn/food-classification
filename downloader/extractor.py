import os
import zipfile

EXTRACT_DIR = "data/extracted/"

def extract_worker(zip_queue, folder_queue):
    """
    앞 단계(다운로드 워커)에서 생성된 ZIP 파일의 절대경로를 받아
    압축을 풀고 원본 ZIP 코어 파일을 삭제합니다.
    이후 해제된 폴더의 절대경로를 folder_queue에 넣습니다.
    """
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    while True:
        zip_path = zip_queue.get()
        if zip_path is None:
            print("압축 해제 워커: 종료 신호 수신")
            folder_queue.put(None)
            break
            
        print(f"📦 압축 해제 시작: {zip_path}")
        
        # 고유 폴더명 설정
        base_name = os.path.basename(zip_path)
        folder_name = os.path.splitext(base_name)[0]
        target_folder = os.path.abspath(os.path.join(EXTRACT_DIR, folder_name))
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_folder)
            
            print(f"✅ 압축 해제 완료: {target_folder}")
            
            # [중요] 삭제 로직 1: 압축 해제가 완전히 끝나면 원본 ZIP 코어 파일 삭제
            try:
                os.remove(zip_path)
                print(f"🗑️ 원본 ZIP 삭제 완료: {zip_path}")
            except Exception as e:
                print(f"❌ 원본 ZIP 삭제 실패: {e}")
                
            # 해제된 디렉토리 경로를 folder_queue에 넣습니다.
            folder_queue.put(target_folder)
            
        except zipfile.BadZipFile as e:
            print(f"❌ 올바른 ZIP 파일이 아닙니다 ({zip_path}): {e}")
        except Exception as e:
            print(f"❌ 압축 해제 중 오류 발생: {e}")
