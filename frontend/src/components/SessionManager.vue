<template>
  <div v-if="showSessionBox" class="session-manager-box">
    <div class="session-info">
      <div class="session-status">
        <el-tag :type="sessionStatus.type" size="small">
          {{ sessionStatus.text }}
        </el-tag>
      </div>
      
      <div v-if="sessionData" class="session-details">
        <div class="expire-info">
          <span class="label">过期时间:</span>
          <span class="value">{{ formatExpireTime(sessionData.expires_at) }}</span>
        </div>
        <div class="remaining-info">
          <span class="label">剩余时间:</span>
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
        刷新信息
      </el-button>
      <el-button 
        size="small" 
        type="danger" 
        @click="deleteCurrentSession"
        :loading="deleting"
        :disabled="!hasValidSession"
      >
        删除会话
      </el-button>
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

// 计算属性
const hasValidSession = computed(() => {
  return props.sessionToken && !sessionData.value?.is_expired
})

const showSessionBox = computed(() => {
  return props.sessionToken || errorMessage.value
})

const sessionStatus = computed(() => {
  if (errorMessage.value) {
    return { type: 'danger', text: '会话错误' }
  }
  if (!props.sessionToken) {
    return { type: 'warning', text: '无会话' }
  }
  if (sessionData.value?.is_expired) {
    return { type: 'danger', text: '会话已过期' }
  }
  return { type: 'success', text: '会话有效' }
})

// 格式化过期时间
const formatExpireTime = (expireTime) => {
  if (!expireTime) return '未知'
  try {
    const date = new Date(expireTime)
    return date.toLocaleString('zh-CN')
  } catch {
    return expireTime
  }
}

// 格式化剩余时间
const formatRemainingTime = (seconds) => {
  if (seconds <= 0) return '已过期'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 获取会话信息
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
      throw new Error(response.data.detail || '获取会话信息失败')
    }
  } catch (error) {
    console.error('获取会话信息失败:', error)
    errorMessage.value = error.response?.data?.detail || error.message || '获取会话信息失败'
    sessionData.value = null
  } finally {
    refreshing.value = false
  }
}

// 刷新会话信息
const refreshSessionInfo = async () => {
  await getSessionInfo()
  if (!errorMessage.value) {
    ElMessage.success('会话信息已刷新')
  }
}

// 删除当前会话
const deleteCurrentSession = async () => {
  if (!props.sessionToken) return
  
  try {
    await ElMessageBox.confirm(
      '确定要删除当前会话吗？删除后需要重新创建会话才能继续使用系统。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
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
      ElMessage.success('会话删除成功')
      sessionData.value = null
      emit('sessionDeleted')
    } else {
      throw new Error(response.data.detail || '删除会话失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      errorMessage.value = error.response?.data?.detail || error.message || '删除会话失败'
    }
  } finally {
    deleting.value = false
  }
}

// 定时更新剩余时间
const updateRemainingTime = () => {
  if (sessionData.value && sessionData.value.remaining_time > 0) {
    sessionData.value.remaining_time -= 1
    if (sessionData.value.remaining_time <= 0) {
      sessionData.value.is_expired = true
      emit('sessionExpired')
    }
  }
}

// 启动定时器
const startTimer = () => {
  if (timer.value) {
    clearInterval(timer.value)
  }
  timer.value = setInterval(updateRemainingTime, 1000)
}

// 清理定时器
const stopTimer = () => {
  if (timer.value) {
    clearInterval(timer.value)
    timer.value = null
  }
}

// 监听sessionToken变化
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
.session-manager-box {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 320px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  padding: 16px;
  border: 1px solid #ebeef5;
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