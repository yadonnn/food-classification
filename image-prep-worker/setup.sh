#!/bin/bash
# setup.sh - 초기 환경 구축용

echo "Phase 1: 시스템 및 AIHub Shell 구성 중..."
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev git curl

# 1. AIHub Shell 설치
curl -o "aihubshell" https://api.aihub.or.kr/api/aihubshell.do
chmod +x aihubshell
sudo cp aihubshell /usr/bin

# 2. 파이썬 가상환경 및 라이브러리 설치
echo "Phase 2: 파이썬 가상환경 생성 및 라이브러리 설치..."
python3.11 -m venv .venv_food
source .venv_food/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. .env 템플릿 생성 (없을 경우에만)
if [ ! -f ".env.example" ]; then
    cp .env.example .env
    echo "⚠️ .env 생성완료. API Key를 입력해주세요."
fi

echo "✅ 셋업 완료! 이제 'python main.py'로 파이프라인을 실행하세요."