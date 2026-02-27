"""
Admin service module for the Face Recognition System.

This module contains business logic for administrative operations
including user management functionalities.
"""

from typing import List, Optional

from ..core import _SESSION_MANAGER_
from ..schemas import BatchOperationResult, User, UserCreateAsAdmin, UserUpdateAsAdmin
from ..utils import hash_password


async def list_users_service(
    current_ip: str,
    skip: int = 0,
    limit: int = 100,
    username: Optional[str] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    set_face: Optional[bool] = None,
):
    """
    Service function to list all users with pagination.

    Args:
        current_ip: 当前会话的IP地址
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        username: Optional filter for username (case-insensitive partial match)
        email: Optional filter for email (case-insensitive partial match)
        full_name: Optional filter for full name (case-insensitive partial match)
        is_active: Optional filter for active status
        is_admin: Optional filter for admin status
        set_face: Optional filter for face picture status (True if face pic is set, False if not)

    Returns:
        A tuple containing the list of users and the total count
    """

    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # Build the query with filters if any filter is provided
    users_list = await sql_instance.list_users()
    # 应用过滤条件
    filtered_users = []
    for user in users_list:
        # 应用各种过滤条件
        if username is not None and username.lower() not in user['username'].lower():
            continue
        if email is not None and email.lower() not in user['email'].lower():
            continue
        if full_name is not None and full_name.lower() not in user['full_name'].lower():
            continue
        if is_active is not None and user['is_active'] != is_active:
            continue
        if is_admin is not None and user['is_admin'] != is_admin:
            continue
        if set_face is not None:
            has_face = user['head_pic'] is not None
            if set_face and not has_face:
                continue
            if not set_face and has_face:
                continue
        filtered_users.append(user)
    
    # 获取总数
    count = len(filtered_users)
    
    # 应用分页
    paginated_users = filtered_users[skip:skip+limit]




    users = []
    for user_obj in paginated_users:
        user = User(
            id=user_obj['id'],
            username=user_obj['username'],
            email=user_obj['email'],
            full_name=user_obj['full_name'],
            is_active=user_obj['is_active'],
            created_at=user_obj['created_at'],
            updated_at=user_obj['updated_at'],
            # head_pic=user_obj.head_pic,
            head_pic="1" if user_obj['head_pic'] else "0",
            is_admin=user_obj['is_admin'],
        )
        users.append(user)

    return users, count


async def create_user_as_admin_service(user_create: UserCreateAsAdmin, current_ip: str):
    """
    Service function to create a new user as admin.

    Args:
        user_create: User creation request object containing user details
        current_ip: 当前会话的IP地址

    Returns:
        Created user object
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # Hash the password
    hashed_password = hash_password(user_create.password)

    # Create the user in the database
    created_user = await sql_instance.create_user(
        username=user_create.username,
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=user_create.is_admin,
    )

    return created_user


async def update_user_as_admin_service(user_id: int, user_update: UserUpdateAsAdmin, current_ip: str):
    """
    Service function to update a specific user by ID.

    Args:
        user_id: The ID of the user to update
        user_update: User update request object containing fields to update
        current_ip: 当前会话的IP地址

    Returns:
        Updated user object
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # Prepare update data
    update_data = {}
    if user_update.username:
        update_data["username"] = user_update.username
    if user_update.email:
        update_data["email"] = user_update.email
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    if user_update.password:
        update_data["hashed_password"] = hash_password(user_update.password)
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    if user_update.is_admin is not None:
        update_data["is_admin"] = user_update.is_admin

    # Update the user
    await sql_instance.update_user(user_id, **update_data)

    # Get the updated user
    updated_user = await sql_instance.get_user_by_id(user_id)

    return updated_user


async def deactivate_user_service(user_id: int, current_ip: str):
    """
    Service function to deactivate a specific user by ID.

    Args:
        user_id: The ID of the user to deactivate
        current_ip: 当前会话的IP地址

    Returns:
        Boolean indicating success
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # Perform soft delete by deactivating the user
    result = await sql_instance.update_user(user_id, is_active=False)
    return result


async def activate_user_service(user_id: int, current_ip: str):
    """
    Service function to activate a specific user by ID.

    Args:
        user_id: The ID of the user to activate
        current_ip: 当前会话的IP地址

    Returns:
        Boolean indicating success
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # Activate the user
    result = await sql_instance.update_user(user_id, is_active=True)
    return result


async def validate_user_update_uniqueness(user_id: int, user_update: UserUpdateAsAdmin, current_ip: str):
    """
    Validate that updated username/email don't conflict with other users.

    Args:
        user_id: The ID of the user being updated
        user_update: User update request object containing fields to update
        current_ip: 当前会话的IP地址

    Returns:
        Error message if validation fails, None otherwise
    """
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    if user_update.username:
        existing_user_with_username = await sql_instance.get_user_by_username(user_update.username)
        if existing_user_with_username and existing_user_with_username['id'] != user_id:
            return "ユーザー名は既に使用されています"

    if user_update.email:
        existing_user_with_email = await sql_instance.get_user_by_email(user_update.email)
        if existing_user_with_email and existing_user_with_email['id'] != user_id:
            return "メールアドレスは既に登録されています"

    return None


async def batch_reset_password_service(
    user_ids: List[int], new_password: str, current_ip: str
) -> BatchOperationResult:
    """
    Service function to reset passwords for multiple users.

    Args:
        user_ids: List of user IDs to reset passwords for
        new_password: New password to set for all users
        current_ip: 当前会话的IP地址

    Returns:
        BatchOperationResult containing success/failure statistics
    """
    success_count = 0
    failed_users = []

    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    hashed_password = hash_password(new_password)

    for user_id in user_ids:
        try:
            result = await sql_instance.update_user(user_id, hashed_password=hashed_password)
            if result:
                success_count += 1
            else:
                failed_users.append(user_id)
        except Exception:
            failed_users.append(user_id)

    return BatchOperationResult(
        success_count=success_count,
        failed_count=len(failed_users),
        total_count=len(user_ids),
        failed_users=failed_users,
        operation="reset-password",
    )


async def batch_activate_users_service(user_ids: List[int], current_ip: str) -> BatchOperationResult:
    """
    Service function to activate multiple users.

    Args:
        user_ids: List of user IDs to activate
        current_ip: 当前会话的IP地址

    Returns:
        BatchOperationResult containing success/failure statistics
    """
    success_count = 0
    failed_users = []

    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    for user_id in user_ids:
        try:
            result = await sql_instance.update_user(user_id, is_active=True)
            if result:
                success_count += 1
            else:
                failed_users.append(user_id)
        except Exception:
            failed_users.append(user_id)

    return BatchOperationResult(
        success_count=success_count,
        failed_count=len(failed_users),
        total_count=len(user_ids),
        failed_users=failed_users,
        operation="active",
    )


async def batch_deactivate_users_service(user_ids: List[int], current_ip: str) -> BatchOperationResult:
    """
    Service function to deactivate multiple users.

    Args:
        user_ids: List of user IDs to deactivate
        current_ip: 当前会话的IP地址

    Returns:
        BatchOperationResult containing success/failure statistics
    """
    success_count = 0
    failed_users = []

    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    for user_id in user_ids:
        try:
            result = await sql_instance.update_user(user_id, is_active=False)
            if result:
                success_count += 1
            else:
                failed_users.append(user_id)
        except Exception:
            failed_users.append(user_id)

    return BatchOperationResult(
        success_count=success_count,
        failed_count=len(failed_users),
        total_count=len(user_ids),
        failed_users=failed_users,
        operation="inactive",
    )


async def batch_reset_face_data_service(user_ids: List[int], current_ip: str) -> BatchOperationResult:
    """
    Service function to reset face data for multiple users.

    Args:
        user_ids: List of user IDs to reset face data for
        current_ip: 当前会话的IP地址

    Returns:
        BatchOperationResult containing success/failure statistics
    """
    success_count = 0
    failed_users = []
    
    # 通过会话管理器获取SQL实例
    sql_instance = await _SESSION_MANAGER_.get_sql_instance(current_ip)
    if not sql_instance:
        raise HTTPException(status_code=401, detail="無効なセッションです")

    for user_id in user_ids:
        try:
            result = await sql_instance.update_user(user_id, head_pic=None, embedding=None)

            if result:
                success_count += 1
            else:
                failed_users.append(user_id)

            await sql_instance.delete_face_embedding(user_id)

        except Exception:
            failed_users.append(user_id)

    return BatchOperationResult(
        success_count=success_count,
        failed_count=len(failed_users),
        total_count=len(user_ids),
        failed_users=failed_users,
        operation="reset-face",
    )
