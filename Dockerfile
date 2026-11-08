# Python 3.11 슬림 리눅스 베이스 이미지
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=5000

# 1. 필수 리눅스 패키지 및 LibreOffice, 한글 폰트 설치
# fonts-nanum, fonts-noto-cjk: 한글 깨짐(네모 박스) 방지를 위한 필수 글꼴
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-impress \
    libreoffice-writer \
    fonts-nanum \
    fonts-noto-cjk \
    fonts-liberation \
    fonts-dejavu-core \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉터리 설정
WORKDIR /app

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 5000

# Gunicorn 프로덕션 서버 실행 (100MB 파일 및 5분 타임아웃 지원)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 300 app:app
