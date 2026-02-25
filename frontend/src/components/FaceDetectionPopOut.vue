<template>
  <el-dialog v-model="dialogVisible" title="顔検出" width="700px" :before-close="handleClose"
    class="face-detection-popout">
    <div class="camera-controls">
      <el-button type="primary" @click="toggleCamera" :loading="loadingModels" 
        :disabled="loadingModels || capturedImage || !modelsLoaded" class="camera-toggle-btn">
        <el-icon>
          <VideoCamera v-if="isCameraOpen" />
          <Camera v-else />
        </el-icon>
        <span>{{ isCameraOpen ? 'カメラ停止' : 'カメラ開始' }}</span>
      </el-button>

      <el-button :type="flipEnabled ? 'success' : 'default'" @click="toggleFlip" 
        class="flip-btn">
        <el-icon>
          <Switch />
        </el-icon>
        <span>{{ flipEnabled ? '水平反転を有効' : '水平反転を無効' }}</span>
      </el-button>
      
      <!-- 自動キャプチャスイッチ -->
      <el-switch
        v-model="autoCaptureEnabled"
        class="auto-capture-switch"
        active-text="自動キャプチャ"
        inactive-text="手動キャプチャ"
        @change="handleAutoCaptureChange"
      />
    </div>

    <!-- キャプチャされた画像プレビューを表示（利用可能な場合） -->
    <div v-if="capturedImage" class="image-preview-container">
      <h3>確認</h3>
      <img :src="capturedImage" alt="Captured face image" class="captured-image-preview" />
      <p>Please confirm to upload this image</p>
    </div>

    <div v-show="isCameraOpen && !capturedImage" class="camera-container">
      <div class="video-wrapper">
        <video ref="videoRef" class="camera-video" :style="videoStyle" autoplay playsinline></video>
        <canvas ref="canvasRef" class="detection-canvas" :style="canvasStyle"></canvas>
      </div>

      <div v-if="loadingModels" class="loading-overlay">
        <el-progress type="circle" :percentage="modelLoadProgress" :width="150" :stroke-width="10" />
        <p>顔検出モデルを読み込み中...</p>
      </div>
    </div>

    <div v-if="!isCameraOpen && !loadingModels && !capturedImage" class="placeholder-container">
      <el-empty description="Camera is not active" :image-size="150">
        <p>"Start Camera"をクリックして顔検出を開始してください</p>
      </el-empty>
    </div>

    <!-- 状態に応じた異なるボタンアクション -->
    <div class="button-actions">
      <el-button @click="handleClose">{{ capturedImage ? '取り消し' : '閉める' }}</el-button>
      
      <div class="confirmation-buttons" v-if="capturedImage">
        <el-button @click="retakeImage">再開</el-button>
        <el-button type="success" @click="confirmAndSendImage(props._handler)" class="confirm-btn">
          <el-icon>
            <Check />
          </el-icon>
          <span>確認してアップロード</span>
        </el-button>
      </div>
      
      <el-button v-else type="success" @click="captureImage" :disabled="!isCameraOpen || loadingModels" class="capture-btn">
        <el-icon>
          <Camera />
        </el-icon>
        <span>画像をキャプチャする</span>
      </el-button>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { FaceUtils } from '@/utils/face.js'
import { ElSwitch } from 'element-plus'

// propsとemitsを定義
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  _handler: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'faceCaptured'])

// Refs
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const videoRef = ref(null)
const canvasRef = ref(null)
const isCameraOpen = ref(false)
const loadingModels = ref(true)
const modelsLoaded = ref(false) // モデルが読み込まれたかどうかを追跡
const modelLoadProgress = ref(0)
const flipEnabled = ref(!!localStorage.getItem('CameraFlipEnabled')) // localStorageからフリップ状態を読み込み
const capturedImage = ref("") // キャプチャされた画像を保存
const autoCaptureEnabled = ref(!!localStorage.getItem('FaceAutoCaptureEnabled')) // localStorageからの自動キャプチャ設定
let stream = null
let faceUtils = null
let detectionInterval = null

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

// 自動キャプチャ設定変更の処理
const handleAutoCaptureChange = (value) => {
  if (value) {
    localStorage.setItem('FaceAutoCaptureEnabled', 'true')
  } else {
    localStorage.removeItem('FaceAutoCaptureEnabled')
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
        modelsLoaded.value = true // 読み込み完了時にmodelsLoadedをtrueに設定
      }, 500)
    }
  } catch (error) {
    // console.error("face-api.jsの読み込みエラー:", error)
    loadingModels.value = false
    modelsLoaded.value = true // エラー時でもtrueに設定してボタンを有効にする
  }
}

// カメラのオン/オフ切り替え
const toggleCamera = async () => {
  if (isCameraOpen.value) {
    stopCamera()
  } else {
    await startCamera()
  }
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
    alert("カメラにアクセスできませんでした。権限を確認してください。")
  }
}

let ctx = null

// リアルタイム処理のための顔検出ループを開始
const startFaceDetectionLoop = async () => {
  if (!isCameraOpen.value || !videoRef.value || !canvasRef.value || !faceUtils) return

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

    // 自動キャプチャすべきかどうかをチェック
    if (autoCaptureEnabled.value && detections && detections.length > 0) {
      // 検出が安定していることを確実にするためにキャプチャをわずかに遅延
      setTimeout(() => {
        if (autoCaptureEnabled.value && detections && detections.length > 0) {
          captureImage()
        }
      }, 300)
    }

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
    }

    // カメラがまだアクティブな場合は顔検出を継続
    if (isCameraOpen.value) {
      // requestAnimationFrameの代わりにsetTimeoutを使用して頻度を制御
      // これによりイベントの発行頻度が高くなりすぎることを防ぐ
      detectionInterval = setTimeout(startFaceDetectionLoop, 500) // ~2 FPS
    }
  } catch (error) {
    // console.error("顔検出中にエラーが発生しました:", error)
  }
}

// ボタンがクリックされたときに画像をキャプチャする関数
const captureImage = () => {
  if (!videoRef.value || !faceUtils) return
  
  // ユーティリティ関数を使用してビデオから画像をキャプチャ
  const imageDataUrl = faceUtils.captureImageFromVideo(videoRef.value, flipEnabled.value)
  
  // 確認のためにキャプチャされた画像を保存
  capturedImage.value = imageDataUrl
  
  // カメラを停止するがダイアログは開いたままにする
  stopCamera()
}

// 画像を再撮影する関数 - キャプチャされた画像をリセットしてカメラを再起動
const retakeImage = () => {
  capturedImage.value = null
  startCamera()  // カメラを再起動
}

// 画像を確認して送信する関数
const confirmAndSendImage = (_handler) => {
  if (capturedImage.value) {
    if (_handler && typeof _handler === 'function') {
      _handler(capturedImage.value)
    }
    handleClose() // 送信後にダイアログを閉じる
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

// ダイアログクローズの処理
const handleClose = () => {
  stopCamera()
  capturedImage.value = null // キャプチャされた画像をリセット
  dialogVisible.value = false
}

// コンポーネントマウント時の初期化
onMounted(async () => {
  // localStorageから自動キャプチャ設定を読み込み
  autoCaptureEnabled.value = !!localStorage.getItem('FaceAutoCaptureEnabled')
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
  align-items: center;
}

.image-preview-container {
  text-align: center;
  margin: 20px 0;
}

.captured-image-preview {
  width: 100%;
  max-width: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin: 10px auto;
  display: block;
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
  justify-content: space-between;
  margin-top: 20px;
}

.confirmation-buttons {
  display: flex;
  gap: 10px;
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

.auto-capture-switch {
  margin-left: 10px;
}
</style>