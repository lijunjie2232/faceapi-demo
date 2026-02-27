"""
顔認識システムのルートモジュール。

このモジュールはアプリケーションのAPIルート定義を含み、
管理者、顔認識、ユーザー管理などの論理的なグループに
エンドポイントを整理します。
"""

from .admin import router as admin
from .face import router as face
from .user import router as user
from .session import router as session

__ALL__ = [
    "admin",
    "face",
    "user",
    "session",
]
