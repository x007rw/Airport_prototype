FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# 対話型プロンプトを無効化
ENV DEBIAN_FRONTEND=noninteractive

# 1. コンパイル環境、GUI依存、確認ツールのインストール
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    git \
    procps \
    xvfb \
    x11vnc \
    fluxbox \
    python3-tk \
    python3-dev \
    build-essential \
    libx11-dev \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/Airport

# 2. Pythonパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Playwrightブラウザ本体のインストール
RUN python3 -m playwright install chromium
RUN python3 -m playwright install-deps chromium

COPY . .

# 権限の付与
RUN chmod +x entrypoint.sh

# 起動
CMD ["./entrypoint.sh"]