"""
兼容性层模块。

此模块提供统一的接口，使服务层代码可以同时支持
真实的数据库连接和内存管理器，无需修改业务逻辑。
"""

from typing import Any, Dict, List, Optional, Union
from ..core import _CONFIG_
from ..db import (
    is_using_memory_manager,
    is_using_memory_sql
)
from ..models.user import UserModel


class DictToObjectWrapper:
    """将字典包装成对象，支持属性访问"""
    def __init__(self, data_dict: Dict):
        self._data = data_dict
        self._sql_client = None  # 用于保存操作
    
    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        # 处理私有属性
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            # 设置数据字典中的值
            if hasattr(self, '_data'):
                self._data[name] = value
            else:
                super().__setattr__(name, value)
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def __contains__(self, key):
        return key in self._data
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def to_dict(self):
        return self._data.copy()
    
    async def save(self):
        """保存更改到数据库"""
        if self._sql_client and 'id' in self._data:
            # 使用SQL客户端更新用户
            await self._sql_client.update_user(self._data['id'], **self._data)
        # 如果没有SQL客户端，就地更新（适用于内存模式）
        # 在内存模式下，数据已经在_data中更新了


class CompatibleUserModel:
    """兼容的用户模型类，自动适配真实数据库或内存管理器"""
    
    def __init__(self):
        self._real_model = UserModel
        self._memory_client = None
        
    async def _ensure_memory_client(self):
        """确保内存客户端已初始化"""
        if self._memory_client is None:
            from ..db.memory_managers import get_memory_sql_client
            self._memory_client = await get_memory_sql_client()
            
    async def get_or_none(self, *args, **kwargs):
        """获取用户或返回None"""
        if is_using_memory_sql():
            await self._ensure_memory_client()
            user_dict = await self._memory_client.get_user(*args, **kwargs)
            if user_dict:
                # 将字典包装成对象
                return DictToObjectWrapper(user_dict)
            return None
        else:
            return await self._real_model.get_or_none(*args, **kwargs)
            
    async def get(self, *args, **kwargs):
        """获取用户，如果不存在则抛出异常"""
        if is_using_memory_sql():
            await self._ensure_memory_client()
            user_dict = await self._memory_client.get_user(*args, **kwargs)
            if not user_dict:
                raise ValueError("User not found")
            return DictToObjectWrapper(user_dict)
        else:
            return await self._real_model.get(*args, **kwargs)
            
    async def create(self, **kwargs):
        """创建用户"""
        if is_using_memory_sql():
            await self._ensure_memory_client()
            user_dict = await self._memory_client.create_user(**kwargs)
            return DictToObjectWrapper(user_dict)
        else:
            return await self._real_model.create(**kwargs)
            
    async def filter(self, **kwargs):
        """过滤用户"""
        if is_using_memory_sql():
            await self._ensure_memory_client()
            # 内存管理器的filter方法是异步的，需要await
            return await self._memory_client.filter(**kwargs)
        else:
            return await self._real_model.filter(**kwargs)
            
    async def all(self):
        """获取所有用户"""
        if is_using_memory_sql():
            await self._ensure_memory_client()
            users = await self._memory_client.list_users()
            # 包装成类似QuerySet的对象
            class MockQuerySet:
                def __init__(self, users):
                    self.users = users
                    
                async def count(self):
                    return len(self.users)
                    
                async def offset(self, skip):
                    return MockQuerySet(self.users[skip:])
                    
                async def limit(self, limit):
                    # 包装字典为对象
                    wrapped_users = [DictToObjectWrapper(user) for user in self.users[:limit]]
                    return wrapped_users
                    
                def filter(self, condition):
                    # 简化的过滤逻辑
                    return self
                    
            return MockQuerySet(users)
        else:
            return self._real_model.all()


# 创建全局兼容模型实例
COMPATIBLE_USER_MODEL = CompatibleUserModel()


def get_compatible_sql_client():
    """获取兼容的 SQL 客户端"""
    if is_using_memory_manager():
        from ..db.memory_managers import get_memory_sql_client
        return get_memory_sql_client()
    else:
        # 对于真实数据库，返回实际的 SQL 客户端
        raise NotImplementedError("Real SQL client not implemented")


def get_compatible_user_model():
    """获取兼容的用户模型"""
    return COMPATIBLE_USER_MODEL


# 重新导出常用的函数和类
from ..models.user import UserModel  # 保留原始导入以便类型提示