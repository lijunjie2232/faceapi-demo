"""
パスワードを安全に暗号化および比較するためのパスワードユーティリティモジュール。
"""

from typing import Union

from passlib.context import CryptContext

# sha256_cryptを使用するようにパスワードハッシュコンテキストを設定
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    平文パスワードをsha256_cryptを使用してハッシュ化。

    引数:
        password: ハッシュ化する平文パスワード

    戻り値:
        文字列としてのハッシュ化されたパスワード
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文パスワードとハッシュ化されたパスワードを検証。

    引数:
        plain_password: 検証する平文パスワード
        hashed_password: 比較対象のハッシュ化されたパスワード

    戻り値:
        パスワードが一致する場合はTrue、それ以外はFalse
    """
    return pwd_context.verify(plain_password, hashed_password)


def is_valid_password(password: str, min_length: int = 8) -> bool:
    """
    パスワードが基本的な検証要件を満たしているか確認。

    引数:
        password: 検証するパスワード
        min_length: 最小必要な長さ（デフォルト: 8）

    戻り値:
        パスワードが有効な場合はTrue、それ以外はFalse
    """
    if len(password) < min_length:
        return False

    # パスワードに少なくとも1つの大文字、小文字、数字が含まれているか確認
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    return has_upper and has_lower and has_digit


if __name__ == "__main__":
    # 使用例
    EXAMPLE_PASSWORD = "MySecurePassword123"

    print(f"元のパスワード: {EXAMPLE_PASSWORD}")

    # パスワードをハッシュ化
    hashed = hash_password(EXAMPLE_PASSWORD)
    print(f"ハッシュ化されたパスワード: {hashed}")

    # パスワードを検証
    is_correct = verify_password(password, hashed)
    print(f"パスワード検証結果: {is_correct}")

    # 間違ったパスワードで試す
    is_wrong = verify_password("WrongPassword", hashed)
    print(f"間違ったパスワード検証結果: {is_wrong}")
