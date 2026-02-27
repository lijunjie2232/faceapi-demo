import axios from 'axios';
import { ElMessage, ElNotification } from 'element-plus';

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
});

// 请求拦截器 - 自动添加Session-Token头
apiClient.interceptors.request.use(
  (config) => {
    // 获取会话令牌
    const sessionToken = localStorage.getItem('session_token');
    
    // 除了创建会话的API外，其他所有请求都需要Session-Token
    config.headers['Session-Token'] = sessionToken;

    // ローカルストレージからトークンを取得
    const token = localStorage.getItem('user_token');

    config.headers['Authorization'] = `Bearer ${token}`;
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理会话过期等情况
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 处理会话过期的情况
    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('sessionExpired'));
    }
    // 处理会话不存在或已过期的情况
    else if (error.response?.status === 404) {
      const detail = error.response.data?.detail || '';
      if (detail.includes('セッションが存在しません') || detail.includes('セッションが存在しないか期限切れです')) {
        window.dispatchEvent(new CustomEvent('sessionCleaned'));
      }
    }
    return Promise.reject(error);
  }
);

// 监听会话过期事件
window.addEventListener('sessionExpired', () => {
  // 只清除用户认证相关的信息，保留会话令牌
  localStorage.removeItem('user_token');
  localStorage.removeItem('username');
  localStorage.removeItem('userInfo');
  
  // 重定向到根路径
  window.location.href = '/';
});

// 监听会话清理事件（404响应）
window.addEventListener('sessionCleaned', () => {
  // 不自动清除会话令牌，触发重新初始化事件
  // 让重新初始化函数决定是否清除和创建新令牌
  window.dispatchEvent(new CustomEvent('reinitializeSession'));
});

// 会话管理相关函数
let sessionToken = '';
let creatingSession = false;
let sessionCheckPromise = null;
let routerInstance = null;

// 设置路由器实例
export const setRouter = (router) => {
  routerInstance = router;
};

// 获取会话令牌
export const getSessionToken = () => {
  return sessionToken;
};

// 设置会话令牌
export const setSessionToken = (token) => {
  sessionToken = token;
  if (token) {
    localStorage.setItem('session_token', token);
  }
};

// 创建新会话
export const createNewSession = async () => {
  // 防止重复创建会话
  if (creatingSession || sessionCheckPromise) {
    console.log('[API.JS] セッション作成中、重複リクエストをスキップ');
    return sessionCheckPromise;
  }

  creatingSession = true;
  sessionCheckPromise = (async () => {
    try {
      console.log('[API.JS] セッション作成リクエストを送信');
      const response = await apiClient.post('/api/v1/session/create');
      
      if (response.data.code === 200 && response.data.token) {
        sessionToken = response.data.token;
        localStorage.setItem('session_token', sessionToken);
        ElNotification.success({
          title: 'セッション作成成功',
          message: `セッション有効期限: ${Math.floor(response.data.expires_in / 60)} 分`,
          duration: 3000
        });
        console.log('[API.JS] セッション作成成功');
        return { success: true, token: sessionToken };
      } else {
        throw new Error(response.data.detail || 'セッション作成に失敗しました');
      }
    } catch (error) {
      console.error('[API.JS] セッション作成に失敗しました:', error.response?.data?.detail || error.message);
      const errorMsg = error.response?.data?.detail || error.message || '不明なエラー';
      ElNotification.error({
        title: 'セッション作成に失敗しました',
        message: errorMsg,
        duration: 5000
      });
      return { success: false, error: errorMsg };
    } finally {
      creatingSession = false;
      sessionCheckPromise = null;
    }
  })();
  
  return sessionCheckPromise;
};

// 验证存储的会话
export const validateStoredSession = async () => {
  console.log('[API.JS] 保存されたセッションを検証');
  
  try {
    const response = await apiClient.get('/api/v1/session/info', {
      headers: {
        'Session-Token': sessionToken
      }
    });
    
    const isValid = response.data.code === 200 && !response.data.is_expired;
    console.log('[API.JS] 検証結果:', isValid, '| レスポンスコード:', response.data.code);
    return isValid;
  } catch (error) {
    console.log('[API.JS] 検証に失敗しました:', error.response?.data?.detail || error.message);
    return false;
  }
};

// 初始化会话
export const initializeSession = async () => {
  console.log('[API.JS] セッション初期化開始');
  
  try {
    // 检查本地存储的会话令牌
    const storedToken = localStorage.getItem('session_token');
    console.log('[API.JS] 保存されたトークンの存在:', !!storedToken);
    
    if (storedToken) {
      sessionToken = storedToken;
      const isValid = await validateStoredSession();
      if (isValid) {
        console.log('[API.JS] 保存されたセッションは有効です');
        return { success: true, initialized: true };
      } else {
        console.log('[API.JS] 保存されたセッションは無効です');
        // 清除无效的会话令牌
        localStorage.removeItem('session_token');
        sessionToken = '';
      }
    }
    
    // 尝试创建新会话
    console.log('[API.JS] 新しいセッションを作成');
    const result = await createNewSession();
    if (result.success) {
      console.log('[API.JS] 新しいセッション作成成功');
      ElMessage.success('セッション作成成功、ようこそ！');
      return { success: true, initialized: true };
    } else {
      console.log('[API.JS] 新しいセッション作成に失敗しました');
      return { success: false, error: result.error };
    }
  } catch (error) {
    console.error('[API.JS] セッション初期化例外:', error);
    return { success: false, error: error.message };
  }
};

// 处理会话过期
export const handleSessionExpired = () => {
  console.log('セッション期限切れ');
  
  // 触发会话过期事件，让全局处理器处理重定向
  window.dispatchEvent(new CustomEvent('sessionExpired'));
  
  ElNotification.warning({
    title: 'セッション期限切れ',
    message: 'ホームページに戻ります',
    duration: 3000
  });
};

// 处理会话删除
export const handleSessionDeleted = () => {
  console.log('セッションが削除されました');
  // 清除会话令牌和用户相关信息
  sessionToken = '';
  localStorage.removeItem('session_token');
  localStorage.removeItem('user_token');
  localStorage.removeItem('username');
  localStorage.removeItem('userInfo');
  
  // 触发会话过期事件，让全局处理器处理重定向
  window.dispatchEvent(new CustomEvent('sessionExpired'));
  
  ElMessage.info('セッションが削除されました、ホームページに戻ります');
};

// 重试创建会话
export const retryCreateSession = async () => {
  console.log('[API.JS] 会话重试创建开始');
  
  // 清除现有的会话令牌
  localStorage.removeItem('session_token');
  sessionToken = '';
  
  // 重新初始化会话
  const result = await initializeSession();
  console.log('[API.JS] 会话重试结果:', result);
  
  return result;
};

// 检查现有会话
export const checkExistingSession = async () => {
  try {
    const response = await apiClient.get('/api/v1/session/current');
    if (response.data.code === 200) {
      ElMessage.info('既存のセッションが検出されました、セッション期限切れ後に再試行してください');
      return { hasSession: true };
    } else {
      ElMessage.info('現在アクティブなセッションはありません、再作成を試みてください');
      return { hasSession: false };
    }
  } catch (error) {
    ElMessage.error('セッション状態の確認に失敗しました');
    return { hasSession: false, error: error.message };
  }
};

// 重新初始化会话
export const reinitializeSession = async () => {
  console.log('[API.JS] セッションを再初期化...');
  
  // 清除现有会话信息
  sessionToken = '';
  localStorage.removeItem('session_token');
  
  // 重新初始化会话
  const result = await initializeSession();
  console.log('[API.JS] 再初期化结果:', result);
  
  if (result.success) {
    ElNotification.success({
      title: 'セッション更新成功',
      message: 'セッションが再作成されました',
      duration: 3000
    });
  } else {
    ElNotification.error({
      title: 'セッション更新失败',
      message: result.error || 'セッションの再作成に失敗しました',
      duration: 5000
    });
  }
  
  return result;
};

// 检查是否有有效会话
export const hasValidSession = () => {
  return sessionToken !== '';
};

export default apiClient;