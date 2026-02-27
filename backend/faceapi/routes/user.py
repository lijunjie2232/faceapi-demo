"""
顔認識システムのユーザールートモジュール。

このモジュールは認証、プロフィール管理、アカウント操作を含む
ユーザー管理のAPIエンドポイントを定義します。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..schemas import DataResponse, User, UserCreate, UserUpdate
from ..services.user import (
    authenticate_user,
    create_user_service,
    delete_user_account_service,
    get_current_user_profile_service,
    update_user_profile_service,
)
from ..utils import create_access_token, get_current_user, get_current_session

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.post("/login", response_model=DataResponse[dict])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    current_ip: str = Depends(get_current_session),
):
    """認証成功時にJWTトークンを返すログインエンドポイント"""
    try:
        user = await authenticate_user(form_data.username, form_data.password, current_ip)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザー名またはパスワードが正しくありません",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # アクセストークンを作成
        access_token = create_access_token(
            data={"sub": str(user['id'])},  # ユーザーIDをサブジェクトとして使用
        )

        token_data = {
            "token": access_token,
            "token_type": "Bearer",
        }

        return DataResponse[dict](
            success=True,
            message="ログイン成功",
            code=200,
            data=token_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"ログイン中にエラーが発生しました: {str(e)}"
        ) from e


@router.post("/signup", response_model=DataResponse[User])
async def create_user(user: UserCreate, current_ip: str = Depends(get_current_session)):
    """新しいユーザーアカウントを作成"""
    try:
        # サービス経由でユーザーを作成
        created_user = await create_user_service(user, current_ip)

        # レスポンス形式に変換
        user_response = User(
            id=created_user['id'],
            username=created_user['username'],
            email=created_user['email'],
            full_name=created_user['full_name'],
            is_active=created_user['is_active'],
            created_at=created_user['created_at'],
            updated_at=created_user['updated_at'],
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
            status_code=400 if "already" in str(e) else 500,
            detail=f"ユーザー作成中にエラーが発生しました: {str(e)}",
        ) from e


@router.get("/me", response_model=DataResponse[User])
async def get_current_user_profile(
    current_user: str = Depends(get_current_user),
    current_ip: str = Depends(get_current_session),
):
    """認証トークンに基づいて現在のユーザーのプロフィールを取得"""
    try:
        user_id = int(current_user)

        user = await get_current_user_profile_service(user_id, current_ip)

        return DataResponse[User](
            success=True, message="プロフィールが正常に取得されました", code=200, data=user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"プロフィール取得中にエラーが発生しました: {str(e)}"
        ) from e


@router.put("/me", response_model=DataResponse[User])
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: str = Depends(get_current_user),
    current_ip: str = Depends(get_current_session),
):
    """認証トークンに基づいて現在のユーザーのプロフィールを更新"""
    try:
        user_id = int(current_user)

        # サービス経由でユーザーを更新
        updated_user_obj = await update_user_profile_service(user_id, user_update, current_ip)

        updated_user = User(
            id=updated_user_obj['id'],
            username=updated_user_obj['username'],
            email=updated_user_obj['email'],
            full_name=updated_user_obj['full_name'],
            is_active=updated_user_obj['is_active'],
            created_at=updated_user_obj['created_at'],
            updated_at=updated_user_obj['updated_at'],
            # head_pic=updated_user_obj.head_pic,
            is_admin=updated_user_obj['is_admin'],
        )

        return DataResponse[User](
            success=True,
            message="プロフィールが正常に更新されました",
            code=200,
            data=updated_user,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400 if "already" in str(e) else 500,
            detail=f"プロフィール更新中にエラーが発生しました: {str(e)}",
        ) from e


@router.delete("/me", response_model=DataResponse[bool])
async def delete_current_user_account(
    current_user: str = Depends(get_current_user),
    current_ip: str = Depends(get_current_session),
):
    """認証トークンに基づいて現在のユーザーのアカウントを削除"""
    try:
        user_id = int(current_user)

        # サービス経由でユーザーアカウントを削除
        success = await delete_user_account_service(user_id, current_ip)

        return DataResponse[bool](
            success=True,
            message="アカウントが正常に無効化されました",
            code=200,
            data=success,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"アカウント削除中にエラーが発生しました: {str(e)}",
        ) from e
