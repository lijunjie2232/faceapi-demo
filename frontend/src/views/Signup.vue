<template>
  <div class="signup-container">
    <el-card class="signup-card">
      <h2>サインアップ</h2>
      
      <!-- Demo Notice -->
      <DemoNotice :is-login-page="true" :show-session-info="true" :floating="false" />
      <el-form :model="signupForm" :rules="signupRules" ref="signupFormRef" label-width="150px" class="signup-form">
        <el-form-item label="ユーザー名" prop="username">
          <el-input v-model="signupForm.username" placeholder="ユーザー名を入力してください"></el-input>
        </el-form-item>
        <el-form-item label="メール" prop="email">
          <el-input v-model="signupForm.email" type="email" placeholder="メールアドレスを入力してください"></el-input>
        </el-form-item>
        <el-form-item label="氏名" prop="full_name">
          <el-input v-model="signupForm.full_name" placeholder="氏名を入力してください"></el-input>
        </el-form-item>
        <el-form-item label="パスワード" prop="password">
          <el-input v-model="signupForm.password" type="password" placeholder="パスワードを入力してください"></el-input>
        </el-form-item>
        <el-form-item label="パスワードを確認" prop="confirmPassword">
          <el-input v-model="signupForm.confirmPassword" type="password" placeholder="パスワードを確認してください"></el-input>
        </el-form-item>
        <el-form-item>
          <div class="button-group">
            <el-button type="primary" @click="handleSignup" :loading="signupLoading">サインアップ</el-button>
          </div>
        </el-form-item>
      </el-form>
      <p>すでにアカウントをお持ちですか？ <router-link to="/login">ログイン</router-link></p>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import apiClient from '../utils/api'
import DemoNotice from '@/components/DemoNotice.vue'

const router = useRouter()

const signupForm = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  confirmPassword: ''
})

const signupRules = {
  username: [
    { required: true, message: 'ユーザー名を入力してください', trigger: 'blur' },
    { min: 3, message: 'ユーザー名は少なくとも3文字である必要があります', trigger: 'blur' }
  ],
  email: [
    { required: true, message: 'メールアドレスを入力してください', trigger: 'blur' },
    { type: 'email', message: '有効なメールアドレスを入力してください', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '氏名を入力してください', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'パスワードを入力してください', trigger: 'blur' },
    { min: 6, message: 'パスワードは少なくとも6文字である必要があります', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: 'パスワードを確認してください', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== signupForm.password) {
          callback(new Error('パスワードが一致しません'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const signupFormRef = ref()
const signupLoading = ref(false)

const handleSignup = async () => {
  const valid = await signupFormRef.value.validate().catch(() => { })
  if (!valid) return

  signupLoading.value = true
  try {
    const userData = {
      username: signupForm.username,
      email: signupForm.email,
      full_name: signupForm.full_name,
      password: signupForm.password
    }

    const response = await apiClient.post('/api/v1/user/signup', userData, {
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.data.code === 200) {
      ElMessage.success('登録成功！ログインしてください。')
      // 登録成功後にログインページにリダイレクト
      router.push('/login')
    }
    else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    // console.error('サインアップエラー:', error)
    ElMessage.error(error.response?.data?.message || '登録に失敗しました')
  } finally {
    signupLoading.value = false
  }
}


</script>

<style scoped>
.signup-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.signup-card {
  width: 520px;
  padding: 20px;
}

.signup-form {
  margin-top: 20px;
}

/* 長いラベルにスペースを提供するためにフォームアイテムのスタイルを調整 */
.el-form-item {
  margin-bottom: 20px;
}

.el-form-item__label {
  text-align: left;
  width: 130px;
  /* ラベルの幅を調整 */
  padding-right: 10px;
  /* ラベルと入力ボックスの間にスペースを追加 */
}

.el-form-item__content {
  flex: 1;
  /* 入力ボックスが十分に伸びるようにする */
  min-width: 0;
  /* コンテンツのオーバーフローを防ぐ */
}

.button-group {
  display: flex;
  gap: 12px;
  width: 100%;
  justify-content: center;
  margin-top: 10px;
}

.button-group .el-button {
  flex: 0 1 auto;
  /* ボタンはすべてのスペースを埋める必要がない */
  min-width: 120px;
  /* 最小幅を設定 */
}
</style>