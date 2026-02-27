"""
認証用のJWTトークンの作成と検証のためのJWTユーティリティモジュール。
"""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from ..core import _CONFIG_, _SESSION_MANAGER_
from ..utils.session_utils import get_current_session

# トークン認証のためのOAuth2スキーム
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{_CONFIG_.API_V1_STR}/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    指定されたデータと有効期限でJWTアクセストークンを作成。

    引数:
        data: トークンに含めるデータ
        expires_delta: トークンのオプション有効期限

    戻り値:
        エンコードされたJWTトークン
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=_CONFIG_.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    # 設定から明示的にHS256アルゴリズムを使用
    encoded_jwt = jwt.encode(
        to_encode, _CONFIG_.JWT_SECRET_KEY, algorithm=_CONFIG_.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    提供されたトークンから現在認証されているユーザーを取得。

    引数:
        token: AuthorizationヘッダーからのJWTトークン

    戻り値:
        トークンからのユーザー識別子

    例外:
        HTTPException: トークンが無効または期限切れの場合
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 設定から明示的にHS256アルゴリズムを指定
        payload = jwt.decode(
            token, _CONFIG_.JWT_SECRET_KEY, algorithms=[_CONFIG_.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    return user_id


async def get_current_active_user(current_user: str = Depends(get_current_user), current_ip: str = Depends(get_current_session)):
    """
    現在のアクティブユーザーを取得し、アクティブであることを確認。

    引数:
        current_user: トークンからのユーザー識別子

    戻り値:
        現在のアクティブユーザー

    例外:
        HTTPException: ユーザーが非アクティブの場合
    """
    # 実際のアプリケーションでは、データベースからユーザー詳細を取得し
    # アクティブかどうかを確認します。ここではユーザーIDを返すだけです。
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    # 将用户ID从字符串转换为整数
    user_id = int(current_user)
    # 通过会话管理器获取SQL实例
    sql_client = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    
    user = await sql_client.get_user_by_id(user_id)
    if not user or not user.get('is_active'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is inactive"
        )
    return user


async def get_current_admin_user(current_user: str = Depends(get_current_user), current_ip: str = Depends(get_current_session)):
    """
    現在の管理者ユーザーを取得し、管理者であることを確認。
    この関数は管理者専用エンドポイントで使用されます。
    パラメータ:
    - current_user: トークンからのユーザー識別子
    戻り値:
    - 現在の管理者ユーザー
    例外:
    - HTTPException: ユーザーが管理者でない場合
    """
    # 将用户ID从字符串转换为整数
    user_id = int(current_user)
    # 通过会话管理器获取SQL实例
    sql_client = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    
    user = await sql_client.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Not an admin")
    return user
