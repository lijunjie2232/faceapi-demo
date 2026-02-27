# マルチステージビルドを使用してイメージサイズを最適化
# ステージ1: フロントエンドのビルド
FROM node:24 AS frontend-builder

# 作業ディレクトリの設定
WORKDIR /app

# フロントエンド依存関係のコピーとインストール
COPY frontend/package*.json ./
RUN npm ci --only=production && npm cache clean --force

# フロントエンドソースコードのコピー
COPY frontend/ .

# モデルファイルのダウンロードスクリプトを実行
RUN npm run build

# ステージ2: バックエンドのビルド
FROM python:3.12 AS backend-builder

# 必要なシステム依存関係のインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定
WORKDIR /app

# Python依存関係のインストール
COPY backend ./backend
RUN pip install -U setuptools
RUN pip install --no-cache-dir -e ./backend

# バックエンドソースコードのコピー


# フロントエンドのビルド成果物をバックエンドにコピー
COPY --from=frontend-builder /app/dist /app/frontend/dist

# 最終ステージ: 本番用イメージ
FROM python:3.12

# ラベルの設定
LABEL maintainer="face-recognition-demo"
LABEL description="顔認識システムデモアプリケーション"

# 必要なシステム依存関係のインストール
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    ffmpeg \
    libgl1 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 非rootユーザーの作成（セキュリティ対策）
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 作業ディレクトリの作成と権限設定
WORKDIR /app
RUN chown -R appuser:appuser /app

# ビルド済みのアプリケーションファイルをコピー
COPY --from=backend-builder --chown=appuser:appuser /app /app

RUN wget https://github.com/lijunjie2232/faceapi/releases/download/v0.1/model_s3_v1.onnx -O /app/model.onnx

# ポートの公開
EXPOSE 8000

# 環境変数の設定
ENV PYTHONPATH=/app
ENV STATIC_ROOT=/app/frontend/dist
ENV USE_MEMORY_DB=true
ENV LISTEN_HOST=0.0.0.0
ENV LISTEN_PORT=8000
ENV MODEL_PATH=/app/model.onnx
ENV MODEL_LOADER=onnx
ENV MODEL_THRESHOLD=0.2285
ENV MODEL_DEVICE=cpu
ENV MODEL_EMB_DIM=512
ENV API_V1_STR=/api/v1
ENV PROJECT_NAME="Face Recognition System Demo"
ENV LISTEN_HOST=0.0.0.0
ENV LISTEN_PORT=8000
ENV ALLOWED_ORIGINS=["*"]
ENV SECRET_KEY=a9a07e8523a927f519e42897e11d821315c810832b73cb82bd94f9411ff854a5
ENV ALGORITHM=HS256
ENV ACCESS_TOKEN_EXPIRE_MINUTES=5
ENV PASSWORD_HASH_ALGORITHM=sha256_crypt
ENV ADMIN_USERNAME=admin
ENV ADMIN_PASSWORD=admin123
ENV ADMIN_EMAIL=admin@example.com
ENV ADMIN_FULL_NAME="Demo Administrator"
ENV STRICT_MODE=false
ENV ALLOW_FACE_DEDUPICATION=false
ENV USE_MEMORY_DB=true
ENV SESSION_ID_EXPIRE_SECONDS=300

# ヘルスチェックの設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 非rootユーザーに切り替え
USER appuser

# コンテナ起動時のコマンド
CMD ["uvicorn", "faceapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
