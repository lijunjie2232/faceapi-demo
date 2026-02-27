"""
顔認識システムのユーザーモデルモジュール。

このモジュールは認証、プロフィール情報、メタデータを含む
ユーザーアカウントのデータベースモデルを定義します。
"""

from tortoise import fields, run_async
from tortoise.models import Model


class UserModel(Model):
    """
    ユーザーアカウントのデータベースモデル。

    このモデルは認証詳細、プロフィール情報、
    アカウント状態と作成時間に関するメタデータを含む
    ユーザーアカウント情報を保存します。
    """

    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=100, unique=True)
    email = fields.CharField(max_length=200, unique=True)
    full_name = fields.CharField(max_length=200, null=True)
    hashed_password = fields.CharField(max_length=200)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    head_pic = fields.TextField(null=True)
    is_admin = fields.BooleanField(default=False)
    embedding = fields.JSONField(null=True, description="人脸特征向量嵌入数据")

    class Meta:
        """テーブル設定を定義するメタクラス。"""

        table = "users"

    def __str__(self):
        return self.username
