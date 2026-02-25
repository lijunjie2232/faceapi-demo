<template>
  <el-dialog v-model="dialogVisible" title="顔認識" width="700px" :before-close="handleClose"
    class="face-detection-popout">
    <div class="camera-controls">
      <el-button :type="flipEnabled ? 'success' : 'default'" @click="toggleFlip" :disabled="!isCameraOpen"
        class="flip-btn">
        <el-icon>
          <Switch />
        </el-icon>
        <span>{{ flipEnabled ? '反転有効' : '反転無効' }}</span>
      </el-button>
    </div>

    <div v-show="isCameraOpen" class="camera-container">
      <div class="video-wrapper">
        <video ref="videoRef" class="camera-video" :style="videoStyle" autoplay playsinline></video>
        <canvas ref="canvasRef" class="detection-canvas" :style="canvasStyle"></canvas>
      </div>

      <div v-if="loadingModels" class="loading-overlay">
        <el-progress type="circle" :percentage="modelLoadProgress" :width="150" :stroke-width="10" />
        <p>顔検出モデルを読み込み中...</p>
      </div>
    </div>

    <div v-if="!isCameraOpen && !loadingModels" class="placeholder-container">
      <el-empty description="カメラがアクティブではありません" :image-size="150">
        <p>カメラを自動的に起動中...</p>
      </el-empty>
    </div>

    <!-- 顔を検証中のステータスメッセージ -->
    <div v-if="verifyingFace" class="verifying-message">
      <el-alert title="顔を検証中、お待ちください..." type="info" :closable="false" show-icon>
      </el-alert>
    </div>

    <!-- アクションボタン -->
    <div class="button-actions">
      <el-button @click="handleClose">閉じる</el-button>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElDialog, ElButton, ElIcon, ElProgress, ElEmpty, ElMessage, ElAlert } from 'element-plus'
import { FaceUtils } from '@/utils/face.js'

// propsとemitsを定義
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'faceVerified'])

// Refs
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const videoRef = ref(null)
const canvasRef = ref(null)
const isCameraOpen = ref(false)
const loadingModels = ref(true)
const modelLoadProgress = ref(0)
const flipEnabled = ref(!!localStorage.getItem('CameraFlipEnabled')) // localStorageからフリップ状態を読み込み
let faceUtils = null
let detectionInterval = null
const verifyingFace = ref(false) // 複数の検証リクエストを防ぐためのフラグ

// ダイアログの可視性を監視してカメラを自動起動
watch(dialogVisible, async (newVal) => {
  if (newVal && !isCameraOpen.value && !loadingModels.value) {
    // UIがレンダリングされる前にカメラを起動するために少し待機
    setTimeout(async () => {
      await startCamera()
    }, 300)
  } else if (!newVal) {
    // ダイアログが閉じたらカメラを停止
    stopCamera()
  }
})

// ビデオとキャンバスの計算済みスタイル
const videoStyle = computed(() => ({
  transform: flipEnabled.value ? 'scaleX(-1)' : 'none'
}))

const canvasStyle = computed(() => ({
  transform: flipEnabled.value ? 'scaleX(-1)' : 'none'
}))

// フリップ機能の切り替え
const toggleFlip = () => {
  flipEnabled.value = !flipEnabled.value
  // フリップ状態をlocalStorageに保存
  if (flipEnabled.value) {
    localStorage.setItem('CameraFlipEnabled', 'true')
  } else {
    localStorage.removeItem('CameraFlipEnabled')
  }
}

const loadModels = async () => {
  try {
    faceUtils = new FaceUtils()

    // face-api.jsモデルを読み込む
    const success = await faceUtils.loadFaceApi((progress) => {
      modelLoadProgress.value = progress
    })

    if (success) {
      setTimeout(() => {
        loadingModels.value = false
      }, 500)
    }
  } catch (error) {
    // console.error("face-api.jsの読み込みエラー:", error)
    ElMessage.error("顔検出モデルの読み込みに失敗しました")
    loadingModels.value = false
  }
}

// カメラ停止
const stopCamera = () => {
  if (detectionInterval) {
    clearTimeout(detectionInterval) // cancelAnimationFrameの代わりにclearTimeoutを使用
    detectionInterval = null
  }

  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  isCameraOpen.value = false
}

// カメラ開始
const startCamera = async () => {
  if (loadingModels.value) return

  try {
    // カメラへのアクセスを要求
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: "user",
        width: { ideal: 640 },
        height: { ideal: 480 }
      }
    })

    if (videoRef.value) {
      videoRef.value.srcObject = stream
      isCameraOpen.value = true

      // ビデオの読み込みを待ってから顔検出ループを開始
      setTimeout(startFaceDetectionLoop, 500)
    }
  } catch (err) {
    // console.error("カメラにアクセスできませんでした:", err)
    ElMessage.error("カメラにアクセスできませんでした。権限を確認してください。")
  }
}

let stream = null
let ctx = null

// リアルタイム処理のための顔検出ループを開始
const startFaceDetectionLoop = async () => {
  if (!isCameraOpen.value || !videoRef.value || !canvasRef.value || !faceUtils || !dialogVisible.value) return

  try {
    // ビデオ要素の表示寸法を取得
    const video = videoRef.value
    const canvas = canvasRef.value

    // ビデオが読み込まれて寸法が利用可能になるまで待機
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      // ビデオ寸法がまだ準備できていない場合は少し遅れて再試行
      setTimeout(startFaceDetectionLoop, 100)
      return
    }

    // 実際の表示サイズを決定するためにビデオ要素の計算済みスタイルを取得
    const computedStyle = window.getComputedStyle(video)
    const videoDisplayWidth = parseFloat(computedStyle.getPropertyValue('width'))
    const videoDisplayHeight = parseFloat(computedStyle.getPropertyValue('height'))

    // キャンバスの寸法を実際のビデオ表示サイズに合わせて設定
    canvas.width = videoDisplayWidth
    canvas.height = videoDisplayHeight

    // キャンバスの位置をビデオ要素のオフセットに合わせて設定
    canvas.style.position = 'absolute'
    canvas.style.top = video.offsetTop + 'px'
    canvas.style.left = video.offsetLeft + 'px'
    canvas.style.width = videoDisplayWidth + 'px'
    canvas.style.height = videoDisplayHeight + 'px'

    // 有効な場合はキャンバスにフリップ変換を適用
    canvas.style.transform = flipEnabled.value ? 'scaleX(-1)' : 'none'

    // 実際のビデオで顔検出を実行
    const detections = await faceUtils.detectFaces(video)

    // キャンバスに検出結果を描画
    if (ctx == null) {
      ctx = canvas.getContext('2d')
    }

    // 表示サイズに合わせて検出結果をスケーリング
    if (detections.length > 0) {
      // 実際のビデオ要素の表示サイズと内在サイズに基づいてスケール係数を計算
      const scaleX = canvas.width / video.videoWidth
      const scaleY = canvas.height / video.videoHeight

      // ユーティリティ関数を使用して検出結果を描画
      faceUtils.drawDetections(canvas, detections, scaleX, scaleY, flipEnabled.value)

      // 顔を検出し、現在検証中でない場合はサーバーに送信
      if (!verifyingFace.value) {
        // 現在のフレームをキャプチャして検証用に送信
        const imageDataUrl = faceUtils.captureImageFromVideo(video, flipEnabled.value)

        // フォームデータに変換してサーバーに送信
        const formData = faceUtils.imageToFormData(imageDataUrl, 'face_image.jpg')

        // 検証プロセスを開始
        verifyFace(formData)
      }
    } else {
      // 顔が検出されない場合はループを継続
      if (isCameraOpen.value) {
        detectionInterval = setTimeout(startFaceDetectionLoop, 500) // ~2 FPS
      }
    }
  } catch (error) {
    // console.error("顔検出中にエラーが発生しました:", error)
    // 少し遅れて再試行
    if (isCameraOpen.value) {
      detectionInterval = setTimeout(startFaceDetectionLoop, 1000)
    }
  }
}

// サーバーで顔を検証する関数
const verifyFace = async (formData) => {
  if (verifyingFace.value) return // すでに検証中の場合はスキップ

  verifyingFace.value = true

  try {
    // キャプチャされた画像を検証エンドポイントに送信
    const response = await faceUtils.verifyFace(formData)

    // 'code'フィールドを持つ期待される構造のレスポンスを確認
    if (response.code === 200) {
      // レスポンスから関連データを抽出
      const { recognized, user_id, confidence, data, message } = response
      const { token, token_type } = data
      
      // トークンをlocalStorageに保存
      localStorage.setItem('token', token)
      localStorage.setItem('token_type', token_type)

      // ユーザー情報を含む成功メッセージを表示
      ElMessage.success(message || `ユーザー${user_id}として顔が正常に認識されました`);

      // 検証結果とともにイベントを発行
      emit('faceVerified', { 
        success: true, 
        recognized: recognized,
        user_id: user_id,
        confidence: confidence,
        token: token,
        token_type: token_type,
      });

      // 成功した検証後にダイアログを閉じる
      handleClose()
    } else {
      // 検証失敗 - 検出ループを継続
      ElMessage.warning(response.message || '顔認識に失敗しました、もう一度お試しください');
    }
  } catch (error) {
    // console.error('顔検証中にエラーが発生しました:', error);

    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message);
    } else {
      ElMessage.error('顔検証中にエラーが発生しました');
    }
  } finally {
    // 次の検証を許可するために検証フラグをリセット
    verifyingFace.value = false

    // カメラがまだ開いている場合は検出ループを継続
    if (isCameraOpen.value) {
      detectionInterval = setTimeout(startFaceDetectionLoop, 500)
    }
  }
}

// ダイアログクローズの処理
const handleClose = () => {
  stopCamera()
  verifyingFace.value = false // 検証フラグをリセット
  dialogVisible.value = false
}

// コンポーネントマウント時の初期化
onMounted(async () => {
  await loadModels()
})

// コンポーネントアンマウント時のカメラストリームのクリーンアップ
onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.face-detection-popout {
  padding: 20px;
}

.camera-controls {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.verifying-message {
  margin: 15px 0;
}

.camera-container {
  position: relative;
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  min-height: 300px;
}

.video-wrapper {
  position: relative;
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.camera-video {
  width: 100%;
  display: block;
  border-radius: 12px;
  object-fit: cover;
  /* ビデオがアスペクト比を維持することを保証 */
  transition: transform 0.2s ease;
  /* フリップ効果のスムーズな遷移 */
}

.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  transition: transform 0.2s ease;
  /* フリップ効果のスムーズな遷移 */
}

.button-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.capture-btn {
  background-color: #67c23a;
  /* 緑色 */
  border-color: #67c23a;
  /* 緑色の枠線 */
  color: white;
  /* 白い文字 */
  padding: 12px 20px;
  font-size: 16px;
  font-weight: 500;
}

.capture-btn:hover,
.capture-btn:focus {
  background-color: #5daf34;
  /* ホバー時の暗い緑色 */
  border-color: #5daf34;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.confirm-btn {
  background-color: #67c23a;
  /* 緑色 */
  border-color: #67c23a;
  /* 緑色の枠線 */
  color: white;
  /* 白い文字 */
  padding: 12px 20px;
  font-size: 16px;
  font-weight: 500;
}

.confirm-btn:hover,
.confirm-btn:focus {
  background-color: #5daf34;
  /* ホバー時の暗い緑色 */
  border-color: #5daf34;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  z-index: 10;
}

.loading-overlay p {
  margin-top: 15px;
  font-size: 16px;
}

.placeholder-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  margin-top: 20px;
}

.flip-btn {
  margin-left: 10px;
}
</style>