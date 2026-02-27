"""
会话依赖注入模块。

提供类似于 get_current_user 的会话验证依赖函数，
用于验证 sessionId 并返回对应的 IP 地址。
"""

from datetime import datetime
from typing import Optional
from loguru import logger

import jwt
from fastapi import Depends, HTTPException, status, Request

from ..core import _CONFIG_

missing_session_token_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing session token",
    headers={"WWW-Authenticate": "Session-Token"},
)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate session token",
    headers={"WWW-Authenticate": "Session-Token"},
)

def get_client_ip(request: Request) -> str:
    """
    从请求中获取客户端真实 IP 地址。

    Args:
        request: FastAPI 请求对象

    Returns:
        str: 客户端 IP 地址
    """
    # 检查 X-Forwarded-For 头部（代理场景）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个 IP（最原始的客户端 IP）
        return forwarded_for.split(",")[0].strip()

    # 检查 X-Real-IP 头部
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 回退到客户端地址
    if request.client:
        return request.client.host

    # 最后的回退
    return "unknown"

def create_session_token(ip_address: str, now: float, expires_at: float) -> str:
    """
    创建包含IP地址的会话令牌。
    
    参数:
        ip_address: 客户端IP地址
        now: 当前时间戳
        expires_at: 过期时间戳
        
    返回:
        编码后的JWT令牌
    """
    # 创建要编码的数据
    data = {
        "ip": ip_address,
        "iat": int(now),
        "exp": int(expires_at)
    }
    
    # 使用会话密钥创建JWT令牌
    encoded_jwt = jwt.encode(
        data, 
        _CONFIG_.SESSION_SECRET_KEY, 
        algorithm=_CONFIG_.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_session(request: Request) -> str:
    """
    从请求头获取并验证会话令牌，返回对应的IP地址。
    
    参数:
        request: FastAPI请求对象
        
    返回:
        验证通过的IP地址字符串
        
    异常:
        HTTPException: 令牌无效、过期或缺失时抛出
    """
    # 从请求头获取Session-Token
    session_token = request.headers.get("Session-Token")
    
    if not session_token:
        raise missing_session_token_exception

    # remove bearer on start
    if session_token.startswith("Bearer "):
        session_token = session_token.removeprefix("Bearer ")
    logger.info(f"セッショントークン: {session_token}")
    
    try:
        # 使用会话密钥解码JWT令牌
        payload = jwt.decode(
            session_token, 
            _CONFIG_.SESSION_SECRET_KEY, 
            algorithms=[_CONFIG_.JWT_ALGORITHM]
        )
        
        # 获取IP地址
        ip_address: str = payload.get("ip")
        if ip_address is None:
            raise credentials_exception
            
        # 验证令牌是否过期
        exp_timestamp = payload.get("exp")
        if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session token expired",
                headers={"WWW-Authenticate": "Session-Token"},
            )
            
    except jwt.PyJWTError:
        raise credentials_exception
    
    return ip_address
