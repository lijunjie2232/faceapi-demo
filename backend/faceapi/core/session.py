"""
会话管理模块。

此模块提供基于 IP 地址的会话管理功能，
每个 IP 地址只能有一个活跃的 sessionId，
并为每个会话维护独立的 SQL 数据库实例。
"""

import time
from typing import Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

# 使用 TTLCache 替代手动会话管理
try:
    from cachetools import TTLCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("cachetools not available, using fallback session management")

from ..core import _CONFIG_
from ..db.memory_managers import MemorySqlManager


@dataclass
class SessionInfo:
    """会话信息数据类"""

    ip_address: str
    created_at: float
    expires_at: float
    sql_instance: MemorySqlManager  # 改用强引用

    @property
    def is_expired(self) -> bool:
        """检查会话是否已过期"""
        return time.time() > self.expires_at

    @property
    def remaining_time(self) -> int:
        """获取剩余有效时间（秒）"""
        remaining = int(self.expires_at - time.time())
        return max(0, remaining)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "ip_address": self.ip_address,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "expires_at": datetime.fromtimestamp(self.expires_at).isoformat(),
            "remaining_time": self.remaining_time,
            "is_expired": self.is_expired,
        }


class SessionManager:
    """
    会话管理器类。

    直接使用 IP 地址作为键管理会话，
    为每个 IP 维护独立的 SQL 数据库实例。
    """

    def __init__(self):
        """初始化会话管理器"""
        if CACHE_AVAILABLE:
            # 使用 TTLCache 自动管理过期
            cache_ttl = _CONFIG_.SESSION_ID_EXPIRE_SECONDS
            # 设置合理的缓存大小限制
            cache_maxsize = 1000  
            self._sessions = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
            self._sql_instances = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
            logger.info(f"TTLCacheを使用してセッションを管理、TTL: {cache_ttl}秒、最大容量: {cache_maxsize}")
        else:
            # 回退到手动管理
            self._sessions: Dict[str, SessionInfo] = {}
            self._sql_instances: Dict[str, MemorySqlManager] = {}
            self._cleanup_interval = 60
            self._last_cleanup = time.time()
            logger.info("手動セッション管理を使用")

    async def create_session(
        self, ip_address: str
    ) -> Union[SessionInfo, None]:
        """
        为指定 IP 地址创建新的会话。

        Args:
            ip_address: 客户端 IP 地址

        Returns:
            SessionInfo 或 None
        """
        if CACHE_AVAILABLE:
            # TTLCache 会自动处理过期，只需检查是否存在
            if ip_address in self._sessions:
                logger.info(f"IP {ip_address} には既にアクティブなセッションがあります")
                return None
        else:
            # 手动检查过期
            existing_session = self._sessions.get(ip_address)
            if existing_session and not existing_session.is_expired:
                logger.info(f"IP {ip_address} には既にアクティブなセッションがあります")
                return None
            await self._cleanup_expired_sessions()

        # 创建新的 SQL 实例
        sql_instance = MemorySqlManager()
        await sql_instance.initialize()

        if CACHE_AVAILABLE:
            # TTLCache 方式：创建会话信息对象
            now = time.time()
            expires_at = now + _CONFIG_.SESSION_ID_EXPIRE_SECONDS
            session_info = SessionInfo(
                ip_address=ip_address,
                created_at=now,
                expires_at=expires_at,
                sql_instance=sql_instance,
            )
            self._sessions[ip_address] = session_info
            self._sql_instances[ip_address] = sql_instance
            logger.info(f"IP {ip_address} の新規セッションを作成 (TTLCacheモード)")
        else:
            # 手动管理方式
            now = time.time()
            expires_at = now + _CONFIG_.SESSION_ID_EXPIRE_SECONDS
            session_info = SessionInfo(
                ip_address=ip_address,
                created_at=now,
                expires_at=expires_at,
                sql_instance=sql_instance,
            )
            self._sessions[ip_address] = session_info
            self._sql_instances[ip_address] = sql_instance
            logger.info(f"IP {ip_address} の新規セッションを作成 (手動管理モード)")

        return self._sessions[ip_address] if CACHE_AVAILABLE else session_info

    async def get_session_by_ip(self, ip_address: str):
        """
        根据 IP 地址获取会话信息。

        Args:
            ip_address: 客户端 IP 地址

        Returns:
            SessionInfo 或 None
        """
        if CACHE_AVAILABLE:
            # TTLCache 模式下存储的是SessionInfo对象
            return self._sessions.get(ip_address)
        else:
            # 手动管理方式
            session_info = self._sessions.get(ip_address)
            if not session_info:
                return None
            
            if session_info.is_expired:
                await self._cleanup_expired_sessions()
                return None
            
            return session_info

    async def get_sql_instance(self, ip_address: str) -> Optional[MemorySqlManager]:
        """
        根据 IP 地址获取对应的 SQL 实例。

        Args:
            ip_address: 客户端 IP 地址

        Returns:
            MemorySqlManager 实例或 None
        """
        if CACHE_AVAILABLE:
            # TTLCache 模式下，从SessionInfo中获取SQL实例
            session_info = self._sessions.get(ip_address)
            if not session_info:
                return None
            return session_info.sql_instance
        else:
            # 手动管理模式
            session_info = await self.get_session_by_ip(ip_address)
            if not session_info:
                return None
            return session_info.sql_instance

    async def delete_session(self, ip_address: str) -> bool:
        """
        删除指定 IP 的会话。

        Args:
            ip_address: 客户端 IP 地址

        Returns:
            bool: 是否删除成功
        """
        if CACHE_AVAILABLE:
            # TTLCache 方式：直接删除
            session_existed = ip_address in self._sessions
            self._sessions.pop(ip_address, None)
            self._sql_instances.pop(ip_address, None)
            if session_existed:
                logger.info(f"セッションを削除: IP {ip_address} (TTLCacheモード)")
            return session_existed
        else:
            # 手动管理方式
            session_info = self._sessions.get(ip_address)
            if not session_info:
                return False
            
            del self._sql_instances[ip_address]
            del self._sessions[ip_address]
            logger.info(f"セッションを削除: IP {ip_address} (手動管理モード)")
            return True

    async def cleanup_all_sessions(self):
        """清理所有会话"""
        if CACHE_AVAILABLE:
            # TTLCache 方式：清空缓存
            count = len(self._sessions)
            self._sessions.clear()
            self._sql_instances.clear()
            logger.info(f"すべてのセッションをクリーンアップ ({count} 件) (TTLCacheモード)")
        else:
            # 手动管理方式
            ip_addresses = list(self._sessions.keys())
            for ip_address in ip_addresses:
                await self.delete_session(ip_address)
            logger.info("すべてのセッションをクリーンアップ (手動管理モード)")

    async def _cleanup_expired_sessions(self):
        """清理过期会话（仅在手动管理模式下使用）"""
        if CACHE_AVAILABLE:
            # TTLCache 自动处理，无需手动清理
            return
            
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        expired_sessions = []
        for ip_address, session_info in self._sessions.items():
            if session_info.is_expired:
                expired_sessions.append(ip_address)

        if expired_sessions:
            logger.info(f"期限切れセッション {len(expired_sessions)} 件をクリーンアップ")
            for ip_address in expired_sessions:
                await self.delete_session(ip_address)

        self._last_cleanup = current_time

    def get_active_session_count(self) -> int:
        """获取活跃会话数量"""
        if CACHE_AVAILABLE:
            # TTLCache 中的都是活跃会话
            return len(self._sessions)
        else:
            # 手动计算活跃会话
            active_count = 0
            for session_info in self._sessions.values():
                if not session_info.is_expired:
                    active_count += 1
            return active_count

    def get_sessions_summary(self) -> Dict:
        """获取会话摘要信息"""
        if CACHE_AVAILABLE:
            total_sessions = len(self._sessions)
            return {
                "total_sessions": total_sessions,
                "active_sessions": total_sessions,  # TTLCache中都是活跃的
                "expired_sessions": 0,
                "unique_ips": total_sessions,
                "mode": "TTLCache",
            }
        else:
            active_count = 0
            expired_count = 0
            unique_ips = set()

            for session_info in self._sessions.values():
                if session_info.is_expired:
                    expired_count += 1
                else:
                    active_count += 1
                unique_ips.add(session_info.ip_address)

            return {
                "total_sessions": len(self._sessions),
                "active_sessions": active_count,
                "expired_sessions": expired_count,
                "unique_ips": len(unique_ips),
                "cleanup_interval": self._cleanup_interval,
                "mode": "Manual",
            }
