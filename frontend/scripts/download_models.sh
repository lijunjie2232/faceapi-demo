#!/bin/bash

# Create models directory if it doesn't exist
mkdir -p public/models

echo "Downloading face-api.js models..."

# Download the model files
# wget -O public/models/face_landmark_68_model-weights_manifest.json https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-weights_manifest.json
# wget -O public/models/face_landmark_68_model-shard1 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-shard1
# wget -O public/models/face_landmark_68_model-shard2 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-shard2
# wget -O public/models/face_landmark_68_tiny_model-weights_manifest.json https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_tiny_model-weights_manifest.json
# wget -O public/models/face_landmark_68_tiny_model-shard1 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_tiny_model-shard1
# wget -O public/models/face_landmark_68_tiny_model-shard2 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_tiny_model-shard2
# wget -O public/models/face_recognition_model-weights_manifest.json https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-weights_manifest.json
# wget -O public/models/face_recognition_model-shard1 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-shard1
# wget -O public/models/face_recognition_model-shard2 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-shard2
# wget -O public/models/face_recognition_model-shard3 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-shard3
wget -O public/models/tiny_face_detector_model-weights_manifest.json https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/tiny_face_detector_model-weights_manifest.json
wget -O public/models/tiny_face_detector_model-shard1 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/tiny_face_detector_model-shard1
# wget -O public/models/tiny_face_detector_model-shard2 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/tiny_face_detector_model-shard2
# wget -O public/models/face_expression_model-weights_manifest.json https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_expression_model-weights_manifest.json
# wget -O public/models/face_expression_model-shard1 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_expression_model-shard1
# wget -O public/models/face_expression_model-shard2 https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_expression_model-shard2

echo "Download completed!"