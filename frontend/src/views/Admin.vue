<template>
  <div class="admin-panel">
    <el-main class="app-main">
      <!-- デモ通知 -->
      <DemoNotice />
      
      <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
        <el-tab-pane label="ユーザー管理" name="users" class="tab-content">
          <user-manager />
        </el-tab-pane>
        <el-tab-pane label="顔検出認識" name="detection-recognizer" class="tab-content">
          <face-detection-recognizer />
        </el-tab-pane>
      </el-tabs>
    </el-main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import UserManager from '@/components/UserManager.vue';
import FaceDetectionRecognizer from '@/components/FaceDetectionRecognizer.vue';
import DemoNotice from '@/components/DemoNotice.vue';

// デフォルトでアクティブにするタブを設定
const activeTab = ref('users');
</script>

<style scoped>
.app-main {
  padding: 20px;
}

.main-tabs {
  min-height: 500px;
}

.tab-content {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style>