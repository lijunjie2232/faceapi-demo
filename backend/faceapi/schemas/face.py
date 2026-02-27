"""
Schema definitions for face recognition related requests and responses.
This module contains Pydantic models for handling face registration and recognition operations.
"""

from typing import List, Optional

from pydantic import BaseModel


class FaceRegisterRequest(BaseModel):
    """
    Schema for face registration request.

    Attributes:
        user_id: ID of the user registering the face
        image_data: Base64 encoded image data
        image_format: Format of the image (default is "jpg")
    """

    user_id: int
    image_data: str  # Base64 encoded image
    image_format: str = "jpg"  # Image format (jpg, png, etc.)


class FaceRecognitionResult(BaseModel):
    """
    Schema for individual face recognition result.

    Attributes:
        user_id: ID of the recognized user (if found)
        username: Name of the recognized user (if found)
        confidence: Confidence score of the recognition
        recognized: Whether a face was successfully recognized
        message: Additional information about the recognition
    """

    user_id: Optional[int] = None
    username: Optional[str] = None
    confidence: Optional[float] = None
    recognized: bool = False
    message: str = ""


class FaceRecognitionRequest(BaseModel):
    """
    Schema for face recognition request.

    Attributes:
        image_data: Base64 encoded image data to recognize
        image_format: Format of the image (default is "jpg")
    """

    image_data: str  # Base64 encoded image
    image_format: str = "jpg"


class FaceRecognitionResponse(BaseModel):
    """
    Schema for face recognition response.

    Attributes:
        results: List of recognition results
        processed_image_url: URL of the processed image (optional)
        processing_time: Time taken to process the recognition
    """

    results: List[FaceRecognitionResult]
    processed_image_url: Optional[str] = None
    processing_time: float
