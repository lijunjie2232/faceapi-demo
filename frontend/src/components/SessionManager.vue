<template>
  <div v-if="showSessionBox" class="session-manager-wrapper">
    <!-- 折りたたみボタン -->
    <div 
      class="fold-toggle" 
      :class="{ 'folded': isFolded }"
      @click="toggleFold"
    >
      <el-button 
        circle 
        size="small" 
        :type="sessionStatus.type"
        :icon="isFolded ? 'ArrowLeft' : 'ArrowRight'"
      />
    </div>
    
    <!-- セッション管理パネル -->
    <div class="session-manager-box" :class="{ 'folded': isFolded }">
      <div class="session-info">
        <div class="session-status">
          <el-tag :type="sessionStatus.type" size="small">
            {{ sessionStatus.text }}
          </el-tag>
        </div>
      
      <div v-if="sessionData" class="session-details">
        <div class="expire-info">
          <span class="label">有効期限:</span>
          <span class="value">{{ formatExpireTime(sessionData.expires_at) }}</span>
        </div>
        <div class="remaining-info">
          <span class="label">残り時間:</span>
          <span class="value">{{ formatRemainingTime(sessionData.remaining_time) }}</span>
        </div>
      </div>
      
        <div v-if="errorMessage" class="error-message">
          <el-alert
            :title="errorMessage"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    
      <div class="session-actions">
        <el-button 
          size="small" 
          type="primary" 
          @click="refreshSessionInfo"
          :loading="refreshing"
          :disabled="!hasValidSession"
        >
          情報を更新
        </el-button>
        <el-button 
          size="small" 
          type="danger" 
          @click="deleteCurrentSession"
          :loading="deleting"
          :disabled="!hasValidSession"
        >
          セッションを削除
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../utils/api'

const props = defineProps({
  apiBaseUrl: {
    type: String,
    default: ''
  },
  sessionToken: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['sessionExpired', 'sessionDeleted'])

// 响应式数据
const sessionData = ref(null)
const refreshing = ref(false)
const deleting = ref(false)
const errorMessage = ref('')
const timer = ref(null)
const isFolded = ref(false)

// 计算属性
const hasValidSession = computed(() => {
  return props.sessionToken && !sessionData.value?.is_expired
})

const showSessionBox = computed(() => {
  return props.sessionToken || errorMessage.value
})

const sessionStatus = computed(() => {
  if (errorMessage.value) {
    return { type: 'danger', text: 'セッションエラー' }
  }
  if (!props.sessionToken) {
    return { type: 'warning', text: 'セッションなし' }
  }
  if (sessionData.value?.is_expired) {
    return { type: 'danger', text: 'セッション期限切れ' }
  }
  return { type: 'success', text: 'セッション有効' }
})

// 有効期限をフォーマット
const formatExpireTime = (expireTime) => {
  if (!expireTime) return '不明'
  try {
    const date = new Date(expireTime)
    return date.toLocaleString('zh-CN')
  } catch {
    return expireTime
  }
}

// 残り時間をフォーマット
const formatRemainingTime = (seconds) => {
  if (seconds <= 0) return '期限切れ'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}時間${minutes}分`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// セッション情報を取得
const getSessionInfo = async () => {
  if (!props.sessionToken) return
  
  try {
    refreshing.value = true
    errorMessage.value = ''
    
    const response = await apiClient.get('/api/v1/session/info', {
      headers: {
        'Session-Token': props.sessionToken
      }
    })
    
    if (response.data.code === 200) {
      sessionData.value = response.data
      // 检查会话是否过期
      if (response.data.is_expired) {
        emit('sessionExpired')
      }
    } else {
      throw new Error(response.data.detail || 'セッション情報の取得に失敗しました')
    }
  } catch (error) {
    console.error('セッション情報の取得に失敗しました:', error)
    errorMessage.value = error.response?.data?.detail || error.message || 'セッション情報の取得に失敗しました'
    sessionData.value = null
  } finally {
    refreshing.value = false
  }
}

// セッション情報を更新
const refreshSessionInfo = async () => {
  await getSessionInfo()
  if (!errorMessage.value) {
    ElMessage.success('セッション情報が更新されました')
  }
}

// 現在のセッションを削除
const deleteCurrentSession = async () => {
  if (!props.sessionToken) return
  
  try {
    await ElMessageBox.confirm(
      '現在のセッションを削除してもよろしいですか？削除後はシステムを続けるために新しいセッションを作成する必要があります。',
      '削除の確認',
      {
        confirmButtonText: '確定',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      }
    )
    
    deleting.value = true
    errorMessage.value = ''
    
    const response = await apiClient.delete('/api/v1/session/current', {
      headers: {
        'Session-Token': props.sessionToken
      }
    })
    
    if (response.data.code === 200) {
      ElMessage.success('セッションが正常に削除されました')
      sessionData.value = null
      emit('sessionDeleted')
    } else {
      throw new Error(response.data.detail || 'セッションの削除に失敗しました')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('セッションの削除に失敗しました:', error)
      errorMessage.value = error.response?.data?.detail || error.message || 'セッションの削除に失敗しました'
    }
  } finally {
    deleting.value = false
  }
}

// 残り時間を定期的に更新
const updateRemainingTime = () => {
  if (sessionData.value && sessionData.value.remaining_time > 0) {
    sessionData.value.remaining_time -= 1
    if (sessionData.value.remaining_time <= 0) {
      sessionData.value.is_expired = true
      emit('sessionExpired')
    }
  }
}

// タイマーを起動
const startTimer = () => {
  if (timer.value) {
    clearInterval(timer.value)
  }
  timer.value = setInterval(updateRemainingTime, 1000)
}

// タイマーをクリーンアップ
const stopTimer = () => {
  if (timer.value) {
    clearInterval(timer.value)
    timer.value = null
  }
}

// 折りたたみ状態を切り替え
const toggleFold = () => {
  isFolded.value = !isFolded.value
}

// sessionTokenの変化を監視
watch(() => props.sessionToken, (newToken) => {
  if (newToken) {
    getSessionInfo()
    startTimer()
  } else {
    sessionData.value = null
    errorMessage.value = ''
    stopTimer()
  }
})

onMounted(() => {
  if (props.sessionToken) {
    getSessionInfo()
    startTimer()
  }
})

onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
.session-manager-wrapper {
  position: fixed;
  top: 100px;
  right: 20px;
  z-index: 1000;
  display: flex;
  align-items: flex-start;
}

.fold-toggle {
  margin-right: 8px;
  transition: transform 0.3s ease;
}

.fold-toggle.folded {
  transform: translateX(-8px);
}

.session-manager-box {
  width: 320px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 16px;
  border: 1px solid #ebeef5;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  min-width: 0;
}

.session-manager-box.folded {
  width: 0;
  padding: 0 0 0 0;
  border-width: 0;
  box-shadow: none;
  margin-left: 0;
}

.session-info {
  margin-bottom: 16px;
}

.session-status {
  margin-bottom: 12px;
  text-align: center;
}

.session-details {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 12px;
}

.expire-info, .remaining-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.expire-info:last-child, .remaining-info:last-child {
  margin-bottom: 0;
}

.label {
  color: #606266;
  font-weight: 500;
}

.value {
  color: #303133;
  font-weight: 600;
}

.error-message {
  margin-bottom: 12px;
}

.session-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.session-actions .el-button {
  flex: 1;
}
</style>