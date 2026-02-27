"""
顔認識システムの管理者ルートモジュール。

このモジュールはユーザーのリスト表示、作成、更新、削除を含む
ユーザー管理の管理APIエンドポイントを定義します。
"""

import logging
from traceback import print_exc
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from tortoise.transactions import atomic

from ..models import UserModel
from ..schemas import (
    BatchOperationRequest,
    BatchOperationResult,
    DataResponse,
    ListResponse,
    User,
    UserCreateAsAdmin,
    UserUpdateAsAdmin,
)
from ..services import (
    batch_activate_users_service,
    batch_deactivate_users_service,
    batch_reset_face_data_service,
    batch_reset_password_service,
    create_user_as_admin_service,
    get_user_service,
    list_users_service,
    update_face_embedding_service,
    update_user_as_admin_service,
    validate_user_update_uniqueness,
)
from ..utils import get_current_admin_user, get_current_session

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)
logger = logging.getLogger(__name__)


@router.get(
    "/users",
    response_model=ListResponse[User],
    dependencies=[Depends(get_current_admin_user)],
)
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    username: Optional[str] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    set_face: Optional[bool] = None,
    current_ip: str = Depends(get_current_session)
):
    """ページネーションとオプションフィルターで全ユーザーをリスト表示する管理者エンドポイント"""
    try:
        limit = min(100, max(limit, 1))
        users, count = await list_users_service(
            current_ip,
            skip,
            limit,
            username,
            email,
            full_name,
            is_active,
            is_admin,
            set_face,
        )

        return ListResponse[User](
            success=True,
            message="ユーザーが正常に取得されました",
            code=200,
            data=users,
            total=count,
            page=(skip // limit) + 1 if limit > 0 else 1,
            size=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ユーザー一覧取得中にエラーが発生しました: {str(e)}",
        ) from e


@router.get(
    "/users/{user_id}",
    response_model=DataResponse[User],
    dependencies=[Depends(get_current_admin_user)],
)
async def get_user_by_id(
    user_id: int,
    current_ip: str = Depends(get_current_session)
):
    """IDで特定のユーザーを取得する管理者エンドポイント"""
    try:
        user = await get_user_service(current_ip, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

        user_response = User(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            is_active=user['is_active'],
            created_at=user['created_at'],
            updated_at=user['updated_at'],
            head_pic=user['head_pic'],
            is_admin=user['is_admin'],
        )

        return DataResponse[User](
            success=True,
            message="ユーザーが正常に取得されました",
            code=200,
            data=user_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ユーザー取得中にエラーが発生しました: {str(e)}",
        ) from e


@router.post(
    "/users",
    response_model=DataResponse[User],
    dependencies=[Depends(get_current_admin_user)],
)
async def create_user_as_admin(
    user_create: UserCreateAsAdmin,
    current_ip: str = Depends(get_current_session)
):
    """新しいユーザーを作成する管理者エンドポイント"""
    try:
        # ユーザーが既に存在するか確認
        existing_user = await get_user_service(current_ip, username=user_create.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="ユーザー名は既に使用されています",
            )

        existing_email = await get_user_service(current_ip, email=user_create.email)
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="メールアドレスは既に登録されています",
            )

        # サービス経由でユーザーを作成
        created_user = await create_user_as_admin_service(user_create, current_ip)

        # レスポンス形式に変換
        user_response = User(
            id=created_user['id'],
            username=created_user['username'],
            email=created_user['email'],
            full_name=created_user['full_name'],
            is_active=created_user['is_active'],
            created_at=created_user['created_at'],
            updated_at=created_user['updated_at'],
            head_pic=created_user['head_pic'],
            is_admin=created_user['is_admin'],
        )

        return DataResponse[User](
            success=True,
            message="ユーザーが正常に作成されました",
            code=200,
            data=user_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400 if "already" in str(e) or "duplicate" in str(e) else 500,
            detail=f"ユーザー作成中にエラーが発生しました: {str(e)}",
        ) from e


@router.put(
    "/users/{user_id}",
    response_model=DataResponse[User],
    dependencies=[Depends(get_current_admin_user)],
)
async def update_user_as_admin(
    user_id: int,
    user_update: UserUpdateAsAdmin,
    current_admin: UserModel = Depends(get_current_admin_user),
    current_ip: str = Depends(get_current_session)
):
    """IDで特定のユーザーを更新する管理者エンドポイント"""
    try:
        # ユーザーを取得して存在を確認
        user = await get_user_service(current_ip, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

        if user_id == current_admin['id']:
            # 現在のユーザーが管理者であっても、自分自身のアクティブ/非アクティブ変更は許可されません
            if user_update.is_active is not None:
                raise HTTPException(status_code=400, detail="自分のステータスは変更できません")

        # ユーザー名とメールアドレスの一意性を検証
        validation_error = await validate_user_update_uniqueness(user_id, user_update, current_ip)
        if validation_error:
            raise HTTPException(status_code=400, detail=validation_error)

        # サービス経由でユーザーを更新
        updated_user = await update_user_as_admin_service(user_id, user_update, current_ip)

        user_response = User(
            id=updated_user['id'],
            username=updated_user['username'],
            email=updated_user['email'],
            full_name=updated_user['full_name'],
            is_active=updated_user['is_active'],
            created_at=updated_user['created_at'],
            updated_at=updated_user['updated_at'],
            head_pic=updated_user['head_pic'],
            is_admin=updated_user['is_admin'],
        )

        return DataResponse[User](
            success=True,
            message="ユーザーが正常に更新されました",
            code=200,
            data=user_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400 if "already" in str(e) or "duplicate" in str(e) else 500,
            detail=f"ユーザー更新中にエラーが発生しました: {str(e)}",
        ) from e


@atomic()
@router.post(
    "/batch/{operation}",
    response_model=DataResponse[BatchOperationResult],
    dependencies=[Depends(get_current_admin_user)],
)
async def batch_operation(
    operation: str,
    batch_request: BatchOperationRequest,
    current_admin: UserModel = Depends(get_current_admin_user),
    current_ip: str = Depends(get_current_session)
):
    """
    複数のユーザーに対してバッチ操作を実行する管理者エンドポイント。

    サポートされる操作:
    - reset-password: パスワードを指定した値にリセット
    - active: ユーザーアカウントをアクティブ化
    - inactive: ユーザーアカウントを非アクティブ化
    - reset-face: 顔データを未設定にリセット

    引数:
        operation: 実行する操作
        batch_request: user_idsとオプション値を含むリクエスト
        current_admin: 現在の管理者ユーザー（依存関係）

    戻り値:
        成功/失敗統計を含むBatchOperationResult
    """
    # 操作を検証
    valid_operations = ["reset-password", "active", "inactive", "reset-face"]
    if operation not in valid_operations:
        raise HTTPException(
            status_code=400,
            detail=f"無効な操作です。有効な操作は: {valid_operations}",
        )

    # user_idsを検証
    if not batch_request.user_ids:
        raise HTTPException(status_code=400, detail="user_idsリストは空にできません")

    # 自己操作制限を確認
    if current_admin['id'] in batch_request.user_ids:
        raise HTTPException(
            status_code=400, detail="バッチ操作に自分のアカウントを含めることはできません"
        )

    # 値の要件を検証
    if operation == "reset-password" and not batch_request.value:
        raise HTTPException(
            status_code=400, detail="パスワードリセット操作には値が必要です"
        )

    try:
        # 要求された操作を実行
        if operation == "reset-password":
            # reset-password操作のために値が存在することを検証済み
            if not batch_request.value:
                raise HTTPException(
                    status_code=400,
                    detail="パスワードリセット操作には値が必要です",
                )
            result = await batch_reset_password_service(
                batch_request.user_ids, batch_request.value, current_ip
            )
        elif operation == "active":
            result = await batch_activate_users_service(batch_request.user_ids, current_ip)
        elif operation == "inactive":
            result = await batch_deactivate_users_service(batch_request.user_ids, current_ip)
        elif operation == "reset-face":
            result = await batch_reset_face_data_service(batch_request.user_ids, current_ip)
        else:
            # 上記の検証により発生すべきではないが、完全性のために追加
            raise HTTPException(status_code=500, detail="サポートされていない操作です")

        return DataResponse[BatchOperationResult](
            success=True,
            message=f"バッチ {operation} 操作が完了しました",
            code=200,
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"バッチ操作実行中にエラーが発生しました: {str(e)}",
        ) from e


# 管理者として任意のユーザーの顔を更新
@atomic()
@router.put(
    "/face/{user_id}",
    dependencies=[Depends(get_current_admin_user)],
)
async def update_face_embedding_as_admin(
    user_id: int,
    image: UploadFile = File(...),
    current_ip: str = Depends(get_current_session)
):
    """
    指定されたユーザーの顔埋め込みを管理者として更新。
    このエンドポイントにより管理者は特定のユーザーの顔埋め込みを更新できます。
    既存の顔埋め込みサービスを使用しますが、管理者レベルの検証とエラー処理を追加します。

    引数:
        user_id (int): 顔埋め込みを更新するユーザーのID
        image (UploadFile): ユーザーの顔を含むアップロードされた画像

    戻り値:
        埋め込みが更新されたことを示す成功メッセージ
    """
    try:
        result = await update_face_embedding_service(user_id, image, current_ip)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print_exc()
        logger.error("顔埋め込み更新エラー: %s", str(e))
        raise e
