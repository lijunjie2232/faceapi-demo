<template>
  <div id="app">
    <!-- 会话管理浮动框 -->
    <SessionManager 
      :api-base-url="API_BASE_URL"
      :session-token="sessionToken"
      @session-expired="handleSessionExpired"
      @session-deleted="handleSessionDeleted"
    />

    <el-container v-if="hasValidSession">
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="app-title">
            <el-icon>
              <User />
            </el-icon>
            <span>Face Recognition System (Demo)</span>
          </h1>
          <div class="user-actions">
            <el-button v-if="userInfo && userInfo.is_admin" class="admin-link-btn" type="text" @click="goToAdmin">
              <el-icon>
                <Management />
              </el-icon>
              <span>Admin</span>
            </el-button>
            <el-dropdown placement="bottom-end">
              <el-button class="user-profile-btn" type="text">
                <span class="user-name">{{ username }}</span>
                <el-icon>
                  <ArrowDown />
                </el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="goToProfile">Profile</el-dropdown-item>
                  <el-dropdown-item @click="logout">Logout</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>

      <el-footer class="app-footer">
        <p class="footer-text">Face Recognition System &copy; {{ currentYear }} | Advanced Facial Recognition Technology
        </p>
      </el-footer>
    </el-container>

    <!-- 无有效会话时不显示任何内容 -->
    <div v-if="!hasValidSession && initializing" class="initializing-screen">
      <div class="loading-content">
        <el-skeleton :rows="5" animated />
        <p class="loading-text">正在初始化会话...</p>
      </div>
    </div>

    <!-- 会话创建失败提示 -->
    <div v-if="sessionCreationFailed" class="session-error-screen">\      <div class="error-content">
        <el-result
          icon="error"
          title="无法创建会话"
          sub-title="当前IP已有活跃会话或服务器暂时不可用，请稍后再试"
        >
          <template #extra>
            <el-button type="primary" @click="retryCreateSession">重试</el-button>
            <el-button @click="checkExistingSession">检查现有会话</el-button>
          </template>
        </el-result>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElNotification } from 'element-plus';
import { User, ArrowDown, Management } from '@element-plus/icons-vue';
import apiClient from './utils/api';
import { provide } from 'vue';
import SessionManager from './components/SessionManager.vue';

const showMainApp = ref(false);
const username = ref('');
const currentYear = new Date().getFullYear();
const router = useRouter();
const route = useRoute();
const userInfo = ref({});
const loading = ref(true);
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

// 会话管理相关
const sessionToken = ref('');
const initializing = ref(true);
const sessionCreationFailed = ref(false);
const creatingSession = ref(false);
const sessionCheckPromise = ref(null); // 防止重复创建会话

// 计算属性
const hasValidSession = computed(() => {
  return sessionToken.value !== '';
});

// 子コンポーネントにuserInfoを提供
provide('userInfo', userInfo);

// 提供会话令牌给子组件
provide('sessionToken', sessionToken);
provide('hasValidSession', hasValidSession);

// 会话管理函数
const createNewSession = async () => {
  // 防止重复创建会话
  if (creatingSession.value || sessionCheckPromise.value) {
    console.log('会话创建已在进行中，跳过重复请求');
    return sessionCheckPromise.value;
  }

  creatingSession.value = true;
  sessionCheckPromise.value = (async () => {
    try {
      console.log('开始创建新会话...');
      const response = await apiClient.post('/api/v1/session/create');
      
      if (response.data.code === 200 && response.data.token) {
        sessionToken.value = response.data.token;
        localStorage.setItem('session_token', sessionToken.value);
        sessionCreationFailed.value = false;
        ElNotification.success({
          title: '会话创建成功',
          message: `会话有效期: ${Math.floor(response.data.expires_in / 3600)}小时`,
          duration: 3000
        });
        console.log('会话创建成功');
        return true;
      } else {
        throw new Error(response.data.detail || '会话创建失败');
      }
    } catch (error) {
      console.error('创建会话失败:', error);
      sessionCreationFailed.value = true;
      sessionToken.value = '';
      localStorage.removeItem('session_token');
      
      const errorMsg = error.response?.data?.detail || error.message || '未知错误';
      ElNotification.error({
        title: '会话创建失败',
        message: errorMsg,
        duration: 5000
      });
      return false;
    } finally {
      creatingSession.value = false;
      sessionCheckPromise.value = null;
    }
  })();
  
  return sessionCheckPromise.value;
};

const validateStoredSession = async () => {
  try {
    console.log('验证存储的会话令牌...');
    const response = await apiClient.get('/api/v1/session/info', {
      headers: {
        'Session-Token': sessionToken.value
      }
    });
    
    if (response.data.code === 200 && !response.data.is_expired) {
      console.log('存储的会话令牌有效');
      return true;
    } else {
      console.log('存储的会话令牌已过期或无效');
      sessionToken.value = '';
      localStorage.removeItem('session_token');
      return false;
    }
  } catch (error) {
    console.log('存储的会话令牌验证失败:', error.message);
    sessionToken.value = '';
    localStorage.removeItem('session_token');
    return false;
  }
};

const initializeSession = async () => {
  initializing.value = true;
  sessionCreationFailed.value = false;
  
  try {
    // 首先检查本地存储的会话令牌
    const storedToken = localStorage.getItem('session_token');
    if (storedToken) {
      sessionToken.value = storedToken;
      const isValid = await validateStoredSession();
      if (isValid) {
        console.log('使用有效的存储会话');
        initializing.value = false;
        return;
      }
    }
    
    // 尝试创建新会话
    console.log('尝试创建新会话...');
    const sessionCreated = await createNewSession();
    if (sessionCreated) {
      console.log('新会话创建成功');
    } else {
      console.log('新会话创建失败');
    }
  } finally {
    initializing.value = false;
  }
};

// 事件处理函数
const handleSessionExpired = () => {
  console.log('会话已过期');
  sessionToken.value = '';
  localStorage.removeItem('session_token');
  sessionCreationFailed.value = false;
  ElNotification.warning({
    title: '会话已过期',
    message: '请重新创建会话',
    duration: 3000
  });
};

const handleSessionDeleted = () => {
  console.log('会话已被删除');
  sessionToken.value = '';
  localStorage.removeItem('session_token');
  sessionCreationFailed.value = false;
  showMainApp.value = false;
  router.push('/login');
  ElMessage.info('会话已删除，请重新登录');
};

const retryCreateSession = async () => {
  sessionCreationFailed.value = false;
  await initializeSession();
};

const checkExistingSession = async () => {
  try {
    const response = await apiClient.get('/api/v1/session/current');
    if (response.data.code === 200) {
      ElMessage.info('检测到现有会话，请等待会话过期后再试');
    } else {
      ElMessage.info('当前无活跃会话，可以尝试重新创建');
      sessionCreationFailed.value = false;
    }
  } catch (error) {
    ElMessage.error('检查会话状态失败');
  }
};

// APIからユーザー情報を取得
const fetchUserInfo = async () => {
  try {
    loading.value = true;

    // ローカルストレージからトークンを取得
    const token = localStorage.getItem('token');

    // 認証ヘッダー付きでAPIリクエストを行う
    const response = await apiClient.get('/api/v1/user/me', {
      headers: {
        'Authorization': `Bearer ${token}`  // Bearerトークン形式を使用
      }
    });

    if (response.data.code === 200) {
      userInfo.value = response.data.data;
      localStorage.setItem('username', userInfo.value.username);
      localStorage.setItem('userInfo', JSON.stringify(response.data.data)); // 完全なユーザー情報を保存
      username.value = userInfo.value.username;
    } else if (response.data.detail === "Not authenticated") {
      // トークンが無効、再度ログインが必要
      // console.error('トークンが無効です、ログインページにリダイレクトします');
      // ローカルストレージをクリア
      localStorage.removeItem('token'); // トークンも削除
      localStorage.removeItem('username'); // ユーザー名も削除
      localStorage.removeItem('userInfo'); // ユーザー情報も削除
    } else {
      // console.error('ユーザー情報の取得に失敗しました:', response.data.message);
    }
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail === "Not authenticated") {
      // トークンが無効、再度ログインが必要
      // console.error('トークンが無効です、ログインページにリダイレクトします');
      // ローカルストレージをクリア
      localStorage.removeItem('token'); // トークンも削除
      localStorage.removeItem('uesrname'); // ユーザー名も削除
    } else {
      // console.error('ユーザー情報の取得中にエラーが発生しました:', error);
    }
  } finally {
    loading.value = false;
  }
};

const checkLoginStatus = async () => {
  try {
    // 检查是否有有效的会话令牌
    if (!hasValidSession.value) {
      // 如果不在登录/注册页面，重定向到登录页
      if (route.path !== '/login' && route.path !== '/signup' && route.path !== '/') {
        router.push('/login');
      }
      return;
    }
    
    // userInfoの代わりにlocalStorageからユーザートークンを確認
    const token = localStorage.getItem('token');
    if (token) {
      await fetchUserInfo();
      // 現在ログイン/サインアップページにいるが認証されている場合、ルートに基づいてリダイレクト
      if (route.path === '/login' || route.path === '/signup') {
        // ログインページから来た場合は、デフォルトページ（ユーザー）に移動
        router.push('/user');
      }
    } else {
      // 用户未登录，但会话有效，可以显示主界面
      // 不再强制重定向到登录页，允许用户先看到界面再登录
      if (route.path !== '/login' && route.path !== '/signup' && route.path !== '/') {
        // 可以选择是否重定向到登录页，或者保持当前位置
        // router.push('/login');
      }
    }
  } catch (error) {
    console.error('登录状态检查失败:', error);
    // 即使检查失败，只要有有效会话就保持显示主界面
  }
};

// 子コンポーネントにcheckLoginStatus関数を提供
provide('checkLoginStatus', checkLoginStatus);

const logout = async () => {
  try {
    // ローカルストレージからトークンとユーザー情報をクリア
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('userInfo'); // ユーザー情報も削除
    username.value = '';
    userInfo.value = {};
    showMainApp.value = false;
    await router.push('/login');
    ElMessage.success('正常にログアウトしました');
  } catch (error) {
    // console.error('ログアウトに失敗しました:', error);
    ElMessage.error('ログアウトに失敗しました');
  }
};

const goToProfile = () => {
  router.push('/user');
};

const goToAdmin = () => {
  router.push('/admin');
};

onMounted(async () => {
  // 首先初始化会话
  await initializeSession();
  // 然后检查登录状态
  if (hasValidSession.value) {
    checkLoginStatus();
  }
});

// 监听会话状态变化
watch(hasValidSession, (newVal) => {
  if (newVal) {
    checkLoginStatus();
  }
});

// ルート変更を監視
router.afterEach(() => {
  checkLoginStatus();
});

</script>

<style>

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #409EFF 0%, #327de8 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 0;
  height: 80px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  /* max-width: 1200px; */
  padding: 0 40px;
}

.app-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.app-title .el-icon {
  font-size: 28px;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-profile-btn {
  color: white;
  padding: 0 10px;
}

.admin-link-btn {
  color: white;
  padding: 0 10px;
  margin-right: 10px;
}

.admin-link-btn .el-icon {
  margin-right: 5px;
}

.user-name {
  font-weight: 500;
  margin-right: 5px;
}

.app-main {
  flex: 1;
  padding: 20px 0;
  background-color: #f0f2f5;
}

.app-footer {
  background-color: #323a45;
  color: white;
  text-align: center;
  padding: 15px 0;
  margin-top: auto;
}

.footer-text {
  margin: 0;
  font-size: 14px;
  color: #aeb7c2;
}

/* 他のページ用の汎用スタイルを保持 */
.admin-panel {
  min-height: calc(100vh - 80px - 65px);
}

.initializing-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: white;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.loading-content {
  text-align: center;
  max-width: 400px;
  padding: 20px;
}

.loading-text {
  margin-top: 20px;
  font-size: 16px;
  color: #606266;
}

.session-error-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: white;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.error-content {
  max-width: 500px;
  width: 100%;
  padding: 20px;
}
</style>