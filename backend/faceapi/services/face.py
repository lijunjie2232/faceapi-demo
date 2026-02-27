"""
顔認識システムの顔サービスモジュール。

このモジュールは顔検証と埋め込み更新を含む
顔認識操作のビジネスロジックを含みます。
"""

import time
from typing import Any, Dict

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile
from loguru import logger

from ..core import _CONFIG_, _SESSION_MANAGER_
from ..face_rec import _MODEL_ as model
from ..utils import create_access_token, detect_face, image_to_base64

from ..utils import inference

async def verify_face_service(image: UploadFile, current_ip: str) -> Dict[str, Any]:
    """
    アップロードされた画像から顔を検証するサービス関数。

    引数:
        image: 顔を含むアップロードされた画像ファイル
        current_ip: 当前会话的IP地址

    戻り値:
        認识結果と成功時のトークンを含む辞書
    """
    # 画像ファイルを読み込み
    contents = await image.read()

    # numpy配列に変換
    nparr = np.frombuffer(contents, np.uint8)
    # pylint: disable=no-member
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # pylint: enable=no-member

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # 画像内の顔を検出
    detected_faces = detect_face(img)

    if not detected_faces:
        return {
            "recognized": False,
            "message": "No face detected in the image",
            "data": {
                "token": None,
                "token_type": "Bearer",
            },
            "code": 400,
        }

    # 顔から特徴を抽出
    features = [
        inference(face_img)[0]
        for face_img in detected_faces
    ]

    # 通过会话管理器获取SQL实例
    sql_client = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_client:
        raise HTTPException(status_code=401, detail="Invalid session")

    # 在用户嵌入向量中搜索相似的顔
    search_results = await sql_client.search_face_embeddings(
        query_vector=features[0].tolist(),
        limit=1,
        threshold=_CONFIG_.MODEL_THRESHOLD
    )
    if not any(search_results):
        # 一致する顔が見つからない
        return {
            "recognized": False,
            "message": "Face not recognized in the database",
            "data": {
                "token": None,
                "token_type": "Bearer",
            },
            "code": 401,
        }

    # 最良の一致を取得
    # best_match = search_results[0][0]
    best_match = list(filter(lambda l: len(l) > 0, search_results))[0][0]

    # 顔が認識され、ユーザー情報を取得しトークンを作成
    user_id = best_match["entity"]["user_id"]

    # アクセストークンを作成
    access_token = create_access_token(
        data={"sub": str(user_id)},
    )

    return {
        "recognized": True,
        "message": f"Face recognized as user(id={user_id})",
        "user_id": user_id,
        "confidence": 1 - best_match["distance"],  # 距離を類似度に変換
        "data": {
            "token": access_token,
            "token_type": "Bearer",
        },
        "code": 200,
    }


async def update_face_embedding_service(
    user_id: int, image: UploadFile, current_ip: str
) -> Dict[str, Any]:
    """
    ユーザーの顔埋め込みを更新するサービス関数。

    引数:
        user_id: 顔埋め込みを更新するユーザーのID
        image: 新しい顔を含むアップロードされた画像ファイル
        current_ip: 当前会话的IP地址

    戻り値:
        成功メッセージと埋め込みIDを含む辞書
    """
    # 画像ファイルを読み込み
    contents = await image.read()

    # numpy配列に変換
    nparr = np.frombuffer(contents, np.uint8)
    # pylint: disable=no-member
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # pylint: enable=no-member

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # 通过会话管理器获取SQL实例
    sql_client = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_client:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # 获取用户对象
    user_dict = await sql_client.get_user_by_id(user_id)
    if not user_dict:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 直接使用用户字典，通过sql_client进行操作
    user = user_dict

    # 画像内の顔を検出
    detected_faces = detect_face(img)

    if not detected_faces:
        raise HTTPException(status_code=400, detail="No face detected in the image")

    if len(detected_faces) > 1 and _CONFIG_.ALLOW_FACE_DEDUPICATION:
        raise HTTPException(
            status_code=400,
            detail="Multiple faces detected. Please upload an image with only one face.",
        )

    # 最初に検出された顔を処理
    face_img = detected_faces[0]

    # 顔から特徴を抽出
    features = inference(face_img)

    # 在用户嵌入向量中搜索相似的顔
    search_results = await sql_client.search_face_embeddings(
        query_vector=features[0].tolist(),
        limit=1,
        threshold=_CONFIG_.MODEL_THRESHOLD
    )
    if any(search_results) and not _CONFIG_.ALLOW_FACE_DEDUPICATION:
        if search_results[0][0]["entity"]["user_id"] != user_id:
            raise HTTPException(
                status_code=400,
                detail="Face already exists in the database. Please use a different face or contact the administrator.",
            )

    # 更新用户的人脸嵌入向量
    insert_result = await sql_client.upsert_face_embedding(
        user_id=user_id,
        feature_vector=features[0].tolist()
    )

    # Milvusクライアントからの応答の可能性のあるバリエーションを処理
    inserted_id = None
    if isinstance(insert_result, dict):
        # 応答内の異なる可能なキーを確認
        if "insertedIds" in insert_result:
            inserted_id = (
                insert_result["insertedIds"][0]
                if insert_result["insertedIds"]
                else None
            )
        elif "inserted_ids" in insert_result:
            inserted_id = (
                insert_result["inserted_ids"][0]
                if insert_result["inserted_ids"]
                else None
            )
    elif hasattr(insert_result, "inserted_ids"):
        inserted_id = (
            insert_result.inserted_ids[0] if insert_result.inserted_ids else None
        )

    # 直接使用SQL客户端更新用户头像（更稳定的方式）
    head_pic_data = image_to_base64(img)
    await sql_client.update_user(user_id, head_pic=head_pic_data)
    logger.debug("ユーザーのhead_picがSQLクライアント経由で更新されました")

    return {
        "success": True,
        "message": f"Face embedding updated successfully for user ID {user_id}",
        "new_embedding_id": inserted_id,
    }
