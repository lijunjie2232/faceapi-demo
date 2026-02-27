<template>
  <div class="user-dashboard">
    <h2>ユーザーダッシュボード</h2>
    <p>
      個人用ユーザーダッシュボードへようこそ。ここではプロフィールを管理し、認識履歴を表示できます。
    </p>

    <!-- デモ通知 -->
    <DemoNotice />

    <div class="user-info">
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>あなたのプロフィール</span>
            <el-button
              v-if="!editing"
              type="primary"
              size="small"
              @click="startEditing"
            >
              プロフィールを編集
            </el-button>
            <div v-else>
              <el-button
                type="success"
                size="small"
                @click="saveProfile"
                :disabled="updating"
              >
                {{ updating ? "更新中..." : "変更を保存" }}
              </el-button>
              <el-button
                size="small"
                @click="cancelEditing"
                :disabled="updating"
              >
                キャンセル
              </el-button>
            </div>
          </div>
        </template>

        <div v-if="loading">
          <el-skeleton :rows="4" animated />
        </div>
        <div v-else-if="userInfo && !authError">
          <el-form
            v-if="!editing"
            :model="userInfo"
            label-position="left"
            class="profile-display"
          >
            <el-form-item label="ユーザー名:">
              <span>{{ userInfo.username }}</span>
            </el-form-item>
            <el-form-item label="メール:">
              <span>{{ userInfo.email }}</span>
            </el-form-item>
            <el-form-item label="氏名:">
              <span>{{ userInfo.full_name }}</span>
            </el-form-item>
            <el-form-item label="ID:">
              <span>{{ userInfo.id }}</span>
            </el-form-item>
            <el-form-item label="ステータス:">
              <el-tag :type="userInfo.is_active ? 'success' : 'danger'">
                {{ userInfo.is_active ? "アクティブ" : "非アクティブ" }}
              </el-tag>
            </el-form-item>
            <el-form-item label="役割:">
              <el-tag :type="userInfo.is_admin ? 'warning' : 'info'">
                {{ userInfo.is_admin ? "管理者" : "一般ユーザー" }}
              </el-tag>
            </el-form-item>
            <el-form-item label="会員登録日:">
              <span id="memberSince">{{
                formatDate(userInfo.created_at)
              }}</span>
            </el-form-item>
            <el-form-item label="最終更新:">
              <span id="lastUpdated">{{
                formatDate(userInfo.updated_at)
              }}</span>
            </el-form-item>

            <!-- ヘッドピックフィールド -->
            <el-form-item label="顔画像:">
              <div class="head-pic-container">
                <div v-if="userInfo.head_pic" class="head-pic-preview">
                  <img
                    :src="'data:image/jpeg;base64,' + userInfo.head_pic"
                    alt="顔画像プレビュー"
                    class="head-pic-image"
                  />
                </div>
                <div v-else class="head-pic-placeholder">
                  画像がアップロードされていません
                </div>

                <el-button
                  :type="
                    isHoveringFaceButton
                      ? 'primary'
                      : userInfo.head_pic
                      ? 'success'
                      : 'warning'
                  "
                  @click="updateFace"
                  @mouseenter="isHoveringFaceButton = true"
                  @mouseleave="isHoveringFaceButton = false"
                  class="face-image-btn"
                >
                  <span class="button-text">
                    {{
                      isHoveringFaceButton
                        ? userInfo.head_pic
                          ? "顔を更新"
                          : "顔を設定する"
                        : userInfo.head_pic
                        ? "顔が設定済み"
                        : "顔が未設定"
                    }}
                  </span>
                </el-button>
              </div>
            </el-form-item>
          </el-form>

          <el-form
            v-else
            :model="editableInfo"
            :rules="formRules"
            ref="profileFormRef"
            label-position="left"
            class="profile-edit"
          >
            <el-form-item label="ユーザー名:" prop="username">
              <el-input
                v-model="editableInfo.username"
                placeholder="ユーザー名"
              />
            </el-form-item>
            <el-form-item label="メール:" prop="email">
              <el-input v-model="editableInfo.email" placeholder="メール" />
            </el-form-item>
            <el-form-item label="氏名:" prop="full_name">
              <el-input v-model="editableInfo.full_name" placeholder="氏名" />
            </el-form-item>
            <el-form-item label="新しいパスワード:" prop="new_password">
              <el-input
                v-model="editableInfo.new_password"
                type="password"
                placeholder="空白のままにして現在のパスワードを保持"
              />
            </el-form-item>
            <el-form-item label="ID:">
              <span>{{ userInfo.id }}</span>
            </el-form-item>
            <el-form-item label="ステータス:">
              <el-tag :type="userInfo.is_active ? 'success' : 'danger'">
                {{ userInfo.is_active ? "アクティブ" : "非アクティブ" }}
              </el-tag>
            </el-form-item>
            <el-form-item label="役割:">
              <el-tag :type="userInfo.is_admin ? 'warning' : 'info'">
                {{ userInfo.is_admin ? "管理者" : "一般ユーザー" }}
              </el-tag>
            </el-form-item>
            <el-form-item label="会員登録日:">
              <span id="memberSince">{{
                formatDate(userInfo.created_at)
              }}</span>
            </el-form-item>
            <el-form-item label="最終更新:">
              <span id="lastUpdated">{{
                formatDate(userInfo.updated_at)
              }}</span>
            </el-form-item>

            <!-- 編集モードでのヘッドピックフィールド -->
            <el-form-item label="顔画像:">
              <div class="head-pic-container">
                <div v-if="userInfo.head_pic" class="head-pic-preview">
                  <img
                    :src="'data:image/jpeg;base64,' + userInfo.head_pic"
                    alt="顔画像プレビュー"
                    class="head-pic-image"
                  />
                </div>
                <div v-else class="head-pic-placeholder">
                  画像がアップロードされていません
                </div>

                <el-button
                  :type="
                    isHoveringFaceButton
                      ? 'primary'
                      : userInfo.head_pic
                      ? 'success'
                      : 'warning'
                  "
                  @click="updateFace"
                  @mouseenter="isHoveringFaceButton = true"
                  @mouseleave="isHoveringFaceButton = false"
                  class="face-image-btn"
                >
                  <span class="button-text">
                    {{
                      isHoveringFaceButton
                        ? userInfo.head_pic
                          ? "顔を更新"
                          : "顔を設定する"
                        : userInfo.head_pic
                        ? "顔が設定済み"
                        : "顔が未設定"
                    }}
                  </span>
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
        <div v-else-if="authError">
          <p class="auth-error">
            認証に失敗しました。ログインページにリダイレクトしています...
          </p>
        </div>
        <div v-else>
          <p>
            ユーザー情報の読み込みに失敗しました。ページを更新してください。
          </p>
        </div>
      </el-card>

      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>認識履歴</span>
          </div>
        </template>
        <p>最近の顔認識ログと活動がここに表示されます。</p>
        <el-table
          :data="recognitionHistory"
          style="width: 100%; margin-top: 15px"
        >
          <el-table-column
            prop="date"
            label="日付"
            width="180"
          ></el-table-column>
          <el-table-column prop="status" label="ステータス" width="120">
            <template #default="scope">
              <el-tag
                :type="scope.row.status === 'Success' ? 'success' : 'danger'"
              >
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="confidence"
            label="信頼度"
            width="120"
          ></el-table-column>
          <el-table-column prop="details" label="詳細"></el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 顔検出ポップアウトウィンドウ -->
    <FaceDetectionPopOut
      v-model="showFaceDetectionPopOut"
      :_handler="handleFaceCaptured"
    />
  </div>
</template>

<script setup>
import { ref, inject, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import apiClient from "../utils/api";
import FaceDetectionPopOut from "../components/FaceDetectionPopOut.vue";
import DemoNotice from "@/components/DemoNotice.vue";

// 親コンポーネント(App)からuserInfoを注入
const injectedUserInfo = inject("userInfo");
const userInfo = ref(null);

// 独立してユーザー情報を取得する関数
const fetchUserInfo = async () => {
  try {
    loading.value = true;
    const token = localStorage.getItem('user_token');
    
    if (!token) {
      authError.value = true;
      return;
    }
    
    const response = await apiClient.get('/api/v1/user/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.data.code === 200) {
      userInfo.value = response.data.data;
      // localStorageにも保存
      localStorage.setItem('userInfo', JSON.stringify(response.data.data));
      authError.value = false;
    } else {
      authError.value = true;
    }
  } catch (error) {
    console.error('[USER] ユーザー情報取得エラー:', error);
    authError.value = true;
  } finally {
    loading.value = false;
  }
};
const editableInfo = ref({
  username: "",
  email: "",
  full_name: "",
  new_password: "", // パスワード用の新しいフィールド
});
const loading = ref(true);
const editing = ref(false);
const updating = ref(false);
const authError = ref(false);
const isHoveringFaceButton = ref(false);
const showFaceDetectionPopOut = ref(false);
const recognitionHistory = ref([
  {
    date: "2023-11-30 14:30:22",
    status: "Success",
    confidence: "98.5%",
    details: "オフィス入口",
  },
  {
    date: "2023-11-30 09:15:47",
    status: "Success",
    confidence: "96.2%",
    details: "メインゲート",
  },
  {
    date: "2023-11-29 18:45:12",
    status: "Failed",
    confidence: "78.1%",
    details: "裏口",
  },
  {
    date: "2023-11-29 08:22:33",
    status: "Success",
    confidence: "95.7%",
    details: "メインゲート",
  },
]);
const profileFormRef = ref(null);
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const router = useRouter();

// 親コンポーネント(App)からcheckLoginStatusを注入
const injectedCheckLoginStatus = inject("checkLoginStatus");

// フォーム検証ルール
const formRules = {
  username: [
    {
      required: true,
      message: "ユーザー名を入力してください",
      trigger: "blur",
    },
    {
      min: 3,
      max: 20,
      message: "長さは3〜20文字である必要があります",
      trigger: "blur",
    },
  ],
  email: [
    {
      required: true,
      message: "メールアドレスを入力してください",
      trigger: "blur",
    },
    {
      type: "email",
      message: "有効なメールアドレスを入力してください",
      trigger: "blur",
    },
  ],
  full_name: [
    { required: true, message: "氏名を入力してください", trigger: "blur" },
    {
      min: 2,
      max: 50,
      message: "長さは2〜50文字である必要があります",
      trigger: "blur",
    },
  ],
  new_password: [
    {
      min: 6,
      message: "パスワードは少なくとも8文字である必要があります",
      trigger: "blur",
    },
  ],
};

// 日付をフォーマットする関数
const formatDate = (dateString) => {
  const options = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

// 顔検出ポップアウトを処理する関数
const updateFace = () => {
  showFaceDetectionPopOut.value = true;
};

// プロフィール編集を開始
const startEditing = () => {
  // 現在のユーザー情報を編集可能なフィールドにコピー
  editableInfo.value = {
    username: userInfo.value.username,
    email: userInfo.value.email,
    full_name: userInfo.value.full_name,
    new_password: "", // 空として初期化
  };
  editing.value = true;
};

// localStorageからトークンを取得する関数
const getToken = () => {
  return localStorage.getItem("token") || "";
};

// プロフィール変更を保存
const saveProfile = async () => {
  // 送信前にフォームを検証
  if (!profileFormRef.value) return;

  const valid = await profileFormRef.value.validate().catch(() => false);
  if (!valid) {
    ElMessage.error("フォームのエラーを修正してください");
    return;
  }

  updating.value = true;

  try {
    const token = getToken();

    // 最初はパスワードなしでリクエストデータを準備
    const requestData = {
      username: editableInfo.value.username,
      email: editableInfo.value.email,
      full_name: editableInfo.value.full_name,
    };

    // パスワードが提供されている場合のみパスワードフィールドを追加
    if (
      editableInfo.value.new_password &&
      editableInfo.value.new_password.trim() !== ""
    ) {
      requestData.password = editableInfo.value.new_password;
    }

    const response = await apiClient.put("/api/v1/user/me", requestData, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (response.data.code === 200 || response.data.success) {
      // アプリケーションの状態でユーザー情報を更新
      userInfo.value = response.data.data;

      // App.vueで注入されたユーザー情報を更新
      if (injectedUserInfo && injectedUserInfo.value) {
        injectedUserInfo.value = response.data.data;
      }

      editing.value = false;
      ElMessage.success(
        response.data.message || "プロフィールが正常に更新されました"
      );

      // App.vueからcheckLoginStatus関数を呼び出してヘッダーのユーザー情報を更新
      if (injectedCheckLoginStatus) {
        injectedCheckLoginStatus();
      }
    } else {
      ElMessage.error(
        response.data.message || "プロフィールの更新に失敗しました"
      );
    }
  } catch (error) {
    // console.error('プロフィール更新エラー:', error);
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail);
    } else {
      ElMessage.error(
        error.message || "プロフィールの更新中にエラーが発生しました"
      );
    }
  } finally {
    updating.value = false;
  }
};

// 編集をキャンセルして変更を元に戻す
const cancelEditing = () => {
  ElMessageBox.confirm(
    "保存されていない変更を破棄してもよろしいですか？",
    "警告",
    {
      confirmButtonText: "はい",
      cancelButtonText: "いいえ",
      type: "warning",
    }
  )
    .then(() => {
      editing.value = false;
      // 編集可能なフィールドを元の値にリセット
      editableInfo.value = {
        username: userInfo.value.username,
        email: userInfo.value.email,
        full_name: userInfo.value.full_name,
        new_password: "",
      };
    })
    .catch(() => {
      // ユーザーがキャンセル、編集を続ける
    });
};

// コンポーネントマウント時にユーザー情報を取得
onMounted(() => {
  console.log('[USER] コンポーネントマウント');
  // 注入されたuserInfoをチェック
  if (injectedUserInfo && injectedUserInfo.value && Object.keys(injectedUserInfo.value).length > 0) {
    console.log('[USER] 注入されたuserInfoを使用');
    userInfo.value = injectedUserInfo.value;
    loading.value = false;
  } else {
    console.log('[USER] 独自にユーザー情報を取得');
    fetchUserInfo();
  }
});

// 注入されたuserInfoの変更を監視
watch(
  injectedUserInfo,
  (newVal) => {
    if (newVal && Object.keys(newVal).length > 0) {
      console.log('[USER] 注入userInfo更新:', newVal);
      userInfo.value = newVal;
      loading.value = false;
      authError.value = false;
    }
  }
);

// 認証エラーが発生した場合にログインにリダイレクト
watch(authError, (newVal) => {
  if (newVal) {
    setTimeout(() => {
      router.push("/login");
    }, 2000);
  }
});

// ポップアウトウィンドウからキャプチャされた顔を処理する関数
const handleFaceCaptured = async (imageData) => {
  try {
    // 画像をフォームデータとして送信するためにFormDataを作成
    const formData = new FormData();

    // トークンを取得
    const token = getToken();

    // base64画像データをblobに変換してフォームデータに追加
    const byteCharacters = atob(imageData.split(",")[1]); // data:image/jpeg;base64,プレフィックスを削除
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += 512) {
      const slice = byteCharacters.slice(offset, offset + 512);
      const byteNumbers = new Array(slice.length);

      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }

      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }

    const blob = new Blob(byteArrays, { type: "image/jpeg" });
    formData.append("image", blob, "face_image.jpg");

    // キャプチャされた画像をアップロードしてユーザーのヘッドピックを更新
    const response = await apiClient.put("/api/v1/face/me", formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data",
      },
    });

    // 'code'フィールドを持つ期待される構造のレスポンスを確認
    if (response.data.code === 200 || response.data.success) {
      ElMessage.success(
        response.data.message || "顔画像が正常に更新されました"
      );
      
      // 新しいヘッドピックを反映するためにユーザー情報を更新
      if (injectedUserInfo && injectedUserInfo.value) {
        injectedUserInfo.value.head_pic = imageData.split(",")[1]; // base64部分のみを保存
      }
    } else {
      ElMessage.error(response.data.message || "顔画像の更新に失敗しました");
    }
  } catch (error) {
    // console.error('顔画像更新エラー:', error);
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail);
    } else {
      ElMessage.error(error.message || "顔画像の更新中にエラーが発生しました");
    }
  }
};
</script>

<style scoped>
.user-dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  color: #303133;
  margin-bottom: 20px;
}

.user-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.info-card {
  text-align: left;
}

.card-header {
  font-weight: bold;
  color: #303133;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.auth-error {
  color: #f56c6c;
  font-weight: bold;
  text-align: center;
  padding: 20px;
}

.el-table {
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 20px;
}

.profile-display .el-form-item {
  margin-bottom: 12px;
}

.profile-display .el-form-item__label {
  font-weight: bold;
  color: #606266;
  width: 120px;
}

.profile-display .el-form-item__content {
  display: block;
  font-size: 14px;
}

.profile-edit .el-form-item {
  margin-bottom: 18px;
}

.profile-edit .el-form-item__label {
  font-weight: bold;
  color: #606266;
  width: 120px;
}

.face-image-btn {
  position: relative;
  overflow: hidden;
}

/* ホバーしていないときのデフォルトテキスト */
.face-image-btn .button-text:not(:hover)::before {
  content: attr(data-normal-text);
}

/* ホバー時のテキスト */
.face-image-btn:hover .button-text::before {
  content: attr(data-hover-text);
}

.head-pic-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.head-pic-preview {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.head-pic-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
  display: block;
}

.head-pic-placeholder {
  padding: 40px 20px;
  text-align: center;
  color: #909399;
  font-size: 14px;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
