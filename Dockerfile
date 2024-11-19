# Python 베이스 이미지
FROM python:3.8-slim

# 작업 디렉토리 설정
WORKDIR /app

# 현재 디렉토리의 모든 파일을 컨테이너의 "/app" 디렉토리에 복사
COPY . /app

# Chrome 및 ChromeDriver 설치
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install \
    && apt-get clean

# Python 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt
