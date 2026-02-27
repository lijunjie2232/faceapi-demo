"""
顔認識システムのコアモジュール。

このモジュールはアプリケーションの設定とロガーを初期化します。
設定を読み込み、_CONFIG_オブジェクトを介してアプリケーション全体で
利用できるようにします。
"""

from loguru import logger

from .config import Config
_CONFIG_ = Config()
logger.info("設定が読み込まれました")
logger.info(_CONFIG_)

from .session import SessionManager

_SESSION_MANAGER_ = SessionManager()


__ALL__ = [
    "_CONFIG_",
    "_SESSION_MANAGER_",
]
