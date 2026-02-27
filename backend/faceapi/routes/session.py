"""
会话管理路由模块。

提供 sessionId 的生成、查询和管理 API。
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
import time
from loguru import logger

from ..core import _CONFIG_
from ..core import _SESSION_MANAGER_
from ..utils import get_current_session, create_session_token, get_client_ip
from ..schemas import SessionCreateResponse, SessionInfoResponse, ErrorResponse


router = APIRouter(prefix="/session", tags=["session"])


@router.post(
    "/create",
    responses={
        200: {"model": SessionCreateResponse, "description": "会话创建成功"},
        400: {"model": ErrorResponse, "description": "会话创建失败"},
        409: {"model": ErrorResponse, "description": "IP 已有活跃会话"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def create_session(request: Request):
    """
    为当前客户端 IP 创建新的会话。

    每个 IP 地址同一时间只能有一个活跃的 sessionId。
    如果该 IP 已有活跃会话，则返回拒绝信息。
    """
    if not _CONFIG_.ENABLE_SESSION_MANAGEMENT:
        return ErrorResponse(code=400, detail="セッション管理機能が有効になっていません")

    client_ip = get_client_ip(request)
    logger.info(f"セッション作成リクエストを受信しました、IP: {client_ip}")

    try:
        session_info = await _SESSION_MANAGER_.create_session(client_ip)
        if not session_info:
            return ErrorResponse(code=409, detail="IP 已有活跃会话")
        token = create_session_token(
            session_info.ip_address, session_info.created_at, session_info.expires_at
        )

        return SessionCreateResponse(
            code=200,
            success=True,
            token=token,
            message="会话创建成功",
            ip_address=client_ip,
            expires_in=_CONFIG_.SESSION_ID_EXPIRE_SECONDS,
        )

    except Exception as e:
        logger.error(f"セッション作成に失敗しました: {str(e)}")
        return ErrorResponse(code=500, detail=f"セッション作成に失敗しました: {str(e)}")


@router.get(
    "/info",
    responses={
        200: {"model": SessionInfoResponse, "description": "获取会话信息成功"},
        404: {"model": ErrorResponse, "description": "会话不存在或已过期"},
        400: {"model": ErrorResponse, "description": "会话管理功能未启用"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def get_session_info(current_ip: str = Depends(get_current_session)):
    """
    获取当前会话的详细信息。

    通过 Session-Token header 验证会话有效性并返回会话信息。
    """
    if not _CONFIG_.ENABLE_SESSION_MANAGEMENT:
        return ErrorResponse(code=400, detail="セッション管理機能が有効になっていません")

    try:
        session_info = await _SESSION_MANAGER_.get_session_by_ip(current_ip)

        if not session_info:
            return ErrorResponse(code=404, detail="会话不存在或已过期")

        return SessionInfoResponse(code=200, **session_info.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セッション情報の取得に失敗しました: {str(e)}")
        return ErrorResponse(code=500, detail=f"获取会话信息失败: {str(e)}")


@router.get(
    "/current",
    responses={
        200: {"model": SessionInfoResponse, "description": "获取当前会话信息成功"},
        404: {"model": ErrorResponse, "description": "当前 IP 无活跃会话"},
        400: {"model": ErrorResponse, "description": "会话管理功能未启用"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def get_current_session_info(request: Request,):
    """
    获取当前客户端 IP 的活跃会话信息。
    """
    if not _CONFIG_.ENABLE_SESSION_MANAGEMENT:
        return ErrorResponse(code=400, detail="セッション管理機能が有効になっていません")

    client_ip = get_client_ip(request)

    try:
        session_info = await _SESSION_MANAGER_.get_session_by_ip(client_ip)

        if not session_info:
            return ErrorResponse(code=404, detail="当前 IP 无活跃会话")

        return SessionInfoResponse(code=200, **session_info.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"現在のセッション情報の取得に失敗しました: {str(e)}")
        return ErrorResponse(code=500, detail=f"获取当前会话信息失败: {str(e)}")


@router.delete(
    "/current",
    responses={
        200: {"description": "会话删除成功"},
        404: {"model": ErrorResponse, "description": "会话不存在"},
        400: {"model": ErrorResponse, "description": "会话管理功能未启用"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def delete_session(current_ip: str = Depends(get_current_session)):
    """
    删除当前会话。

    通过 Session-Token header 验证会话有效性并删除对应会话。
    """
    if not _CONFIG_.ENABLE_SESSION_MANAGEMENT:
        return ErrorResponse(code=400, detail="セッション管理機能が有効になっていません")

    try:
        success = await _SESSION_MANAGER_.delete_session(current_ip)

        if not success:
            return ErrorResponse(code=404, detail="セッションが存在しません")

        return {
            "code": 200,
            "success": True,
            "message": "セッションが正常に削除されました",
            "ip_address": current_ip,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セッション削除に失敗しました: {str(e)}")
        return ErrorResponse(code=500, detail=f"セッション削除に失敗しました: {str(e)}")


@router.get("/summary")
async def get_session_summary():
    """
    获取会话管理器的摘要信息。
    """
    if not _CONFIG_.ENABLE_SESSION_MANAGEMENT:
        return ErrorResponse(code=400, detail="セッション管理機能が有効になっていません")

    try:
        summary = _SESSION_MANAGER_.get_sessions_summary()
        summary["config"] = {
            "session_expire_seconds": _CONFIG_.SESSION_ID_EXPIRE_SECONDS,
            "enable_session_management": _CONFIG_.ENABLE_SESSION_MANAGEMENT,
        }
        return summary
    except Exception as e:
        logger.error(f"セッション概要の取得に失敗しました: {str(e)}")
        return ErrorResponse(code=500, detail=f"セッション概要の取得に失敗しました: {str(e)}")


@router.post("/cleanup")
async def cleanup_expired_sessions():
    """
    手动触发过期会话清理。
    """
    if not _CONFIG_.ENABLE_SESSION_MANAGEMENT:
        return ErrorResponse(code=400, detail="セッション管理機能が有効になっていません")

    try:
        await _SESSION_MANAGER_._cleanup_expired_sessions()
        return {"success": True, "message": "期限切れセッションのクリーンアップが完了しました"}
    except Exception as e:
        logger.error(f"期限切れセッションのクリーンアップに失敗しました: {str(e)}")
        return ErrorResponse(code=500, detail=f"期限切れセッションのクリーンアップに失敗しました: {str(e)}")
