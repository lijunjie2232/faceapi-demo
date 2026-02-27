"""
顔認識システムの顔認識ルートモジュール。

このモジュールはアプリケーションの顔登録、認識、
検証機能のAPIエンドポイントを定義します。
"""

import logging
from traceback import print_exc

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from tortoise.transactions import atomic

from ..services.face import update_face_embedding_service, verify_face_service
from ..utils import get_current_user, get_current_session

router = APIRouter(
    prefix="/face",
    tags=["face"],
)
logger = logging.getLogger(__name__)


@router.post("/verify")
async def verify_face(
    image: UploadFile = File(...),
    current_ip: str = Depends(get_current_session)
):
    """
    アップロードされた画像から顔を検証し、拒否結果またはOAuth2トークンを返します。

    引数:
        image: 顔を含むアップロードされた画像ファイル

    戻り値:
        顔が認識された場合は拒否メッセージまたはOAuth2トークン
    """
    try:
        result = await verify_face_service(image, current_ip)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print_exc()
        logger.error("顔検証エラー: %s", str(e))
        raise e


@atomic()
@router.put("/me", dependencies=[Depends(get_current_user)])
async def update_face_embedding(
    image: UploadFile = File(...), 
    current_user: str = Depends(get_current_user),
    current_ip: str = Depends(get_current_session)
):
    """
    現在認証されているユーザーの顔埋め込みを更新します。
    ユーザーAPIと同様にOAuth2認証が必要です。

    引数:
        image: 新しい顔を含むアップロードされた画像ファイル
        current_user: 現在認証されているユーザー（JWTトークンから）

    戻り値:
        埋め込みが更新されたことを示す成功メッセージ
    """
    try:
        # トークンからユーザーIDを取得
        user_id = int(current_user)

        result = await update_face_embedding_service(user_id, image, current_ip)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print_exc()
        logger.error("顔埋め込み更新エラー: %s", str(e))
        raise e
