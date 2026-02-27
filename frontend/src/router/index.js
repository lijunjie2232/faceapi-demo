import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import Login from '../views/Login.vue'
import Signup from '../views/Signup.vue'
import Admin from '../views/Admin.vue'
import User from '../views/User.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/user', // userページにリダイレクトしてデフォルトページとする
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/signup',
    name: 'Signup',
    component: Signup
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/user',
    name: 'User',
    component: User,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// グローバル前置ガード
router.beforeEach(async (to, from, next) => {
  console.log('[ROUTER] 导航:', from.path, '->', to.path, '| 需要认证:', to.meta.requiresAuth);
  
  // ルートが認証を必要とするかどうかをチェック
  if (to.meta.requiresAuth) {
    const userToken = localStorage.getItem('user_token');
    
    console.log('[ROUTER] 用户认证检查 - user_token:', !!userToken);
    
    // 如果没有用户令牌，重定向到登录页
    if (!userToken) {
      console.log('[ROUTER] 无用户令牌，重定向到登录页');
      ElMessage.warning('请先登录');
      next('/login');
      return;
    }
    
    // 检查管理员权限
    if (to.meta.requiresAdmin) {
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
      console.log('[ROUTER] 管理员权限检查:', userInfo.is_admin);
      
      if (!userInfo.is_admin) {
        ElMessage.error('拒绝访问：需要管理员权限');
        next('/user');
        return;
      }
    }
    
    console.log('[ROUTER] 用户认证通过，允许访问');
    next();
  } else {
    console.log('[ROUTER] 无需认证，直接通过');
    next();
  }
});

export default router;