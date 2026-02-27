from pydantic import BaseModel

class SessionCreateResponse(BaseModel):
    """会话创建响应模型"""
    code: int
    success: bool
    token: str
    message: str
    ip_address: str
    expires_in: int


class SessionInfoResponse(BaseModel):
    """会话信息响应模型"""
    code: int
    ip_address: str
    created_at: str
    expires_at: str
    remaining_time: int
    is_expired: bool


class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int
    detail: str
