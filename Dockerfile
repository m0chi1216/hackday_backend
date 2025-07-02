# Python公式イメージを使用（マルチステージビルド）
FROM python:3.11-slim as builder

# 作業ディレクトリを設定
WORKDIR /app

# システム依存関係をインストール（Node.jsも含む）
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 本番用イメージ
FROM python:3.11-slim

# Node.jsをインストール
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app

# 作業ディレクトリを設定
WORKDIR /app

# builderステージからPythonパッケージをコピー
COPY --from=builder /root/.local /home/app/.local

# アプリケーションコードをコピー
COPY main/ ./main/
COPY *.py ./
COPY requirements.txt ./

# Node.jsファイルをコピー
COPY nodejs/ ./nodejs/

# Node.js依存関係をインストール（本番ステージで実行）
WORKDIR /app/nodejs
RUN echo "=== Installing Node.js dependencies ===" && \
    ls -la && \
    cat package.json && \
    npm install --production && \
    echo "=== Installation completed ===" && \
    ls -la node_modules/ && \
    echo "=== Checking riichi module ===" && \
    ls -la node_modules/riichi/ || echo "riichi module not found"
WORKDIR /app

# ファイルの所有者を変更
RUN chown -R app:app /app

# 非rootユーザーに切り替え
USER app

# PATHにユーザーのlocalを追加
ENV PATH=/home/app/.local/bin:$PATH

# ポートを公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# アプリケーションを起動
CMD ["uvicorn", "main.main:app", "--host", "0.0.0.0", "--port", "8000"]
