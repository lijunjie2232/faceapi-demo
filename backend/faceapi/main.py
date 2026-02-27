"""顔認識システムAPIのメインアプリケーションモジュール。

このモジュールはFastAPIアプリケーションを初期化し、ライフスパンイベントを設定し、
ミドルウェアを登録し、顔認識システムのすべてのAPIルートを含みます。
"""

import asyncio
from contextlib import asynccontextmanager
import uvicorn
from pathlib import Path
from loguru import logger
from workers import WorkerEntrypoint

from faceapi.core import _CONFIG_
from faceapi.routes import admin, face, user, session
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter


@asynccontextmanager
async def lifespan(_: FastAPI):
    """起動およびシャットダウンイベントのライフスパンイベントハンドラ"""
    # 起動イベント
    # await asyncio.gather(db_init())
    yield
    # シャットダウンイベント（もしあれば）


app = FastAPI(
    title=_CONFIG_.PROJECT_NAME,
    description="ユーザー管理機能付き顔認識システムのAPI",
    version="0.1.0",
    lifespan=lifespan,
)

# CORSミドルウェアを追加r
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CONFIG_.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define API routes first
# Using an APIRouter is the cleanest way to manage prefixes
api_router = APIRouter(prefix="/api/v1")

# 設定を使用してAPIルートを含める
api_router.include_router(user)
api_router.include_router(face)
api_router.include_router(admin)
api_router.include_router(session)

app.include_router(api_router)

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}

# 静的ファイルをサービスする
STATIC_ROOT = Path(_CONFIG_.STATIC_ROOT)
if STATIC_ROOT.is_dir():
    # Mount the Vue build directory (dist)
    # Ensure Vue app is built (npm run build)
    # This serves images, js, and css files
    app.mount("/assets", StaticFiles(directory=STATIC_ROOT/"assets"),
              name="assets",)
    app.mount("/models", StaticFiles(directory=STATIC_ROOT /
              "models"), name="models",)

    # Catch-all route for the Vue Router
    # This ensures that if a user refreshes on /dashboard,
    # FastAPI serves index.html instead of a 404.
    @app.get("/{full_path:path}")
    async def serve_vue_app(full_path: str):
        return FileResponse(STATIC_ROOT/"index.html")
    logger.info(f"Vueアプリ {STATIC_ROOT} がサービス準備完了です。")

else:
    logger.warning(
        "警告: 'dist' フォルダが見つかりません。まずVueアプリをビルドしてください。")

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        return await asgi.fetch(app, request.js_object, self.env)
        
# if __name__ == "__main__":
#     uvicorn.run(
#         app,
#         host=_CONFIG_.LISTEN_HOST,
#         port=_CONFIG_.LISTEN_PORT,
#     )
    
