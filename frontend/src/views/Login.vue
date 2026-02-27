<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>ログイン</h2>
      
      <!-- デモ通知 -->
      <DemoNotice :is-login-page="true" :floating="false" />
      
      <!-- 管理者情報アラート -->
      <el-alert
        title="管理者アカウント情報"
        type="info"
        description="初期管理者ユーザー: admin / パスワード: admin123。管理者の顔画像はまだ設定されていません。まずパスワードでログインし、その後顔画像を設定してください。"
        show-icon
        :closable="false"
        class="admin-info-alert"
      />
      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-width="100px" class="login-form">
        <el-form-item label="ユーザー名" prop="username">
          <el-input v-model="loginForm.username" placeholder="ユーザー名を入力してください"></el-input>
        </el-form-item>
        <el-form-item label="パスワード" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="パスワードを入力してください"></el-input>
        </el-form-item>
        <el-form-item>
          <div class="button-group">
            <el-button type="primary" @click="handleLogin" :loading="loginLoading">ログイン</el-button>
            <!-- <el-button @click="resetForm">リセット</el-button> -->
            <el-button @click="openFaceRecognizer">顔でログイン</el-button>
          </div>
        </el-form-item>
      </el-form>
      <p>アカウントをお持ちでないですか？ <router-link to="/signup">サインアップ</router-link></p>
    </el-card>

    <!-- 顔認識ポップアウトコンポーネント -->
    <FaceRecongnizerPopOut v-model="faceRecognizerVisible" @face-verified="handleFaceVerification" />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import apiClient from '../utils/api'
import FaceRecongnizerPopOut from '@/components/FaceRecongnizerPopOut.vue'
import DemoNotice from '@/components/DemoNotice.vue'

const route = useRoute()
const router = useRouter()

const loginForm = reactive({
  username: '',
  password: ''
})

// 顔認識ポップアップの状態
const faceRecognizerVisible = ref(false)

const loginRules = {
  username: [
    { required: true, message: 'ユーザー名を入力してください', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'パスワードを入力してください', trigger: 'blur' },
    { min: 4, message: 'パスワードは少なくとも6文字である必要があります', trigger: 'blur' }
  ]
}

const loginFormRef = ref()
const loginLoading = ref(false)

const handleLogin = async () => {
  const valid = await loginFormRef.value.validate().catch(() => { })
  if (!valid) return

  loginLoading.value = true
  try {
    const formData = new FormData()
    formData.append('username', loginForm.username)
    formData.append('password', loginForm.password)

    const response = await apiClient.post('/api/v1/user/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // 実際のフォーマットに応じてレスポンスを処理
    if (response.data.code === 200) {
      const { token, token_type } = response.data.data

      // アクセストークンを正しいキーでlocalStorageに保存
      localStorage.setItem('user_token', `${token}`)
      localStorage.setItem('token_type', `${token_type}`)

      ElMessage.success('ログイン成功！')

      // ルートパラメータからリダイレクトパスを取得（ある場合）
      const redirectPath = route.query.redirect || '/user'

      console.log(`Redirecting to: ${redirectPath}`)
      // 意図したページまたはホームページにリダイレクト
      router.push(redirectPath)
    } else {
      ElMessage.error(response.data.detail || 'ログインに失敗しました')
    }
  } catch (error) {
    // console.error('ログインエラー:', error)
    ElMessage.error(error.response?.data?.detail || 'ログインに失敗しました')
  } finally {
    loginLoading.value = false
  }
}

// const resetForm = () => {
//   loginFormRef.value.resetFields()
// }

// 顔認識ポップアップを開く
const openFaceRecognizer = () => {
  faceRecognizerVisible.value = true
}

// 顔検証成功の処理
const handleFaceVerification = (verificationData) => {
  if (verificationData && verificationData.token) {
    // アクセストークンを正しいキーでlocalStorageに保存
    localStorage.setItem('user_token', `${verificationData.token}`)
    localStorage.setItem('token_type', `${verificationData.token_type || 'Bearer'}`)

    ElMessage.success('顔ログイン成功！')

    // ポップアップを閉じる
    faceRecognizerVisible.value = false

    // 意図したページまたはホームページにリダイレクト
    const redirectPath = route.query.redirect || '/user'
    router.push(redirectPath)
  } else {
    ElMessage.error('顔検証に失敗しました。もう一度お試しください。')
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 500px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.button-group {
  display: flex;
  gap: 10px;
  justify-content: center;
  width: 100%;
}

.login-form {
  margin-bottom: 20px;
}

.admin-info-alert {
  margin: 20px 0;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
</style>