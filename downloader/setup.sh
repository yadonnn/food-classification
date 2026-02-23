#!/bin/bash

# 1. 시스템 업데이트 및 필수 도구 설치
sudo apt update
sudo apt install -y software-properties-common curl git fontconfig
sudo apt-get install -y fonts-nanum
# 2. Python 3.11 설치
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# 3. 필수 시스템 라이브러리 (OpenCV용)
sudo apt install -y libgl1-mesa-glx libglib2.0-0

# 4. 가상환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# 5. AIHub Shell 다운로드 및 전역 실행 설정
curl -o "aihubshell" https://api.aihub.or.kr/api/aihubshell.do
chmod +x aihubshell
sudo cp aihubshell /usr/bin

# 5. Git 초기화 및 특정 폴더만 가져오기 (Sparse Checkout)
echo "🚀 Git 설정을 시작합니다..."

# 변수 설정 (본인의 레포 주소로 수정하세요)
REPO_URL="https://github.com/yadonnn/food-classification.git"

git init
# 이미 origin이 있을 경우를 대비해 기존 연결 삭제 후 추가
git remote remove origin 2>/dev/null
git remote add origin $REPO_URL

# sparse-checkout 활성화 및 downloader 폴더 지정
git sparse-checkout init --cone
git sparse-checkout set downloader

# 코드 가져오기
git pull origin main

# 6. 파이썬 패키지 설치 (requirements.txt가 있다면)
if [ -f "downloader/requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r downloader/requirements.txt
    echo "📦 라이브러리 설치 완료!"
fi
echo "✅ 모든 환경 세팅 및 코드 로드가 완료되었습니다!"