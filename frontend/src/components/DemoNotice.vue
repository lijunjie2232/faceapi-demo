<template>
  <div v-if="floating" class="demo-notice-float">
    <transition name="slide-fade">
      <div v-show="isVisible" class="demo-notice-content">
        <el-alert
          :title="title"
          :type="type"
          :description="description"
          show-icon
          :closable="false"
          class="demo-alert"
        />
      </div>
    </transition>
    
    <div class="demo-toggle-btn" @click="toggleNotice">
      <el-button 
        circle 
        :type="isVisible ? 'primary' : 'info'"
        :icon="isVisible ? 'ArrowDown' : 'ArrowUp'"
        size="small"
      />
    </div>
  </div>
  
  <!-- 非浮动版本，用于登录和注册页面 -->
  <div v-else class="demo-notice-inline">
    <el-alert
      :title="title"
      :type="type"
      :description="description"
      show-icon
      :closable="false"
      class="demo-alert"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ArrowDown, ArrowUp } from '@element-plus/icons-vue'

const props = defineProps({
  isLoginPage: {
    type: Boolean,
    default: false
  },
  showSessionInfo: {
    type: Boolean,
    default: true
  },
  floating: {
    type: Boolean,
    default: true
  }
})

const isVisible = ref(true)

const toggleNotice = () => {
  isVisible.value = !isVisible.value
}

const title = computed(() => {
  return props.isLoginPage ? 'デモシステムについて' : 'デモ版システム'
})

const type = computed(() => {
  return props.isLoginPage ? 'warning' : 'info'
})

const description = computed(() => {
  let desc = '本プロジェクトはデモ版です。'
  
  if (props.showSessionInfo) {
    desc += '各セッションは5分間有効で、その後自動的に破棄されます。各セッションのデータは独立しており、セキュリティ上の心配はございません。'
  }
  
  return desc
})
</script>

<style scoped>
/* 浮动版本样式 */
.demo-notice-float {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column-reverse;
  align-items: flex-end;
  gap: 10px;
}

/* 内联版本样式（用于登录和注册页面） */
.demo-notice-inline {
  margin-bottom: 20px;
}

.demo-notice-inline.login-page {
  max-width: 500px;
  margin: 0 auto 20px;
}

.demo-notice-content {
  max-width: 350px;
  transition: all 0.3s ease;
}

.demo-alert {
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  margin-bottom: 0;
}

.demo-toggle-btn {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.demo-toggle-btn:hover {
  transform: scale(1.1);
}

/* 滑动淡入动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.3s ease-in;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

/* 在小屏幕上调整位置 */
@media (max-width: 768px) {
  .demo-notice-float {
    bottom: 10px;
    right: 10px;
  }
  
  .demo-notice-content {
    max-width: 300px;
  }
}
</style>