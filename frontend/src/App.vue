<template>
  <div id="app">
    <!-- セッションチェック段階 - 基本ロード画面のみ表示 -->
    <div v-if="sessionChecking" class="session-check-screen">
      <div class="checking-content">
        <el-skeleton :rows="5" animated />
        <p class="checking-text">セッション状態を確認中...</p>
      </div>
    </div>

    <!-- セッション作成失敗通知 -->
    <div v-else-if="sessionCreationFailed" class="session-error-screen">
      <div class="error-content">
        <el-result
          icon="error"
          title="セッションを作成できません"
          :sub-title="errorMessage || '現在のIPには既にアクティブなセッションがあるか、サーバーが一時的に利用できません。後でもう一度お試しください'"
        >
          <template #extra>
            <el-button type="primary" @click="handleRetryCreateSession" :loading="retrying">再試行</el-button>
            <el-button @click="checkCurrentSessionStatus">既存セッションを確認</el-button>
          </template>
        </el-result>
      </div>
    </div>

    <!-- セッション有効時にメインアプリを表示 -->
    <template v-else-if="isSessionValid">
      <!-- セッション管理フローティングボックス -->
      <SessionManager 
        :api-base-url="API_BASE_URL"
        :session-token="sessionToken"
        @session-expired="handleSessionExpired"
        @session-deleted="handleSessionDeleted"
      />

      <el-container>
        <el-header class="app-header">
          <div class="header-content">
            <h1 class="app-title">
              <el-icon>
                <User />
              </el-icon>
              <span>顔認識システム（デモ）</span>
            </h1>
            <div class="user-actions">
              <el-button v-if="userInfo && userInfo.is_admin" class="admin-link-btn" type="text" @click="goToAdmin">
                <el-icon>
                  <Management />
                </el-icon>
                <span>管理者</span>
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
                    <el-dropdown-item @click="goToProfile">プロフィール</el-dropdown-item>
                    <el-dropdown-item @click="logout">ログアウト</el-dropdown-item>
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
          <p class="footer-text">顔認識システム &copy; {{ currentYear }} | 高度な顔認識技術
          </p>
        </el-footer>
      </el-container>
    </template>

    <!-- フォールバック状況 - 空状態を表示 -->
    <div v-else class="empty-state-screen">
      <div class="empty-content">
        <el-empty description="不明な状態、ページを更新してもう一度お試しください" />
        <el-button @click="refreshPage">ページを更新</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElNotification } from 'element-plus';
import { User, ArrowDown, Management } from '@element-plus/icons-vue';
import apiClient, { 
  setRouter,
  getSessionToken,
  setSessionToken,
  initializeSession,
  handleSessionExpired,
  handleSessionDeleted,
  retryCreateSession as apiRetryCreateSession,
  checkExistingSession,
  reinitializeSession
} from './utils/api';
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

// セッション管理関連状態
const sessionToken = ref('');
const sessionChecking = ref(true);  // セッション確認中
const sessionCreationFailed = ref(false);  // セッション作成失敗
const errorMessage = ref('');  // エラーメッセージ
const retrying = ref(false);  // 再試行中
const hasValidSessionComputed = ref(false);  // 有効なセッションがあるかどうか

// 算出プロパティ - セッションが有効かどうか
const isSessionValid = computed(() => {
  const result = hasValidSessionComputed.value && sessionToken.value !== '';
  console.log('[APP.VUE] セッション有効性計算:', result, '| トークン存在:', !!sessionToken.value);
  return result;
});

// セッション作成を再試行
const handleRetryCreateSession = async () => {
  console.log('[APP.VUE] セッション作成の再試行を開始');
  retrying.value = true;
  sessionCreationFailed.value = false;
  errorMessage.value = '';
  
  try {
    // api.jsの再試行メソッドを使用
    const result = await apiRetryCreateSession();
    console.log('[APP.VUE] 再試行結果:', result);
    
    if (result.success) {
      sessionToken.value = getSessionToken();
      hasValidSessionComputed.value = true;
      sessionChecking.value = false;
      retrying.value = false;
      ElMessage.success('セッション作成が成功しました！');
      // 成功後にユーザーのログイン状態を確認
      await checkLoginStatus();
    } else {
      sessionCreationFailed.value = true;
      errorMessage.value = result.error || '会话创建失败';
      retrying.value = false;
    }
  } catch (error) {
    console.error('[APP.VUE] セッション作成再試行例外:', error);
    sessionCreationFailed.value = true;
    errorMessage.value = error.message || '不明なエラー';
    retrying.value = false;
  }
};

// 現在のセッション状態を確認
const checkCurrentSessionStatus = async () => {
  try {
    const result = await checkExistingSession();
    if (result.hasSession) {
      ElMessage.info('既存セッションを検出しました。セッションの有効期限が切れるまでお待ちください');
    } else {
      ElMessage.info('現在アクティブなセッションはありません。再作成を試すことができます');
    }
  } catch (error) {
    ElMessage.error('セッション状態の確認に失敗しました');
  }
};

// ページを更新
const refreshPage = () => {
  window.location.reload();
};

// 子コンポーネントにuserInfoを提供
provide('userInfo', userInfo);

// セッショントークンを子コンポーネントに提供
provide('sessionToken', sessionToken);
provide('hasValidSession', hasValidSessionComputed);

// sessionTokenの変化を監視し、api.jsに同期
watch(sessionToken, (newToken, oldToken) => {
  console.log('[APP.VUE] sessionToken更新:', oldToken, '->', newToken);
  setSessionToken(newToken);
  // セッション状態の再計算をトリガー
  console.log('[APP.VUE] 更新後のセッション状態:', hasValidSessionComputed.value);
});



// APIからユーザー情報を取得
const fetchUserInfo = async () => {
  try {
    loading.value = true;

    // ローカルストレージからトークンを取得
    const token = localStorage.getItem('user_token');

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
      localStorage.removeItem('user_token'); // トークンも削除
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
      localStorage.removeItem('user_token'); // トークンも削除
      localStorage.removeItem('uesrname'); // ユーザー名も削除
    } else {
      // console.error('ユーザー情報の取得中にエラーが発生しました:', error);
    }
  } finally {
    loading.value = false;
  }
};

const checkLoginStatus = async () => {
  console.log('[APP.VUE] ログイン状態を確認 - ルート:', route.path, '| セッション有効:', hasValidSessionComputed.value);
  
  try {
    // 有効なセッショントークンがあるかどうかを確認
    if (!hasValidSessionComputed.value) {
      console.log('[APP.VUE] 有効なセッションなし');
      return;
    }
    
    // ユーザー認証状態を確認
    const userToken = localStorage.getItem('user_token');
    console.log('[APP.VUE] ユーザー認証状態:', !!userToken);
    
    if (userToken) {
      await fetchUserInfo();
      // ログイン/登録ページにいるが認証済みの場合、ユーザーページにジャンプ
      if (route.path === '/login' || route.path === '/signup') {
        console.log('[APP.VUE] 認証済みユーザーがログインページにアクセス、ユーザーページにジャンプ');
        router.push('/user');
      }
    } else {
      console.log('[APP.VUE] セッション有効だが未認証');
    }
  } catch (error) {
    console.error('[APP.VUE] ログイン状態確認例外:', error);
  }
};

// 子コンポーネントにcheckLoginStatus関数を提供
provide('checkLoginStatus', checkLoginStatus);

const logout = async () => {
  try {
    // ローカルストレージからトークンとユーザー情報をクリア
    localStorage.removeItem('user_token');
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
  console.log('[APP.VUE] アプリケーションマウント開始');
  console.log('[APP.VUE] 現在のルート:', route.path);
  console.log('[APP.VUE] ストレージ状態 - session:', !!localStorage.getItem('session_token'), 'user:', !!localStorage.getItem('user_token'));
  
  // ルーターインスタンスを設定
  setRouter(router);
  
  // セッションチェックを実行
  await performSessionCheck();
  
  // セッション再初期化イベントを監視
  window.addEventListener('reinitializeSession', handleReinitializeSession);
});

// セッションチェックのコアロジックを実行
const performSessionCheck = async () => {
  console.log('[APP.VUE] セッションチェックを開始');
  sessionChecking.value = true;
  sessionCreationFailed.value = false;
  errorMessage.value = '';
  
  try {
    const result = await initializeSession();
    console.log('[APP.VUE] セッションチェック結果:', result);
    
    if (result.success) {
      sessionToken.value = getSessionToken();
      hasValidSessionComputed.value = true;
      sessionChecking.value = false;
      console.log('[APP.VUE] セッションチェック完了、ログイン状態の確認を準備');
      await checkLoginStatus();
    } else {
      // セッション作成失敗
      sessionCreationFailed.value = true;
      hasValidSessionComputed.value = false;
      sessionChecking.value = false;
      errorMessage.value = result.error || '会话创建失败';
      console.log('[APP.VUE] セッション作成失敗、エラー画面を表示');
    }
  } catch (error) {
    console.error('[APP.VUE] セッションチェック例外:', error);
    sessionCreationFailed.value = true;
    hasValidSessionComputed.value = false;
    sessionChecking.value = false;
    errorMessage.value = error.message || 'セッションチェック中に不明なエラーが発生しました';
  }
};

// セッション再初期化イベントを処理
const handleReinitializeSession = async () => {
  console.log('[APP.VUE] セッション再初期化イベントを受信');
  await performSessionCheck();
};

// コンポーネントアンマウント時にクリーンアップ
onUnmounted(() => {
  window.removeEventListener('reinitializeSession', handleReinitializeSession);
});

onUnmounted(() => {
  // イベントリスナーをクリーンアップ
  window.removeEventListener('reinitializeSession', reinitializeSession);
});

// セッション有効性の変化を監視
watch(isSessionValid, (newVal, oldVal) => {
  console.log('[APP.VUE] セッション有効性変化:', oldVal, '->', newVal);
  if (newVal && !oldVal) {
    console.log('[APP.VUE] セッションが有効になり、ログイン状態を確認');
    checkLoginStatus();
  }
});

// ルート変化を監視、セッション有効時にログイン状態を確認
watch(() => route.path, (newPath) => {
  if (isSessionValid.value) {
    console.log('[APP.VUE] ルート変化、ログイン状態を確認:', newPath);
    checkLoginStatus();
  }
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

.session-check-screen {
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

.checking-content {
  text-align: center;
  max-width: 400px;
  padding: 20px;
}

.checking-text {
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

.empty-state-screen {
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

.empty-content {
  text-align: center;
  max-width: 400px;
  padding: 20px;
}
</style>