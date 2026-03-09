#!/bin/bash
# setup.sh - 초기 환경 구축용

echo "Phase 1: 시스템 및 AIHub Shell 구성 중..."
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev git curl

# 1. AIHub Shell 설치
curl -o "aihubshell" https://api.aihub.or.kr/api/aihubshell.do
chmod +x aihubshell
sudo cp aihubshell /usr/bin

# 2. .env 템플릿 생성 (없을 경우에만)
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️ .env 생성완료. API Key를 입력해주세요."
    fi
fi

echo "✅ 시스템 셋업 완료! 이제 'uv sync' 후 'uv run -m image_pipeline.main'으로 파이프라인을 실행하세요."