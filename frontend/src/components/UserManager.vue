<template>
  <div class="user-manager component-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="table-container">
          <div class="header-actions">
            <h3 class="section-header">ユーザー管理</h3>
            <div class="header-buttons">
              <el-button type="primary" @click="openDrawer" :icon="Plus">
                ユーザーを追加
              </el-button>
              <el-button type="success" @click="refreshUsers" :icon="Refresh" :loading="loading" plain>
                更新
              </el-button>
              <el-dropdown v-if="selectedUsers.length > 0" @command="handleBatchAction">
                <el-button type="warning" :icon="Operation">
                  一括操作 <el-icon class="el-icon--right"><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="activate">選択したユーザーを有効化</el-dropdown-item>
                    <el-dropdown-item command="deactivate">選択したユーザーを無効化</el-dropdown-item>
                    <el-dropdown-item command="reset-password" divided>パスワードをリセット</el-dropdown-item>
                    <el-dropdown-item command="delete-face">顔データを削除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <span v-if="selectedUsers.length > 0" class="selection-info">
                {{ selectedUsers.length }} 名のユーザーが選択されました
              </span>
            </div>
          </div>

          <!-- 検索フィルターセクション -->
          <div class="filter-section">
            <el-space wrap :size="10" class="filter-tags">
              <el-tag v-for="tag in filterTags" :key="tag.name" closable :type="getFilterTagType(tag.name)"
                @close="removeFilterTag(tag.name)" round>
                {{ tag.label }}: {{ tag.value }}
              </el-tag>

              <el-button type="info" size="middle" icon="Plus" @click="showFilterDialog = true" round plain>
                列でフィルター
              </el-button>
            </el-space>
          </div>

          <el-card>
            <el-table :data="users" style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
              <el-table-column type="selection" width="55"></el-table-column>
              <el-table-column prop="id" label="ID" width="80"></el-table-column>
              <el-table-column prop="username" label="ユーザー名" width="120"></el-table-column>
              <el-table-column prop="email" label="メール" min-width="200"></el-table-column>
              <el-table-column prop="full_name" label="氏名" width="200"></el-table-column>
              <el-table-column prop="head_pic" label="顔データ" min-width="100">
                <template #default="scope">
                  <el-button :type="scope.row.head_pic === '1' ? 'success' : 'danger'" size="small"
                    @click="openFaceDetection(scope.row)" @mouseenter="handleMouseEnter(scope.row.id)"
                    @mouseleave="handleMouseLeave" plain>
                    <span>{{
                      hoveredUserId === scope.row.id
                        ? (scope.row.head_pic === '1' ? '顔を更新する' : '追加する')
                        : (scope.row.head_pic === '1' ? '顔が追加済み' : '顔が無し')
                    }}</span>
                  </el-button>
                </template>
              </el-table-column>
              <el-table-column prop="is_admin" label="役割" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.is_admin ? 'danger' : 'info'" size="middle" round>
                    {{ scope.row.is_admin ? '管理者' : 'ユーザー' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_active" label="ステータス" width="100">
                <template #default="scope">
                  <el-switch v-model="scope.row.is_active" :active-value="true" :inactive-value="false"
                    @change="handleStatusChange(scope.row)" :loading="statusLoading[scope.row.id]">
                    <template #active-action>
                      <el-icon>
                        <CircleCheckFilled />
                      </el-icon>
                    </template>
                    <template #inactive-action>
                      <el-icon>
                        <RemoveFilled />
                      </el-icon>
                    </template>
                  </el-switch>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="作成日" width="160">
                <template #default="scope">
                  {{ formatDate(scope.row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column prop="updated_at" label="最終更新" width="160">
                <template #default="scope">
                  {{ formatDate(scope.row.updated_at) }}
                </template>
              </el-table-column>
              <el-table-column label="アクション" min-width="140" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="editUser(scope.row)" type="primary">
                    <el-icon>
                      <Edit />
                    </el-icon>
                    編集
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteUser(scope.row.id)" plain>
                    <el-icon>
                      <Delete />
                    </el-icon>
                    削除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="table-footer">
              <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                :current-page="pagination.page" :page-sizes="[5, 10, 20, 50]" :page-size="pagination.size"
                layout="total, sizes, prev, pager, next, jumper" :total="pagination.total"
                style="margin-top: 20px; text-align: right;"></el-pagination>
              <div class="footer-actions">
                <el-button type="success" @click="refreshUsers" :icon="Refresh" :loading="loading" size="large" plain>
                  リストを更新
                </el-button>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>

    <!-- フィルターダイアログ -->
    <el-dialog v-model="showFilterDialog" title="フィルターを追加" width="500px" :before-close="closeFilterDialog">
      <el-form :model="filterForm" label-width="120px">
        <el-form-item label="フィルタータイプ">
          <el-select v-model="filterForm.key" placeholder="フィルタータイプを選択" @change="onFilterKeyChange"
            style="width: 100%;">
            <el-option v-for="option in filterOptions" :key="option.value" :label="option.label" :value="option.value">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item v-if="['username', 'email', 'full_name'].includes(filterForm.key)"
          :label="filterOptions.find(o => o.value === filterForm.key)?.label || '値'">
          <el-input v-model="filterForm.value" placeholder="値を入力" @keyup.enter="addFilterTag">
          </el-input>
        </el-form-item>

        <el-form-item v-else-if="['is_active', 'is_admin', 'set_face'].includes(filterForm.key)"
          :label="filterOptions.find(o => o.value === filterForm.key)?.label || '値'">
          <el-select v-model="filterForm.value" placeholder="値を選択" style="width: 100%;">
            <el-option label="はい" :value="true"></el-option>
            <el-option label="いいえ" :value="false"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item v-else label="値">
          <el-input v-model="filterForm.value" placeholder="値を入力" @keyup.enter="addFilterTag">
          </el-input>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeFilterDialog">キャンセル</el-button>
          <el-button type="primary" @click="addFilterTag"
            :disabled="!filterForm.key || (filterForm.value !== false && !filterForm.value)">
            フィルターを追加
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 右側ドロワーのフォーム -->
    <el-drawer v-model="drawerVisible" :title="formTitle" direction="rtl" size="500px"
      :before-close="handleDrawerClose">
      <div class="drawer-content">
        <el-form :model="userForm" :rules="formRules" ref="userFormRef" label-width="120px">
          <el-form-item label="ユーザー名" prop="username">
            <el-input v-model="userForm.username" placeholder="ユーザー名を入力"></el-input>
          </el-form-item>

          <el-form-item label="メール" prop="email">
            <el-input v-model="userForm.email" placeholder="メールアドレスを入力"></el-input>
          </el-form-item>

          <el-form-item label="氏名" prop="full_name">
            <el-input v-model="userForm.full_name" placeholder="氏名を入力"></el-input>
          </el-form-item>

          <el-form-item label="役割" v-if="userForm.id">
            <el-switch v-model="userForm.is_admin" active-text="管理者" inactive-text="ユーザー" />
          </el-form-item>

          <el-form-item label="ステータス">
            <el-switch v-model="userForm.is_active">
              <template #active-action>
                <el-icon>
                  <CircleCheckFilled />
                </el-icon>
              </template>
              <template #inactive-action>
                <el-icon>
                  <RemoveFilled />
                </el-icon>
              </template>
            </el-switch>
          </el-form-item>

          <el-form-item label="パスワード" :prop="!userForm.id ? 'password' : ''" :required="!userForm.id">
            <el-input v-model="userForm.password" type="password"
              :placeholder="userForm.id ? '空白のままにして現在のパスワードを保持' : 'パスワードを入力'"></el-input>
          </el-form-item>

          <div class="form-actions">
            <el-button type="primary" @click="submitForm" :loading="submitting" style="flex: 1;">
              <span>{{ userForm.id ? 'ユーザーを更新' : 'ユーザーを作成' }}</span>
            </el-button>

            <el-button @click="resetForm" v-if="userForm.id" style="flex: 1; margin-left: 10px;">
              キャンセル
            </el-button>
          </div>
        </el-form>
      </div>
    </el-drawer>

    <!-- パスワードリセットダイアログ -->
    <el-dialog v-model="passwordResetDialogVisible" title="パスワードをリセット" width="400px"
      :before-close="handlePasswordResetCancel">
      <el-form :model="{ newPassword, confirmPassword }" :rules="passwordResetRules" ref="passwordResetFormRef"
        label-width="120px">
        <el-form-item label="新しいパスワード" prop="newPassword">
          <el-input v-model="newPassword" type="password" placeholder="新しいパスワードを入力" show-password
            @input="validatePasswordMatch"></el-input>
        </el-form-item>
        <el-form-item label="パスワードを確認" prop="confirmPassword" :validate-status="passwordMatchStatus"
          :help="passwordMatchMessage">
          <el-input v-model="confirmPassword" type="password" placeholder="新しいパスワードを確認" show-password
            @input="validatePasswordMatch">
            <template #suffix>
              <el-icon v-if="passwordMatchStatus === 'success'" class="password-match-icon success">
                <Check />
              </el-icon>
              <el-icon v-else-if="passwordMatchStatus === 'error'" class="password-match-icon error">
                <Close />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handlePasswordResetCancel">キャンセル</el-button>
          <el-button type="primary" @click="confirmPasswordReset" :loading="submitting" :disabled="!isPasswordValid">
            パスワードをリセット
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 顔検出ポップアウトウィンドウ -->
    <FaceDetectionPopOut v-model="showFaceDetectionPopOut" :_handler="updateUserFace" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import apiClient from '../utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, CircleCheckFilled, RemoveFilled, Operation, ArrowDown, Check, Close } from '@element-plus/icons-vue'
import FaceDetectionPopOut from './FaceDetectionPopOut.vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const users = ref([])
const loading = ref(false)
const submitting = ref(false)
const userFormRef = ref()
const drawerVisible = ref(false)
const showFaceDetectionPopOut = ref(false)  // faceDetectionVisibleから変更
// const currentUserToken = ref('')
const selectedUserForFace = ref(null)
// const currentUserRole = ref(false) // 現在のユーザーが管理者かどうか
// hover状態管理を追加
const hoveredUserId = ref(null)
// 状態更新のloading状態を追加
const statusLoading = ref({})
// 多選択状態管理を追加
const selectedUsers = ref([])
// パスワードリセット関連の状態を追加
const passwordResetDialogVisible = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')
const passwordResetFormRef = ref()

// 検索フィルター関連の状態を追加
const filterTags = ref([])
const showFilterDialog = ref(false)
const filterForm = reactive({
  key: '',
  value: ''
})

// パスワード確認検証状態を追加
const passwordMatchStatus = ref('')
const passwordMatchMessage = ref('')

const userForm = reactive({
  id: undefined,
  username: '',
  email: '',
  full_name: '',
  is_admin: false,
  is_active: true,
  password: ''
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const filterOptions = [
  { value: 'username', label: 'ユーザー名' },
  { value: 'email', label: 'メール' },
  { value: 'full_name', label: '氏名' },
  { value: 'is_active', label: 'アクティブ状態' },
  { value: 'is_admin', label: '管理者役割' },
  { value: 'set_face', label: '顔データあり' }
]

const formRules = computed(() => {
  return {
    username: [
      { required: true, message: 'ユーザー名を入力してください', trigger: 'blur' },
      { min: 3, max: 30, message: '長さは3〜30文字である必要があります', trigger: 'blur' }
    ],
    email: [
      { required: true, message: 'メールアドレスを入力してください', trigger: 'blur' },
      { type: 'email', message: '有効なメールアドレスを入力してください', trigger: 'blur' }
    ],
    password: [
      { required: !userForm.id, message: 'パスワードを入力してください', trigger: 'blur' },
      { min: 6, message: 'パスワードは少なくとも6文字である必要があります', trigger: 'blur' }
    ]
  }
})

const passwordResetRules = computed(() => {
  return {
    newPassword: [
      { required: true, message: '新しいパスワードを入力してください', trigger: 'blur' },
      { min: 6, message: 'パスワードは少なくとも6文字である必要があります', trigger: 'blur' }
    ],
    confirmPassword: [
      { required: true, message: 'パスワードを確認してください', trigger: 'blur' },
      { min: 6, message: 'パスワードは少なくとも6文字である必要があります', trigger: 'blur' }
    ]
  }
})

const formTitle = computed(() => {
  return userForm.id ? 'ユーザーを編集' : '新しいユーザーを作成'
})

// // 現在のユーザーが役割を変更できるかどうかを判断（管理者のみが役割を変更可能）
// const canModifyRole = computed(() => {
//   return currentUserRole.value === true
// })

onMounted(() => {
  fetchUsers()
})

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString()
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

    // クエリパラメータを構築
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size
    }

    // フィルターパラメータを追加
    filterTags.value.forEach(tag => {
      params[tag.name] = tag.value
    })

    const queryParams = new URLSearchParams(params).toString()

    const response = await apiClient.get(`/api/v1/admin/users?${queryParams}`)

    if (response.data.success) {
      users.value = response.data.data
      pagination.total = response.data.total || users.value.length
    } else {
      ElMessage.error(response.data.message || 'ユーザーの取得に失敗しました')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'ユーザーの取得中にエラーが発生しました')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size) => {
  pagination.page = 1
  pagination.size = size
  fetchUsers()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  fetchUsers()
}

const openDrawer = () => {
  resetForm()
  drawerVisible.value = true
}

const editUser = (user) => {
  Object.assign(userForm, {
    ...user,
    password: '' // 編集時は元のパスワードを表示しない
  })
  drawerVisible.value = true
}

const handleDrawerClose = (done) => {
  resetForm()
  done()
}

const resetForm = () => {
  userForm.id = undefined
  userForm.username = ''
  userForm.email = ''
  userForm.full_name = ''
  userForm.is_admin = false
  userForm.is_active = true
  userForm.password = ''
  userFormRef.value?.clearValidate()
}

const submitForm = async () => {
  try {
    await userFormRef.value.validate()
  } catch {
    return
  }

  submitting.value = true

  try {
    let response
    const token = localStorage.getItem('token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

    const userData = {
      username: userForm.username,
      email: userForm.email,
      full_name: userForm.full_name,
      is_active: userForm.is_active,
      ...(userForm.password && { password: userForm.password }),
      is_admin: userForm.is_admin,
    }


    if (userForm.id) {
      // 既存のユーザーを更新
      response = await apiClient.put(`/api/v1/admin/users/${userForm.id}`, userData)
    } else {
      // 新しいユーザーを作成
      response = await apiClient.post(`/api/v1/admin/users/`, {
        ...userData,
        password: userForm.password
      })
    }

    if (response.data.success) {
      ElMessage.success(
        userForm.id ? 'ユーザーが正常に更新されました' : 'ユーザーが正常に作成されました'
      )
      drawerVisible.value = false
      resetForm()
      fetchUsers()
    } else {
      ElMessage.error(response.data.message || '操作に失敗しました')
    }
  } catch (error) {
    ElMessage.error(
      error.response?.data?.detail ||
      (userForm.id ? 'ユーザーの更新に失敗しました' : 'ユーザーの作成に失敗しました')
    )
  } finally {
    submitting.value = false
  }
}

const openFaceDetection = (user) => {
  selectedUserForFace.value = user
  showFaceDetectionPopOut.value = true  // faceDetectionVisible.value = trueから変更
}

// マウスイベント処理メソッドを追加
const handleMouseEnter = (userId) => {
  hoveredUserId.value = userId
}

const handleMouseLeave = () => {
  hoveredUserId.value = null
}


// 管理者としてユーザーの顔を更新する関数
const updateUserFace = async (imageData) => {
  try {
    // 画像をフォームデータとして送信するためにFormDataを作成
    const formData = new FormData();

    // userIdを取得
    const userId = selectedUserForFace.value.id;

    // トークンを取得
    const token = localStorage.getItem('token') || '';

    // base64画像データをblobに変換してフォームデータに追加
    const byteCharacters = atob(imageData.split(',')[1]); // data:image/jpeg;base64,プレフィックスを削除
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

    const blob = new Blob(byteArrays, { type: 'image/jpeg' });
    formData.append('image', blob, 'face_image.jpg');

    // キャプチャされた画像をアップロードして指定されたユーザーの顔を更新
    const response = await apiClient.put(`/api/v1/admin/face/${userId}`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });

    // 'code'フィールドを持つ期待される構造のレスポンスを確認
    if (response.data.code === 200 || response.data.success) {
      ElMessage.success(response.data.message || '顔画像が正常に更新されました');

      // 新しい顔データを反映するためにユーザーリストを更新
      const userIndex = users.value.findIndex(u => u.id === userId);
      if (userIndex !== -1) {
        users.value[userIndex].head_pic = '1'; // 顔データがあることをマーク
      }
    } else {
      ElMessage.error(response.data.message || '顔画像の更新に失敗しました');
    }

    // return response.data;
  } catch (error) {
    // console.error('ユーザー顔画像の更新中にエラーが発生しました:', error);
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail);
    } else {
      ElMessage.error(error.message || '顔画像の更新中にエラーが発生しました');
    }
    throw error;
  }
  finally {

    // ユーザーリストを更新
    fetchUsers();
  }
}

const handleStatusChange = async (user) => {
  try {
    statusLoading.value[user.id] = true

    const token = localStorage.getItem('token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

    const response = await apiClient.put(`/api/v1/admin/users/${user.id}`, {
      is_active: user.is_active
    })

    if (response.data.success) {
      ElMessage.success(`ユーザーが正常に${user.is_active ? '有効化' : '無効化'}されました`)
    } else {
      // API呼び出しが失敗した場合は変更を元に戻す
      user.is_active = !user.is_active
      ElMessage.error(response.data.message || 'ユーザー状態の更新に失敗しました')
    }
  } catch (error) {
    // API呼び出しが失敗した場合は変更を元に戻す
    user.is_active = !user.is_active
    ElMessage.error(error.response?.data?.detail || 'ユーザー状態の更新に失敗しました')
  } finally {
    statusLoading.value[user.id] = false
  }
}

const deleteUser = async (userId) => {
  try {
    await ElMessageBox.confirm(
      '本当にこのユーザーを削除してもよろしいですか？この操作は元に戻せません。',
      '警告',
      {
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        type: 'warning'
      }
    )

    await apiClient.delete(`/api/v1/users/${userId}`)
    ElMessage.success('ユーザーが正常に削除されました')
    fetchUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'ユーザーの削除に失敗しました')
  }
}

const refreshUsers = async () => {
  loading.value = true
  try {
    await fetchUsers()
    ElMessage.success('ユーザーリストが正常に更新されました')
  } catch (error) {
    ElMessage.error('ユーザーリストの更新に失敗しました')
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const handleBatchAction = async (command) => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('少なくとも1名のユーザーを選択してください')
    return
  }

  try {
    switch (command) {
      case 'activate':
        await batchUpdateStatus(true)
        break
      case 'deactivate':
        await batchUpdateStatus(false)
        break
      case 'reset-password':
        await batchResetPassword()
        break
      case 'delete-face':
        await batchDeleteFace()
        break
    }
  } catch (error) {
    // console.error('一括操作に失敗しました:', error)
  }
}

const batchUpdateStatus = async (isActive) => {
  try {
    await ElMessageBox.confirm(
      `${selectedUsers.value.length} 名のユーザーを${isActive ? '有効化' : '無効化'}してもよろしいですか？`,
      '一括操作の確認',
      {
        confirmButtonText: '確認',
        cancelButtonText: 'キャンセル',
        type: 'warning'
      }
    )

    const token = localStorage.getItem('token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

    // 新しい一括操作APIエンドポイントを使用
    const response = await apiClient.post(`/api/v1/admin/batch/${isActive ? 'active' : 'inactive'}`, {
      user_ids: selectedUsers.value.map(user => user.id)
    })

    if (response.data.success) {
      const result = response.data.data
      ElMessage.success(`${result.total_count} 名中 ${result.success_count} 名のユーザーが正常に${isActive ? '有効化' : '無効化'}されました`)

      // ローカルのユーザー状態を更新
      selectedUsers.value.forEach(user => {
        const userIndex = users.value.findIndex(u => u.id === user.id)
        if (userIndex !== -1) {
          users.value[userIndex].is_active = isActive
        }
      })
    } else {
      ElMessage.error(response.data.message || '一括操作に失敗しました')
    }

    // 選択をクリアしてリストを更新
    selectedUsers.value = []
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '一括操作に失敗しました')
    }
  }
}

const batchResetPassword = async () => {
  try {
    await ElMessageBox.confirm(
      `${selectedUsers.value.length} 名のユーザーのパスワードをリセットしてもよろしいですか？`,
      'パスワードリセットの確認',
      {
        confirmButtonText: '続行',
        cancelButtonText: 'キャンセル',
        type: 'warning'
      }
    )

    // パスワード入力ダイアログを表示
    newPassword.value = ''
    confirmPassword.value = ''
    passwordMatchStatus.value = ''
    passwordMatchMessage.value = ''
    passwordResetDialogVisible.value = true
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('パスワードリセットがキャンセルされました')
    }
  }
}

const confirmPasswordReset = async () => {
  try {
    await passwordResetFormRef.value.validate()
  } catch {
    return
  }

  submitting.value = true

  try {
    const token = localStorage.getItem('token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

    // 新しい一括パスワードリセットAPIエンドポイントを使用
    const response = await apiClient.post(`/api/v1/admin/batch/reset-password`, {
      user_ids: selectedUsers.value.map(user => user.id),
      value: newPassword.value
    })

    if (response.data.success) {
      const result = response.data.data
      ElMessage.success(`${result.total_count} 名中 ${result.success_count} 名のユーザーのパスワードが正常にリセットされました`)
    } else {
      ElMessage.error(response.data.message || 'パスワードリセットに失敗しました')
    }

    // ダイアログを閉じて選択をクリア
    passwordResetDialogVisible.value = false
    newPassword.value = ''
    confirmPassword.value = ''
    selectedUsers.value = []
    fetchUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'パスワードリセットに失敗しました')
  } finally {
    submitting.value = false
  }
}

// パスワード一致検証メソッド
const validatePasswordMatch = () => {
  if (!confirmPassword.value) {
    passwordMatchStatus.value = ''
    passwordMatchMessage.value = ''
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    passwordMatchStatus.value = 'error'
    passwordMatchMessage.value = 'パスワードが一致しません'
  } else {
    passwordMatchStatus.value = 'success'
    passwordMatchMessage.value = 'パスワードが一致します'
  }
}

// パスワードが有効かどうかを計算（送信ボタンを無効化するために使用）
const isPasswordValid = computed(() => {
  return newPassword.value.length >= 6 &&
    confirmPassword.value.length >= 6 &&
    newPassword.value === confirmPassword.value
})

const handlePasswordResetCancel = () => {
  passwordResetDialogVisible.value = false
  newPassword.value = ''
  confirmPassword.value = ''
  passwordMatchStatus.value = ''
  passwordMatchMessage.value = ''
  passwordResetFormRef.value?.clearValidate()
}

const batchDeleteFace = async () => {
  try {
    await ElMessageBox.confirm(
      `${selectedUsers.value.length} 名のユーザーの顔データを削除してもよろしいですか？この操作は元に戻せません。`,
      '顔データ削除の確認',
      {
        confirmButtonText: '顔データを削除',
        cancelButtonText: 'キャンセル',
        type: 'error'
      }
    )

    const token = localStorage.getItem('token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

    // 新しい一括顔データリセットAPIエンドポイントを使用
    const response = await apiClient.post(`/api/v1/admin/batch/reset-face`, {
      user_ids: selectedUsers.value.map(user => user.id)
    })

    if (response.data.success) {
      const result = response.data.data
      ElMessage.success(`${result.total_count} 名中 ${result.success_count} 名のユーザーの顔データが正常に削除されました`)

      // ユーザーリスト中の顔状態を更新
      selectedUsers.value.forEach(user => {
        const userIndex = users.value.findIndex(u => u.id === user.id)
        if (userIndex !== -1) {
          users.value[userIndex].head_pic = '0' // 顔データが削除されたことをマーク
        }
      })
    } else {
      ElMessage.error(response.data.message || '顔データの削除に失敗しました')
    }

    // 選択をクリアしてリストを更新
    selectedUsers.value = []
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '顔データの削除に失敗しました')
    }
  }
}

// 新しいフィルタータグ関連メソッド
const onFilterKeyChange = () => {
  filterForm.value = ''
}

const addFilterTag = () => {
  if (!filterForm.key || (filterForm.value !== false && !filterForm.value)) return

  // タグラベル表示名を取得
  const option = filterOptions.find(opt => opt.value === filterForm.key)
  const label = option ? option.label : filterForm.key

  // 同じフィルター条件が既に存在するかどうかを確認、存在する場合は置換
  const existingIndex = filterTags.value.findIndex(tag => tag.name === filterForm.key)
  if (existingIndex !== -1) {
    // 既存のフィルター条件を置換
    filterTags.value[existingIndex] = {
      name: filterForm.key,
      value: filterForm.value,
      label: label,
      type: getFilterTagType(filterForm.key)
    }
  } else {
    // 新しいタグを追加
    filterTags.value.push({
      name: filterForm.key,
      value: filterForm.value,
      label: label,
      type: getFilterTagType(filterForm.key)
    })
  }

  // セレクターをリセット
  filterForm.key = ''
  filterForm.value = ''

  // ダイアログを閉じる
  showFilterDialog.value = false

  // ユーザーリストを再取得
  pagination.page = 1
  fetchUsers()
}

const removeFilterTag = (tagName) => {
  const index = filterTags.value.findIndex(tag => tag.name === tagName)
  if (index !== -1) {
    filterTags.value.splice(index, 1)
    fetchUsers()
  }
}

// 新しいメソッド：フィルターダイアログを開く
const closeFilterDialog = () => {
  showFilterDialog.value = false
  filterForm.key = ''
  filterForm.value = ''
}

// 異なるフィルタータイプのタグ色を取得する計算プロパティを追加
const getFilterTagType = (filterName) => {
  switch (filterName) {
    case 'username':
      return 'info'
    case 'email':
      return 'warning'
    case 'full_name':
      return 'success'
    case 'is_active':
      return 'primary'
    case 'is_admin':
      return 'danger'
    case 'set_face':
      return 'warning'
    default:
      return 'primary'
  }
}

</script>


<style scoped>
.user-manager {
  padding: 25px;
}

.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  padding: 25px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.header-buttons {
  display: flex;
  gap: 10px;
  align-items: center;
}

.section-header {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  flex: 1;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: center;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.footer-actions {
  display: flex;
  align-items: center;
}

.drawer-content {
  padding: 20px 0;
}

.form-actions {
  display: flex;
  margin-top: 30px;
  gap: 10px;
}

.role-hint {
  margin-top: 5px;
}

.selection-info {
  margin-left: 15px;
  color: #606266;
  font-size: 14px;
  background: #f5f7fa;
  padding: 5px 10px;
  border-radius: 4px;
}

/* ヘッダーアクションのレスポンシブ調整 */
@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .header-buttons {
    justify-content: center;
    flex-wrap: wrap;
  }

  .selection-info {
    margin-left: 0;
    margin-top: 10px;
    text-align: center;
  }
}

/* レスポンシブ調整 */
@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .header-buttons {
    justify-content: center;
  }

  .table-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .footer-actions {
    justify-content: center;
  }
}

/* ドロワーのスタイル最適化 */
:deep(.el-drawer__header) {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

:deep(.el-drawer__body) {
  padding: 0 20px;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-input__inner) {
  height: 40px;
}

/* アバターのスタイル最適化 */
:deep(.el-avatar) {
  background-color: #409eff;
  color: white;
  font-weight: 500;
}

/* 顔ボタンのスタイル最適化 */
:deep(.el-button .el-icon) {
  margin-right: 5px;
}

/* ダイアログのフッタースタイル */
:deep(.el-dialog__footer) {
  text-align: right;
}
</style>