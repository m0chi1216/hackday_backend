# Python公式イメージを使用（マルチステージビルド）
FROM python:3.11-slim as builder

# 作業ディレクトリを設定
WORKDIR /app

# システム依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 本番用イメージ
FROM python:3.11-slim

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app

# 作業ディレクトリを設定
WORKDIR /app

# builderステージからPythonパッケージをコピー
COPY --from=builder /root/.local /home/app/.local

# アプリケーションコードをコピー
COPY . .

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
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
