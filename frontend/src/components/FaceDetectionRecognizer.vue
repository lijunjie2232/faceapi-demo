<template>
  <div class="face-detection-recognizer component-container">
    <el-row :gutter="30" class="main-row">
      <el-col :xs="24" :sm="24" :md="12" :lg="12" class="col-container">
        <div class="upload-section">
          <h3 class="section-header">認識用画像をアップロード</h3>

          <!-- 条件付きレンダリング：画像が存在する場合はプレビューを表示、そうでない場合はアップロードエリアを表示 -->
          <div v-if="imagePreview" class="image-preview-container">
            <div class="preview-wrapper">
              <img :src="imagePreview" alt="Preview" class="preview-image rounded-img" />
            </div>

            <div class="preview-controls">
              <el-button type="primary" @click="clearImage" class="clear-btn">
                <el-icon>
                  <Refresh />
                </el-icon>
                <span>新しい画像</span>
              </el-button>

              <el-button type="primary" @click="verifyFace" :loading="loading" :disabled="!imagePreview || loading"
                class="recognize-btn">
                <el-icon>
                  <VideoCamera />
                </el-icon>
                <span>顔を検証{{ loading ? '...' : '' }}</span>
              </el-button>
            </div>
          </div>

          <div v-else class="upload-area">
            <el-upload class="image-uploader" drag :show-file-list="false" accept="image/*"
              :before-upload="handleImageUpload">
              <el-icon class="uploader-icon">
                <Upload />
              </el-icon>
              <div class="uploader-text">クリックまたはドラッグして画像をこのエリアにアップロード</div>
              <p class="uploader-hint">JPG、PNG、WEBP形式をサポート</p>
            </el-upload>
          </div>

          <!-- カメラボタンは常に表示 -->
          <el-button type="primary" @click="showPopOutWindow = true" class="camera-toggle-btn"
            :style="imagePreview ? 'margin-top: 15px;' : ''">
            <el-icon>
              <VideoCamera />
            </el-icon>
            <span>カメラを使用</span>
          </el-button>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="12" :lg="12" class="col-container">
        <div class="result-section">
          <h3 class="section-header">検証結果</h3>
          <div v-if="!userInfo && !verificationResult" class="no-results">
            <el-empty description="まだ結果がありません" :image-size="100">
              <p>画像をアップロードするかカメラを使用し、「顔を検証」をクリックして結果を表示</p>
            </el-empty>
          </div>

          <!-- 検証結果が存在する場合は表示 -->
          <div v-if="verificationResult || userInfo" class="verification-result">
            <el-card class="result-item" :class="{ 'recognized': verificationResult?.recognized || userInfo }">
              <template #header>
                <div class="card-header">
                  <span :class="(verificationResult && verificationResult.recognized) || userInfo ? 'recognized-text' : 'unknown-text'">
                    {{ (verificationResult && verificationResult.recognized) || userInfo ? '✅ 検証済み' : '❓ 検証失敗' }}
                  </span>
                </div>
              </template>
              <div class="result-content">
                <p><strong>ステータス:</strong> {{ verificationResult?.message || (userInfo ? '検証成功' : '検証保留中') }}</p>

                <!-- 検証済みの場合はユーザー情報を表示 -->
                <div v-if="userInfo" class="user-info-detail-container">
                  <div class="user-card">
                    <div class="user-header">
                      <div class="user-avatar">
                        <el-avatar :size="80" shape="circle" :src="getUserAvatar()">
                          {{ userInfo.full_name ?
                            userInfo.full_name.charAt(0).toUpperCase() :
                            userInfo.username.charAt(0).toUpperCase() }}
                        </el-avatar>
                      </div>
                      <div class="user-basic-info">
                        <h2>{{ userInfo.full_name || userInfo.username }}</h2>
                        <p>@{{ userInfo.username }}</p>
                      </div>
                    </div>

                    <div class="user-details">
                      <div class="detail-row">
                        <div class="detail-item">
                          <label>ID:</label>
                          <span>{{ userInfo.id }}</span>
                        </div>
                        <div class="detail-item">
                          <label>メール:</label>
                          <span>{{ userInfo.email }}</span>
                        </div>
                      </div>

                      <div class="detail-row">
                        <div class="detail-item">
                          <label>役割:</label>
                          <el-tag :type="userInfo.is_admin ? 'danger' : 'info'" size="small">
                            {{ userInfo.is_admin ? '管理者' : 'ユーザー' }}
                          </el-tag>
                        </div>
                        <div class="detail-item">
                          <label>ステータス:</label>
                          <el-tag :type="userInfo.is_active ? 'success' : 'danger'" size="small">
                            {{ userInfo.is_active ? 'アクティブ' : '非アクティブ' }}
                          </el-tag>
                        </div>
                      </div>

                      <div class="detail-row">
                        <div class="detail-item full-width">
                          <label>作成日:</label>
                          <span>{{ userInfo.created_at }}</span>
                        </div>
                      </div>

                      <div class="detail-row">
                        <div class="detail-item full-width">
                          <label>最終更新:</label>
                          <span>{{ userInfo.updated_at }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 検証失敗時に失敗メッセージを表示 -->
                <div v-if="verificationResult && !verificationResult.recognized && !userInfo">
                  <p>顔の検証に失敗しました。もう一度お試しください。</p>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 認識結果が存在する場合は表示 -->
          <div v-if="results.length > 0" class="recognition-results">
            <h4>認識結果</h4>
            <div class="results-list">
              <el-card v-for="(result, index) in results" :key="index" class="result-item"
                :class="{ 'recognized': result.recognized }">
                <template #header>
                  <div class="card-header">
                    <span :class="result.recognized ? 'recognized-text' : 'unknown-text'">
                      {{ result.recognized ? '✅ 認識済み' : '❓ 不明な顔' }}
                    </span>
                  </div>
                </template>
                <div class="result-content">
                  <p><strong>ユーザーID:</strong> {{ result.user_id || 'N/A' }}</p>
                  <p><strong>信頼度:</strong>
                    <el-progress :percentage="result.confidence ? parseFloat((result.confidence * 100).toFixed(2)) : 0"
                      :color="result.confidence > 0.7 ? '#67C23A' : result.confidence > 0.5 ? '#E6A23C' : '#F56C6C'"
                      :format="() => result.confidence ? `${(result.confidence * 100).toFixed(2)}%` : 'N/A'" />
                  </p>
                  <p><strong>メッセージ:</strong> {{ result.message }}</p>

                  <!-- 認識された場合はユーザー情報を表示 -->
                  <div v-if="result.recognized && result.user_info" class="user-info-display">
                    <h4>ユーザー情報</h4>
                    <div class="user-info-grid">
                      <div class="info-item">
                        <label>ユーザー名:</label>
                        <span>{{ result.user_info.username }}</span>
                      </div>
                      <div class="info-item">
                        <label>氏名:</label>
                        <span>{{ result.user_info.full_name || 'N/A' }}</span>
                      </div>
                      <div class="info-item">
                        <label>メール:</label>
                        <span>{{ result.user_info.email }}</span>
                      </div>
                      <div class="info-item">
                        <label>役割:</label>
                        <el-tag :type="result.user_info.is_admin ? 'danger' : 'info'" size="small">
                          {{ result.user_info.is_admin ? '管理者' : 'ユーザー' }}
                        </el-tag>
                      </div>
                      <div class="info-item">
                        <label>ステータス:</label>
                        <el-tag :type="result.user_info.is_active ? 'success' : 'danger'" size="small">
                          {{ result.user_info.is_active ? 'アクティブ' : '非アクティブ' }}
                        </el-tag>
                      </div>
                    </div>

                    <!-- アバター -->
                    <div class="avatar-section" v-if="result.user_info.head_pic">
                      <label>アバター:</label>
                      <el-avatar :size="60" :src="'data:image/jpeg;base64,' + result.user_info.head_pic" />
                    </div>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 顔検出ポップアウトウィンドウ -->
    <FaceDetectionPopOut v-model="showPopOutWindow" :_handler="handleCameraCapture" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus'
import { Upload, VideoCamera, Refresh } from '@element-plus/icons-vue'
import apiClient from '../utils/api'
import FaceDetectionPopOut from './FaceDetectionPopOut.vue'

const imagePreview = ref(null);
const imageFile = ref(null);
const results = ref([]);
const verificationResult = ref(null);
const userInfo = ref(null); // ユーザー情報用の新しいref
const loading = ref(false);
const showPopOutWindow = ref(false);
const API_BASE_URL = ref(import.meta.env.VITE_API_BASE_URL || "");

const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });
};

const handleImageUpload = (file) => {
  imageFile.value = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    imagePreview.value = e.target.result;
  };
  reader.readAsDataURL(file);

  // この時点でサーバーへのアップロードを防止
  return false;
};

const handleCameraCapture = async (imageData) => {
  try {
    // データURLからbase64データを抽出
    const base64Data = imageData.split(',')[1];
    const byteCharacters = atob(base64Data);
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

    // 認識用に一時的なファイルオブジェクトを作成して保存
    imageFile.value = new File([blob], 'face_capture.jpg', { type: 'image/jpeg' });
    imagePreview.value = imageData; // キャプチャされた画像でプレビューを更新

    ElMessage.success('画像が正常にキャプチャされました');
  } catch (error) {
    // console.error('カメラキャプチャの処理中にエラーが発生しました:', error);
    ElMessage.error('キャプチャされた画像の処理中にエラーが発生しました');
  }
};

const verifyFace = async () => {
  if (!imageFile.value) {
    ElMessage.error('まず画像を選択してください');
    return;
  }

  loading.value = true;

  try {
    // 画像を送信するためのFormDataを作成
    const formData = new FormData();

    // データURLからbase64データを抽出しBlobに変換
    const base64Data = await fileToBase64(imageFile.value);
    const extractedBase64 = base64Data.split(',')[1];
    const byteCharacters = atob(extractedBase64);
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

    const blob = new Blob(byteArrays, { type: imageFile.value.type });
    formData.append('image', blob, imageFile.value.name);

    // キャプチャされた画像を検証エンドポイントに送信
    const response = await apiClient.post('/api/v1/face/verify', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    // 'code'フィールドを持つ期待される構造のレスポンスを確認
    if (response.data.code === 200 || response.data.success || response.data.recognized === true) {
      verificationResult.value = response.data.data;
      // トークンを使用してユーザー情報を取得
      if(response.data.data.token) {
        await getUserInfo(response.data.data.token);
      }
      ElMessage.success(response.data.message || '顔の検証に成功しました');
    } else {
      // 検証失敗
      verificationResult.value = {
        recognized: false,
        message: response.data.message || '顔の検証に失敗しました'
      };
      ElMessage.warning(response.data.message || '顔の検証に失敗しました、もう一度お試しください');
    }
  } catch (error) {
    // console.error('顔検証中にエラーが発生しました:', error);

    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message);
    } else {
      ElMessage.error('顔検証中にエラーが発生しました');
    }

    verificationResult.value = {
      recognized: false,
      message: error.response?.data?.message || '顔検証中にエラーが発生しました'
    };
  } finally {
    loading.value = false;
  }
};

// トークンを使用してユーザー情報を取得する関数
const getUserInfo = async (token) => {
  try {
    // 認証ヘッダー付きでAPIリクエストを行う
    const response = await apiClient.get('/api/v1/user/me', {
      headers: {
        'Authorization': `Bearer ${token}`  // Bearerトークン形式を使用
      }
    });

    if (response.data.code === 200) {
      userInfo.value = response.data.data;
    } else {
      ElMessage.error(response.data.message || 'ユーザー情報の取得に失敗しました');
    }
  } catch (error) {
    // console.error('ユーザー情報の取得中にエラーが発生しました:', error);
    ElMessage.error('ユーザー情報の取得中にエラーが発生しました');
  }
}

const clearImage = () => {
  imagePreview.value = null;
  imageFile.value = null;
  results.value = [];
  verificationResult.value = null;
  userInfo.value = null;
};

// ユーザーアバターURLを取得する関数
const getUserAvatar = () => {
  if (userInfo.value && userInfo.value.head_pic && userInfo.value.head_pic.trim() !== '') {
    // head_picが完全なURLの場合は直接使用
    return 'data:image/jpeg;base64,' + userInfo.value.head_pic;
  }
  return undefined; // el-avatarにデフォルトスロットコンテンツを表示させるためにundefinedを返す
};
</script>

<style scoped>
.face-detection-recognizer {
  padding: 25px;
}

.main-row {
  margin-bottom: 30px;
}

.col-container {
  margin-bottom: 20px;
}

.upload-section {
  text-align: center;
  background: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.upload-area {
  margin-bottom: 25px;
}

.image-preview-container {
  margin-bottom: 25px;
}

.image-uploader {
  margin-bottom: 25px;
}

.uploader-icon {
  font-size: 68px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  line-height: 178px;
  text-align: center;
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  margin: 0 auto;
  transition: all 0.3s;
}

.uploader-icon:hover {
  border-color: #409eff;
  color: #409eff;
}

.uploader-text {
  font-size: 16px;
  color: #606266;
  margin-top: 15px;
}

.uploader-hint {
  font-size: 14px;
  color: #909399;
  margin: 10px 0 0;
}

.preview-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 8px;
}

.preview-controls {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 20px;
}

.clear-btn {
  width: 120px;
  padding: 10px 15px;
  font-size: 14px;
}

.recognize-btn {
  width: 180px;
  padding: 10px 15px;
  font-size: 14px;
}

.camera-toggle-btn {
  width: 100%;
  max-width: 300px;
  padding: 12px 20px;
  font-size: 16px;
  font-weight: 500;
}

.result-section {
  min-height: 400px;
  background: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #909399;
  text-align: center;
}

.result-item {
  margin-bottom: 15px;
  border-radius: 8px;
}

.result-item.recognized {
  border-left: 4px solid #67c23a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recognized-text {
  color: #67c23a;
  font-weight: bold;
}

.unknown-text {
  color: #e6a23c;
  font-weight: bold;
}

.result-content p {
  margin: 12px 0;
}

.result-content p:last-child {
  margin-bottom: 0;
}

.user-info-detail-container {
  margin: 30px auto;
  max-width: 600px;
}

.user-info-detail-container h3 {
  margin-bottom: 20px;
  color: #303133;
  font-weight: 500;
  text-align: center;
}

.user-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 25px;
  border: 1px solid #ebeef5;
  margin: 0 auto;
}

.user-header {
  display: flex;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.user-avatar {
  margin-right: 20px;
}

.user-basic-info h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.user-basic-info p {
  margin: 5px 0 0;
  color: #909399;
  font-size: 16px;
}

.user-details .detail-row {
  display: flex;
  margin-bottom: 15px;
}

.user-details .detail-row:last-child {
  margin-bottom: 0;
}

.user-details .detail-item {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.user-details .detail-item.full-width {
  flex: none;
  width: 100%;
}

.user-details .detail-item label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 5px;
  font-weight: 500;
}

.user-details .detail-item span {
  font-size: 15px;
  color: #606266;
  padding: 2px 0;
}

.user-card .el-tag {
  margin-top: 8px;
  max-width: 100px;
}

.user-info-display {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.user-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 10px 0;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 3px;
  font-weight: 500;
}

.info-item span {
  font-size: 14px;
  color: #606266;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.avatar-section label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  min-width: 60px;
}
</style>