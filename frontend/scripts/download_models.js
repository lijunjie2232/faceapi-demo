const fs = require('fs');
const https = require('https');
const path = require('path');

// モデルを保存するディレクトリ
const modelsDir = path.join(__dirname, 'public', 'models');
if (!fs.existsSync(modelsDir)) {
  fs.mkdirSync(modelsDir, { recursive: true });
}

// ダウンロードするモデルのリスト
const modelFiles = [
  'tiny_face_detector_model-weights_manifest.json',
  'tiny_face_detector_model-shard1',
  // 'face_landmark_68_model-weights_manifest.json',
  // 'face_landmark_68_model-shard1',
  // 'face_landmark_68_tiny_model-weights_manifest.json',
  // 'face_landmark_68_tiny_model-shard1',
  // 'face_recognition_model-weights_manifest.json',
  // 'face_recognition_model-shard1',
  // 'face_recognition_model-shard2',
  // 'face_recognition_model-shard3',
  // 'age_gender_model-weights_manifest.json',
  // 'age_gender_model-shard1',
  // 'age_gender_model-shard2',
  // 'face_expression_model-weights_manifest.json',
  // 'face_expression_model-shard1',
];

// モデルのベースURL
const baseUrl = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/';
console.log('face-api.jsモデルをダウンロード中...');

modelFiles.forEach((filename, index) => {
  const url = baseUrl + filename;
  const filePath = path.join(modelsDir, filename);

  console.log(`${filename}をダウンロード中...`);

  const file = fs.createWriteStream(filePath);

  https.get(url, (response) => {
    if (response.statusCode === 200) {
      response.pipe(file);
      file.on('finish', () => {
        file.close();
        console.log(`${filename}が正常にダウンロードされました。`);
        
        // すべてのファイルがダウンロードされたかどうかを確認
        if (index === modelFiles.length - 1) {
          console.log('すべてのモデルが正常にダウンロードされました！');
        }
      });
    } else {
      console.error(`${filename}のダウンロードに失敗しました。ステータスコード: ${response.statusCode}`);
    }
  }).on('error', (err) => {
    console.error(`${filename}のダウンロードエラー:`, err.message);
    file.close();
    fs.unlink(filePath, () => {}); // エラーがある場合はファイルを削除
  });
});