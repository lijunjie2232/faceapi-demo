"""
顔認識システムの設定モジュール。

このモジュールはアプリケーションのすべての設定を処理するConfigクラスを定義します。
データベース接続、モデルパラメータ、セキュリティ設定などが含まれます。
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource


class Config(BaseSettings):
    """
    顔認識システムの設定クラス。

    このクラスにはアプリケーションのすべての設定が含まれています。
    データベース接続、モデルパラメータ、セキュリティ設定などがあります。
    設定は環境変数から読み込むことができます。
    """

    # モデル設定
    MODEL_PATH: str = Field(
        os.getenv("MODEL_PATH", "model.onnx"), description="モデルファイルへのパス"
    )
    MODEL_LOADER: str = Field(
        os.getenv("MODEL_LOADER", "onnx"), description="使用するモデルローダーの種類"
    )
    MODEL_THRESHOLD: float = Field(
        float(os.getenv("MODEL_THRESHOLD", "0.23")), description="顔認識信頼度の閾値"
    )
    MODEL_DEVICE: str = Field(
        os.getenv("MODEL_DEVICE", "cpu"),
        description="モデル推論に使用するデバイス (cpu, cuda:0, cuda:1, etc.)",
    )
    MODEL_EMB_DIM: int = Field(
        int(os.getenv("EMB_DIM", "512")), description="モデルの埋め込み次元数"
    )

    # アプリケーション設定
    API_V1_STR: str = Field("/api/v1", description="APIのバージョンプレフィックス")
    PROJECT_NAME: str = Field("Face Recognition System (Demo)", description="プロジェクト名")

    # セキュリティ設定
    JWT_SECRET_KEY: str = Field(
        os.getenv("SECRET_KEY", "461159441a3c8c88cb3b611de07fcbb05a9fb838a1803e62588a3db265b0b415"),
        description="JWTトークンのシークレットキー",
    )
    JWT_ALGORITHM: str = Field(
        os.getenv("ALGORITHM", "HS256"), description="JWTトークンのアルゴリズム"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        5, description="アクセストークンの有効期限（分）"
    )

    # パスワードハッシュ設定
    PASSWORD_HASH_ALGORITHM: str = Field(
        os.getenv("PASSWORD_HASH_ALGORITHM", "sha256_crypt"),
        description="パスワードハッシュのアルゴリズム",
    )

    # 顔認識設定
    # FACE_DETECTION_MODEL: str = "hog"  # オプション: "hog", "cnn"
    # TOLERANCE: float = 0.6  # 値が小さいほど厳密なマッチング

    # STRICT_MODEでは、顔とユーザー名・パスワードの両方を検証する必要があります
    STRICT_MODE: bool = Field(
        True, description="厳格モード（顔認証と資格情報の両方を検証）"
    )

    # サーバー設定
    LISTEN_HOST: str = Field(
        os.getenv("LISTEN_HOST", "0.0.0.0"), description="サーバーのリッスンホスト"
    )
    LISTEN_PORT: int = Field(
        int(os.getenv("LISTEN_PORT", "80")), description="サーバーのリッスンポート"
    )

    # CORSの許可オリジン
    ALLOWED_ORIGINS: list[str] = Field(
        os.getenv("ALLOWED_ORIGINS", ["*"]),
        description="CORS許可オリジンリスト",
    )

    # default init account
    ADMIN_USERNAME: str = Field(
        os.getenv("ADMIN_USERNAME", "admin"), description="初期管理者ユーザー名"
    )
    ADMIN_PASSWORD: str = Field(
        os.getenv("ADMIN_PASSWORD", "admin123"), description="初期管理者パスワード"
    )
    ADMIN_EMAIL: str = Field(
        os.getenv("ADMIN_EMAIL", "admin@example.com"),
        description="初期管理者メールアドレス",
    )
    ADMIN_FULL_NAME: str = Field(
        os.getenv("ADMIN_FULL_NAME", "Demo Administrator"), description="初期管理者氏名"
    )
    # システム設定
    ALLOW_FACE_DEDUPICATION: bool = Field(
        False, description="顔の重複検出を許可するかどうか"
    )

    # 演示模式设置
    USE_MEMORY_DB: bool = Field(
        True, description="使用内存数据库进行演示（不连接实际数据库）"
    )
    STATIC_ROOT: str = Field(
        os.getenv("STATIC_ROOT", "frontend/dist"), description="静的ファイルルート"
    )
    
    # 会话管理设置
    SESSION_SECRET_KEY: str = Field(
        os.getenv("SESSION_SECRET_KEY", "67e210bda1031ef8b9d0263effab831de0940d5b0c1f0b791ea8f5bdd78423b1"),
        description="会话密钥",
    )
    SESSION_ID_EXPIRE_SECONDS: int = Field(
        int(os.getenv("SESSION_ID_EXPIRE_SECONDS", "300")), 
        description="sessionId 有效期（秒）"
    )
    ENABLE_SESSION_MANAGEMENT: bool = Field(
        True, description="启用会话管理功能"
    )

    # class Config:
    #     """環境ファイル設定を定義するPydantic設定クラス。"""

    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
