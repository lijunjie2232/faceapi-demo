"""
顔認識システムのサービスモジュール。

このモジュールはAPIルートハンドラとは別に、
アプリケーションの様々な機能のビジネスロジック実装を含みます。
"""

from .admin import (
    activate_user_service,
    batch_activate_users_service,
    batch_deactivate_users_service,
    batch_reset_face_data_service,
    batch_reset_password_service,
    create_user_as_admin_service,
    deactivate_user_service,
    list_users_service,
    update_user_as_admin_service,
    validate_user_update_uniqueness,
)
from .face import update_face_embedding_service, verify_face_service
from .user import (
    create_user_service,
    delete_user_account_service,
    get_current_user_profile_service,
    get_user_service,
)

__ALL__ = [
    "list_users_service",
    "update_user_as_admin_service",
    "create_user_as_admin_service",
    "deactivate_user_service",
    "activate_user_service",
    "validate_user_update_uniqueness",
    "update_face_embedding_service",
    "verify_face_service",
    "update_user_profile_service",
    "create_user_service",
    "delete_user_account_service",
    "get_current_user_profile_service",
    "get_user_service",
    "batch_reset_password_service",
    "batch_activate_users_service",
    "batch_deactivate_users_service",
    "batch_reset_face_data_service",
]
