"""
Schema definitions for user-related operations.
This module contains Pydantic models for user creation, update, and representation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """
    Base user schema containing common fields for user operations.

    Attributes:
        username: Unique identifier for the user
        email: Email address of the user
        full_name: Full name of the user (optional)
    """

    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Attributes:
        password: Password for the new user account
    """

    password: str


class UserCreateAsAdmin(UserCreate):
    """
    Schema for creating a user with admin privileges.

    Attributes:
        is_admin: Flag indicating if the user has admin privileges (default is False)
    """

    is_admin: Optional[bool] = False


class UserUpdate(BaseModel):
    """
    Schema for updating user information.
    All fields are optional to allow partial updates.

    Attributes:
        username: Updated username (optional)
        email: Updated email address (optional)
        full_name: Updated full name (optional)
        password: Updated password (optional)
        is_active: Updated active status (optional)
    """

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    # head_pic: Optional[str] = None


class UserUpdateAsAdmin(UserUpdate):
    """
    Schema for updating user information with admin privileges.
    Extends UserUpdate with an additional admin flag.

    Attributes:
        is_admin: Updated admin status (optional)
    """

    is_admin: Optional[bool] = None


class UserInDB(UserBase):
    """
    Schema representing a user stored in the database.

    Attributes:
        id: Unique identifier of the user in the database
        is_active: Active status of the user account
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
        head_pic: Path or URL to the user's profile picture (optional)
        is_admin: Admin status of the user
    """

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    head_pic: Optional[str] = None
    is_admin: bool

    class Config:
        from_attributes = True


class UserPydantic(BaseModel):
    """
    Schema for returning user information in API responses.

    Attributes:
        id: Unique identifier of the user
        username: Username of the user
        email: Email address of the user
        full_name: Full name of the user (optional)
        is_active: Active status of the user account
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
        head_pic: Path or URL to the user's profile picture (optional)
    """

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    head_pic: Optional[str] = None


class UserInPydantic(BaseModel):
    """
    Schema for basic user information in API responses.

    Attributes:
        username: Username of the user
        email: Email address of the user
        full_name: Full name of the user (optional)
    """

    username: str
    email: str
    full_name: Optional[str] = None


class UserCreatePydantic(BaseModel):
    """
    Schema for creating a user with Pydantic validation.

    Attributes:
        username: Username for the new user
        email: Email address for the new user
        full_name: Full name of the user (optional)
        password: Password for the new user account
    """

    username: str
    email: str
    full_name: Optional[str] = None
    password: str


class UserUpdatePydantic(BaseModel):
    """
    Schema for updating user information with Pydantic validation.
    All fields are optional to allow partial updates.

    Attributes:
        username: Updated username (optional)
        email: Updated email address (optional)
        full_name: Updated full name (optional)
        password: Updated password (optional)
        head_pic: Updated profile picture (optional)
    """

    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    head_pic: Optional[str] = None


class BatchOperationRequest(BaseModel):
    """
    Schema for batch operation requests.

    Attributes:
        user_ids: List of user IDs to perform the operation on
        value: Optional value for operations that require it (e.g., new password for reset-password)
    """

    user_ids: List[int]
    value: Optional[str] = None


class BatchOperationResult(BaseModel):
    """
    Schema for batch operation results.

    Attributes:
        success_count: Number of successfully processed users
        failed_count: Number of users that failed processing
        total_count: Total number of users in the request
        failed_users: List of user IDs that failed processing
        operation: The operation that was performed
    """

    success_count: int
    failed_count: int
    total_count: int
    failed_users: List[int]
    operation: str


class User(UserInDB):
    """
    Schema representing a complete user object.
    Extends UserInDB without adding new fields.
    """

    pass
