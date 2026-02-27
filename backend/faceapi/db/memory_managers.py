"""
内存数据库管理器模块。

此模块提供内存中的数据库管理器，用于演示目的，
模拟 Milvus 向量数据库和 SQL 关系数据库的功能。
适用于用户数量有限（最多5个用户）的演示场景。
"""

import base64
import json
import time
from typing import Any, Dict, List, Optional, Union
from loguru import logger
import numpy as np


class MemorySqlManager:
    """
    内存中的 SQL 数据库管理器。
    
    模拟关系数据库的用户表操作功能。
    支持用户创建、查询、更新和删除操作。
    """
    
    def __init__(self):
        """初始化内存 SQL 管理器"""
        self.users = {}  # 用户存储 {user_id: user_data}
        self.next_id = 1
        self._initialized = False
        
    async def initialize(self):
        """初始化数据库连接（模拟）"""
        if not self._initialized:
            logger.info("初始化内存 SQL 管理器")
            # 创建默认管理员用户
            await self._create_default_admin()
            self._initialized = True
            
    async def _create_default_admin(self):
        """创建默认管理员用户"""
        from ..utils.pass_utils import hash_password
        from ..core import _CONFIG_
        
        # 检查是否已存在管理员用户
        existing_admin = await self.get_user_by_username("admin")
        if not existing_admin:
            # 使用配置中的密码，如果没有则使用默认值
            admin_password = getattr(_CONFIG_, 'ADMIN_PASSWORD', 'admin')
            hashed_password = hash_password(admin_password)
            admin_user = await self.create_user(
                username="admin",
                email=getattr(_CONFIG_, 'ADMIN_EMAIL', 'admin@example.com'),
                full_name=getattr(_CONFIG_, 'ADMIN_FULL_NAME', 'Administrator'),
                hashed_password=hashed_password,
                is_active=True,
                is_admin=True
            )
            logger.info(f"创建默认管理员用户: {admin_user['username']} (ID: {admin_user['id']})")
            
    async def create_user(self, username: str, email: str, full_name: str = None,
                         hashed_password: str = None, is_active: bool = True,
                         is_admin: bool = False, head_pic: str = None, 
                         embedding: list = None) -> Dict:
        """创建新用户"""
        # 检查用户名和邮箱是否已存在
        for user in self.users.values():
            if user['username'] == username:
                raise ValueError("Username already taken")
            if user['email'] == email:
                raise ValueError("Email already registered")
                
        user_id = self.next_id
        self.next_id += 1
        
        user_data = {
            'id': user_id,
            'username': username,
            'email': email,
            'full_name': full_name,
            'hashed_password': hashed_password,
            'is_active': is_active,
            'is_admin': is_admin,
            'head_pic': head_pic,
            'embedding': embedding,
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
        self.users[user_id] = user_data
        logger.info(f"创建用户: {username} (ID: {user_id})")
        return user_data
        
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        return self.users.get(user_id)
        
    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        for user in self.users.values():
            if user['username'] == username:
                return user
        return None
        
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """根据邮箱获取用户"""
        for user in self.users.values():
            if user['email'] == email:
                return user
        return None
        
    async def get_user(self, *args, **kwargs) -> Optional[Dict]:
        """通用用户查询方法"""
        if 'id' in kwargs:
            return await self.get_user_by_id(kwargs['id'])
        elif 'username' in kwargs:
            return await self.get_user_by_username(kwargs['username'])
        elif 'email' in kwargs:
            return await self.get_user_by_email(kwargs['email'])
        return None
        
    async def get_or_none(self, *args, **kwargs) -> Optional[Dict]:
        """获取用户或返回None"""
        return await self.get_user(*args, **kwargs)
        
    async def filter(self, **kwargs):
        """过滤用户（模拟 Tortoise ORM 的 filter 方法）"""
        class FilterResult:
            def __init__(self, manager, filters):
                self.manager = manager
                self.filters = filters
                
            async def update(self, **update_data):
                """更新匹配的用户"""
                updated_count = 0
                for user_id, user in self.manager.users.items():
                    match = True
                    for key, value in self.filters.items():
                        if user.get(key) != value:
                            match = False
                            break
                    if match:
                        user.update(update_data)
                        user['updated_at'] = time.time()
                        updated_count += 1
                return updated_count
                
            async def delete(self):
                """删除匹配的用户"""
                to_delete = []
                for user_id, user in self.manager.users.items():
                    match = True
                    for key, value in self.filters.items():
                        if user.get(key) != value:
                            match = False
                            break
                    if match:
                        to_delete.append(user_id)
                        
                for user_id in to_delete:
                    del self.manager.users[user_id]
                return len(to_delete)
                
        return FilterResult(self, kwargs)
        
    async def update_user(self, user_id: int, **update_data) -> bool:
        """更新用户信息"""
        if user_id in self.users:
            self.users[user_id].update(update_data)
            self.users[user_id]['updated_at'] = time.time()
            return True
        return False
        
    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
        
    async def list_users(self) -> List[Dict]:
        """列出所有用户"""
        return list(self.users.values())
        
    async def count_users(self) -> int:
        """统计用户数量"""
        return len(self.users)
        
    async def search_face_embeddings(self, query_vector: List[float], 
                                   limit: int = 1, threshold: float = 0.3) -> List[Dict]:
        """在用户嵌入向量中搜索相似的人脸特征"""
        results = []
        
        for user_id, user_data in self.users.items():
            # logger.debug(user_data)
            if user_data.get('embedding') is not None:
                similarity = self._cosine_similarity(query_vector, user_data['embedding'])
                logger.debug(f"Similarity for user {user_id}: {similarity}")
                if similarity >= threshold:
                    results.append({
                        'entity': {
                            'user_id': user_id
                        },
                        'distance': 1 - similarity,  # 转换为距离
                        'id': user_id
                    })
        
        # 按相似度排序并限制结果数量
        results.sort(key=lambda x: x['distance'])
        return [results[:limit]] if results else [[]]
        
    async def upsert_face_embedding(self, user_id: int, feature_vector: List[float]) -> Dict:
        """插入或更新用户的人脸嵌入向量"""
        if user_id in self.users:
            self.users[user_id]['embedding'] = feature_vector
            self.users[user_id]['updated_at'] = time.time()
            return {"insertedIds": [user_id]}
        else:
            raise ValueError(f"User with id {user_id} not found")
            
    async def delete_face_embedding(self, user_id: int) -> Dict:
        """删除用户的人脸嵌入向量"""
        if user_id in self.users:
            self.users[user_id]['embedding'] = None
            self.users[user_id]['head_pic'] = None
            self.users[user_id]['updated_at'] = time.time()
            return {"deleted_count": 1}
        else:
            return {"deleted_count": 0}
            
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""        
        # 转换为numpy数组
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # 计算点积
        dot_product = np.dot(v1, v2)
        
        # 计算向量的模长
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        # 避免除零错误
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        # 计算余弦相似度
        return float(dot_product / (norm1 * norm2))
        
    def get_user_model_mock(self):
        """获取用户模型的模拟对象（用于兼容现有代码）"""
        class UserModelMock:
            @staticmethod
            async def get_or_none(*args, **kwargs):
                return await self.get_or_none(*args, **kwargs)
                
            @staticmethod
            async def get(*args, **kwargs):
                user = await self.get_user(*args, **kwargs)
                if not user:
                    raise ValueError("User not found")
                return user
                
            @staticmethod
            async def create(**kwargs):
                return await self.create_user(**kwargs)
                
            @staticmethod
            async def filter(**kwargs):
                return await self.filter(**kwargs)
                
        return UserModelMock()


# 导出函数保持与原接口兼容
async def get_memory_milvus_client():
    """获取内存 Milvus 客户端实例"""
    await MEMORY_MILVUS_MANAGER.initialize()
    return MEMORY_MILVUS_MANAGER
    
async def get_memory_sql_client():
    """获取内存 SQL 客户端实例"""
    await MEMORY_SQL_MANAGER.initialize()
    return MEMORY_SQL_MANAGER


# 简单的内存Milvus管理器（为保持接口兼容性）
class MemoryMilvusManager:
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            logger.info("初始化内存 Milvus 管理器（模拟）")
            self._initialized = True
    
    async def search_face_embeddings(self, query_vector, limit=1, threshold=0.3):
        # 模拟搜索，返回空结果
        return [[]]
    
    async def upsert_face_embedding(self, user_id, feature_vector):
        # 模拟插入，返回成功
        return {"insertedIds": [user_id]}

# 全局实例
MEMORY_SQL_MANAGER = MemorySqlManager()
MEMORY_MILVUS_MANAGER = MemoryMilvusManager()

# async def test_default_admin_creation():
#     """测试默认管理员用户创建功能"""
#     print("=== 测试默认管理员用户创建 ===")
    
#     # 初始化管理器
#     await MEMORY_SQL_MANAGER.initialize()
    
#     # 获取管理员用户
#     admin_user = await MEMORY_SQL_MANAGER.get_user_by_username("admin")
    
#     if admin_user:
#         print(f"✓ 找到管理员用户:")
#         print(f"  - 用户名: {admin_user['username']}")
#         print(f"  - 邮箱: {admin_user['email']}")
#         print(f"  - 全名: {admin_user['full_name']}")
#         print(f"  - 是否管理员: {admin_user['is_admin']}")
#         print(f"  - 是否激活: {admin_user['is_active']}")
#         print(f"  - 用户ID: {admin_user['id']}")
        
#         # 验证密码
#         from ..utils.pass_utils import verify_password
#         password_valid = verify_password("admin", admin_user['hashed_password'])
#         print(f"  - 密码验证: {'✓ 正确' if password_valid else '✗ 错误'}")
        
#         # 尝试错误密码
#         wrong_password_valid = verify_password("wrong_password", admin_user['hashed_password'])
#         print(f"  - 错误密码验证: {'✓ 正确' if wrong_password_valid else '✗ 错误'}")
        
#     else:
#         print("✗ 未找到管理员用户")
        
#     # 列出所有用户
#     all_users = await MEMORY_SQL_MANAGER.list_users()
#     print(f"\n=== 所有用户 ({len(all_users)} 个) ===")
#     for user in all_users:
#         print(f"- {user['username']} ({'管理员' if user['is_admin'] else '普通用户'})")
        
#     return admin_user is not None