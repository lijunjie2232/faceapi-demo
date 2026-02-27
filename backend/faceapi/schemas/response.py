"""
Schema definitions for standard API responses.
This module contains Pydantic models for consistent API response formats.
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel):
    """
    Base response schema containing common fields for all API responses.

    Attributes:
        success: Boolean indicating if the request was successful
        message: Human-readable message describing the result
        code: Status code for the response
        timestamp: Timestamp of when the response was generated
    """

    success: bool
    message: str
    code: int = 200
    timestamp: datetime = datetime.now()


class DataResponse(BaseResponse, Generic[T]):
    """
    Response schema for single data item responses.

    Attributes:
        data: Optional single data item of generic type T
    """

    data: Optional[T] = None


class ListResponse(BaseResponse, Generic[T]):
    """
    Response schema for list data responses.

    Attributes:
        data: List of items of generic type T
        total: Total number of items available (for pagination)
        page: Current page number (for pagination)
        size: Size of current page (for pagination)
    """

    data: List[T] = []
    total: int = 0
    page: Optional[int] = None
    size: Optional[int] = None
