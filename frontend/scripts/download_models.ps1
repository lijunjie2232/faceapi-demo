# Create models directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "public/models"

Write-Host "Downloading face-api.js models..."

# Array of model files to download
$models = @(
    # @{ Path = "public/models/face_landmark_68_model-weights_manifest.json"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-weights_manifest.json" },
    # @{ Path = "public/models/face_landmark_68_model-shard1"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-shard1" },
    # @{ Path = "public/models/face_landmark_68_tiny_model-weights_manifest.json"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_tiny_model-weights_manifest.json" },
    # @{ Path = "public/models/face_landmark_68_tiny_model-shard1"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_tiny_model-shard1" },
    # @{ Path = "public/models/face_recognition_model-weights_manifest.json"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-weights_manifest.json" },
    # @{ Path = "public/models/face_recognition_model-shard1"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-shard1" },
    # @{ Path = "public/models/face_recognition_model-shard2"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-shard2" },
    @{ Path = "public/models/tiny_face_detector_model-weights_manifest.json"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/tiny_face_detector_model-weights_manifest.json" },
    @{ Path = "public/models/tiny_face_detector_model-shard1"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/tiny_face_detector_model-shard1" },
backend    # @{ Path = "public/models/face_expression_model-weights_manifest.json"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_expression_model-weights_manifest.json" },
    # @{ Path = "public/models/face_expression_model-shard1"; Url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_expression_model-shard1" }
)

# Download each model file
foreach ($model in $models) {
    Write-Host "Downloading $($model.Path)..."
    try {
        Invoke-WebRequest -Uri $model.Url -OutFile $model.Path
        Write-Host "Successfully downloaded $($model.Path)" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download $($model.Path): $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "Download completed!" -ForegroundColor Yellow