import { ElMessage } from 'element-plus';
import apiClient from './api';

/**
 * 顔認識関連機能をカプセル化したFace APIユーティリティクラス
 */
export class FaceUtils {
  constructor() {
    this.faceapi = null;
    this.API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
    this.MODELS_PATH = import.meta.env.VITE_FACE_API_MODELS_PATH || '/models';
  }

  /**
   * face-api.jsライブラリとモデルを読み込む
   * @param {Function} onProgress - 進捗コールバック関数、進捗率パーセントを引数に受け取る
   * @returns {Promise<boolean>} 読み込み成功かどうか
   */
  async loadFaceApi(onProgress = null) {
    try {
      if (this.faceapi) {
        return true; // すでに読み込み済み
      }

      // face-api.jsを動的に読み込む
      const faceApiModule = await import('face-api.js');
      this.faceapi = faceApiModule;

      if (onProgress) onProgress(25);

      // ローカルパスからモデルを読み込む
      await this.loadModelsFromPath(this.MODELS_PATH);

      if (onProgress) onProgress(100);

      return true;
    } catch (error) {
      // console.error("face-api.jsまたはモデルの読み込みエラー:", error);

      // ローカル読み込みに失敗した場合、CDNから読み込む
      try {
        await this.loadModelsFromPath('https://raw.githubusercontent.com/justadudewhochacks/face-api.js/master/weights');

        if (onProgress) onProgress(100);

        return true;
      } catch (cdnError) {
        // console.error("CDNからのモデル読み込みエラー:", cdnError);
        ElMessage.error("顔検出モデルの読み込みに失敗しました");
        return false;
      }
    }
  }

  /**
   * 指定されたパスからモデルを読み込む
   * @param {string} path - モデルパス
   */
  async loadModelsFromPath(path) {
    await this.faceapi.nets.tinyFaceDetector.loadFromUri(path);
  }

  /**
   * 顔検出器のオプションを取得
   * @returns {*} TinyFaceDetectorOptionsインスタンス
   */
  getFaceDetectorOptions() {
    return new this.faceapi.TinyFaceDetectorOptions();
  }

  /**
   * 顔検出を実行
   * @param {HTMLVideoElement|HTMLImageElement} input - 入力要素
   * @returns {Promise<Array>} 検出された顔の配列
   */
  async detectFaces(input) {
    if (!this.faceapi) {
      // console.error("face-api.jsが読み込まれていません");
      return [];
    }

    try {
      const detections = await this.faceapi.detectAllFaces(
        input,
        this.getFaceDetectorOptions()
      );
      return detections;
    } catch (error) {
      // console.error("顔検出中にエラーが発生しました:", error);
      return [];
    }
  }

  /**
   * canvasに検出枠を描画
   * @param {HTMLCanvasElement} canvas - キャンバス要素
   * @param {Array} detections - 検出結果
   * @param {number} scaleX - X軸のスケール係数
   * @param {number} scaleY - Y軸のスケール係数
  //  * @param {boolean} isFlipped - 反転するかどうか
   */
  drawDetections(canvas, detections, scaleX = 1, scaleY = 1) {
    if (!canvas || !detections || detections.length === 0) return;

    const ctx = canvas.getContext('2d');

    // キャンバスをクリア
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    detections.forEach(detection => {
      const box = detection.box;

      // 座標をスケーリング
      let x = box.x * scaleX;
      let y = box.y * scaleY;
      const width = box.width * scaleX;
      const height = box.height * scaleY;

      // 反転する場合はX座標を調整
      // if (isFlipped) {
      //   x = canvas.width - x - width;
      // }

      // 楕円形の検出枠を描画
      this.drawEllipseWithGradient(ctx, x + width / 2, y + height / 2, width / 2, height / 2);
    });
  }

  /**
   * グラデーション効果付きの楕円を描画
   * @param {CanvasRenderingContext2D} ctx - キャンバスコンテキスト
   * @param {number} centerX - 中心X座標
   * @param {number} centerY - 中心Y座標
   * @param {number} radiusX - X軸半径
   * @param {number} radiusY - Y軸半径
   */
  drawEllipseWithGradient(ctx, centerX, centerY, radiusX, radiusY) {
    ctx.save();

    // 緑色の枠線を描画
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, Math.PI * 2);
    ctx.stroke();

    // 可視性を向上させるためにL字型の角マーカーを追加
    ctx.beginPath();

    // 左上
    ctx.moveTo(centerX - radiusX, centerY - radiusY + 10);
    ctx.lineTo(centerX - radiusX, centerY - radiusY);
    ctx.lineTo(centerX - radiusX + 10, centerY - radiusY);

    // 右上
    ctx.moveTo(centerX + radiusX - 10, centerY - radiusY);
    ctx.lineTo(centerX + radiusX, centerY - radiusY);
    ctx.lineTo(centerX + radiusX, centerY - radiusY + 10);

    // 左下
    ctx.moveTo(centerX - radiusX, centerY + radiusY - 10);
    ctx.lineTo(centerX - radiusX, centerY + radiusY);
    ctx.lineTo(centerX - radiusX + 10, centerY + radiusY);

    // 右下
    ctx.moveTo(centerX + radiusX - 10, centerY + radiusY);
    ctx.lineTo(centerX + radiusX, centerY + radiusY);
    ctx.lineTo(centerX + radiusX, centerY + radiusY - 10);

    ctx.stroke();

    // 中心に小さな円を描画
    ctx.beginPath();
    ctx.fillStyle = '#00ff00';
    ctx.arc(centerX, centerY, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  /**
   * ビデオから画像をキャプチャ
   * @param {HTMLVideoElement} video - ビデオ要素
   * @param {boolean} flipEnabled - 反転するかどうか
   * @returns {string} 画像データURL
   */
  captureImageFromVideo(video, flipEnabled = false) {
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    const tempCtx = tempCanvas.getContext('2d');

    if (flipEnabled) {
      tempCtx.translate(tempCanvas.width, 0);
      tempCtx.scale(-1, 1);
    }

    tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);

    return tempCanvas.toDataURL('image/jpeg');
  }

  /**
   * 画像データURLをBlobに変換
   * @param {string} imageDataUrl - 画像データURL
   * @param {string} filename - ファイル名
   * @returns {FormData} 画像を含むフォームデータ
   */
  imageToFormData(imageDataUrl, filename = 'image.jpg') {
    const formData = new FormData();

    const base64Data = imageDataUrl.split(',')[1];
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
    formData.append('image', blob, filename);

    return formData;
  }

  /**
   * 検証リクエストを送信
   * @param {FormData} formData - フォームデータ
   * @returns {Promise<any>} 検証レスポンス
   */
  async verifyFace(formData) {
    try {
      const response = await apiClient.post('/api/v1/face/verify', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response.data;
    } catch (error) {
      console.error('顔検証中にエラーが発生しました:', error);
      throw error;
    }
  }
}