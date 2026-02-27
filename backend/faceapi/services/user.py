"""
顔認識システムのユーザーサービスモジュール。

このモジュールは認証とプロフィール操作を含む
ユーザー管理のビジネスロジックを含みます。
"""

from fastapi import HTTPException

from ..core import _SESSION_MANAGER_
from ..schemas import User, UserCreate, UserUpdate
from ..utils import hash_password, verify_password


async def authenticate_user(username: str, password: str, current_ip: str):
    """
    ユーザー名/メールアドレスとパスワードでユーザーを認証。

    引数:
        username: ユーザーのユーザー名またはメールアドレス
        password: 検証する平文パスワード
        current_ip: 当前会话的IP地址

    戻り値:
        成功した場合は認証されたユーザーオブジェクト、それ以外はNone
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # 使用SQL实例查询用户
    user = await sql_instance.get_user_by_username(username) or await sql_instance.get_user_by_email(username)

    if not user:
        return None

    # ユーザーがアクティブかどうか确认
    if not user.get('is_active', False):
        return None

    # パスワードを検証
    if not verify_password(
        plain_password=password,
        hashed_password=user.get('hashed_password'),
    ):
        return None

    return user


async def create_user_service(user: UserCreate, current_ip: str):
    """
    新しいユーザーを作成するサービス関数。

    引数:
        user: ユーザー詳細を含むユーザー作成リクエストオブジェクト
        current_ip: 当前会话的IP地址

    戻り値:
        作成されたユーザーオブジェクト
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # ユーザーが既に存在するか确认
    existing_user = await sql_instance.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="ユーザー名は既に使用されています")

    existing_email = await sql_instance.get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="メールアドレスは既に登録されています")

    # pass_utilsモジュールを使用してパスワードをハッシュ化
    hashed_password = hash_password(user.password)

    # データベースにユーザーを作成
    created_user = await sql_instance.create_user(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True,
    )

    return created_user


async def get_current_user_profile_service(user_id: int, current_ip: str):
    """
    現在のユーザーのプロフィールを取得するサービス関数。

    引数:
        user_id: プロフィールを取得するユーザーのID
        current_ip: 当前会话的IP地址

    戻り値:
        見つかった場合はユーザープロフィールオブジェクト
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    user_obj = await sql_instance.get_user_by_id(user_id)

    if not user_obj:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    user = User(
        id=user_obj['id'],
        username=user_obj['username'],
        email=user_obj['email'],
        full_name=user_obj['full_name'],
        is_active=user_obj['is_active'],
        created_at=user_obj['created_at'],
        updated_at=user_obj['updated_at'],
        head_pic=user_obj['head_pic'],
        is_admin=user_obj['is_admin'],
    )

    return user


async def update_user_profile_service(user_id: int, user_update: UserUpdate, current_ip: str):
    """
    現在のユーザーのプロフィールを更新するサービス関数。

    引数:
        user_id: 更新するユーザーのID
        user_update: 更新するフィールドを含むユーザー更新リクエストオブジェクト
        current_ip: 当前会话的IP地址

    戻り値:
        更新されたユーザーオブジェクト
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # 存在を確認するために現在のユーザーを取得
    current_user_obj = await sql_instance.get_user_by_id(user_id)

    if not current_user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    # 他のユーザーのためにユーザー名またはメールアドレスが既に存在するか確認
    if user_update.username:
        existing_user_with_username = await sql_instance.get_user_by_username(user_update.username)
        if existing_user_with_username and existing_user_with_username['id'] != user_id:
            raise HTTPException(status_code=400, detail="ユーザー名は既に使用されています")

    if user_update.email:
        existing_user_with_email = await sql_instance.get_user_by_email(user_update.email)
        if existing_user_with_email and existing_user_with_email['id'] != user_id:
            raise HTTPException(status_code=400, detail="メールアドレスは既に登録されています")

    # 更新データを准备
    update_data = {}
    if user_update.username:
        update_data["username"] = user_update.username
    if user_update.email:
        update_data["email"] = user_update.email
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    if user_update.password:
        update_data["hashed_password"] = hash_password(user_update.password)

    # ユーザーを更新
    await sql_instance.update_user(user_id, **update_data)

    # 更新されたユーザーを取得
    updated_user_obj = await sql_instance.get_user_by_id(user_id)

    return updated_user_obj


async def delete_user_account_service(user_id: int, current_ip: str):
    """
    現在のユーザーのアカウントを削除（非アクティブ化）するサービス関数。

    引数:
        user_id: 非アクティブ化するユーザーのID
        current_ip: 当前会话的IP地址

    戻り値:
        成功を示すブール値
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # 存在を確認するためにユーザーを取得
    user = await sql_instance.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 完全削除ではなくユーザーを非アクティブ化
    result = await sql_instance.update_user(user_id, is_active=False)

    return result


async def get_user_service(current_ip: str, *args, **kwargs):
    """
    IDで特定のユーザーを取得するサービス関数。

    引数:
        current_ip: 当前会话的IP地址
        *args, **kwargs: 查询参数

    戻り値:
        見つかった場合はユーザーオブジェクト、それ以外はNone
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    user = await sql_instance.get_user(*args, **kwargs)
    return user
