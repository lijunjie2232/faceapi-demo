import base64
from pathlib import PosixPath

import cv2
import numpy as np
from functools import partial

from ..face_rec import _MODEL_
from ..core import _CONFIG_



class FaceDetector:
    """
    OpenCV Haarカスケードに基づく顔検出器
    """

    def __init__(self):
        # cv2.dataが利用できない場合の処理
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        except AttributeError:
            # cv2.dataが利用できない場合のフォールバック
            cascade_path = "haarcascade_frontalface_default.xml"

        # pylint: disable=no-member
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        # pylint: enable=no-member

    def detect_from_array(self, image_array):
        """
        numpy配列画像から顔を検出
        """
        gray_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )
        # 切り取られた顔画像を返す
        return [image_array[y : y + h, x : x + w] for (x, y, w, h) in faces]


def detect_face(image):
    """
    OpenCV Haarカスケードを使用して画像内の顔を検出。

    引数:
        image: ファイルパス（文字列）または画像を表すnumpy配列のいずれか

    戻り値:
        検出された顔を表すnumpy配列のリスト、または顔が見つからない場合は空リスト
    """
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # 異なる入力タイプを処理
    if isinstance(image, str):
        # 画像がファイルパスの場合
        image = cv2.imread(image, cv2.COLOR_BGR2RGB)
    elif isinstance(image, np.ndarray):
        # 画像が既にnumpy配列の場合
        pass
    else:
        raise ValueError("画像はファイルパス文字列またはnumpy配列である必要があります")

    if image is None:
        return []

    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(
        gray_image,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
    )

    # 切り取られた顔画像を返す
    return [image[y : y + h, x : x + w] for (x, y, w, h) in faces]


def image_to_base64(image):
    """
    画像をbase64エンコードされた文字列に変換

    引数:
        image: ファイルパス（文字列）、numpy配列、または画像を表すバイトのいずれか

    戻り値:
        画像のBase64エンコードされた文字列表現
    """
    if isinstance(image, str):
        # ファイルから画像を読み込み
        image_data = cv2.imread(image)
        _, buffer = cv2.imencode(".jpg", image_data)
        image_bytes = buffer.tobytes()
    elif isinstance(image, np.ndarray):
        # numpy配列をバイトに変換
        _, buffer = cv2.imencode(".jpg", image)
        image_bytes = buffer.tobytes()
    elif isinstance(image, bytes):
        # 画像が既にバイトの場合
        image_bytes = image
    else:
        raise ValueError(
            "画像はファイルパス文字列、numpy配列、またはバイトである必要があります"
        )

    # バイトをbase64にエンコード
    base64_string = base64.b64encode(image_bytes).decode("utf-8")

    return base64_string


def base64_to_image(base64_string: str):
    """
    base64エンコードされた文字列を画像（numpy配列）に変換

    引数:
        base64_string: 画像を表すBase64エンコードされた文字列

    戻り値:
        デコードされた画像を表すnumpy配列
    """
    # base64文字列をバイトにデコード
    image_bytes = base64.b64decode(base64_string.encode("utf-8"))

    # バイトをnumpy配列に変換
    nparr = np.frombuffer(image_bytes, np.uint8)

    # numpy配列を画像にデコード
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    return image


def preprocess_image(image):
    """
    画像を前処理する（ONNXモデル用）

    引数:
        image: 入力画像（numpy配列）

    戻り値:
        前処理された画像テンソル
    """
    img = cv2.resize(image, (112, 112))
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0).astype(np.float32)
    img = img / 255.0
    img = (img - 0.5) / 0.5
    return img

def inference_onnx(session, img, to_array=True):
    """
    ONNXモデルを使用して推論を行う

    引数:
        session: ONNXセッションオブジェクト
        img: 入力画像（ファイルパス、numpy配列、またはNone）
        to_array: 出力をnumpy配列として返すかどうか

    戻り値:
        特徴ベクトル（numpy配列またはテンソル）
    """
    if img is None:
        img = np.random.randint(0, 255, size=(112, 112, 3), dtype=np.uint8)
    elif isinstance(img, str) or isinstance(img, PosixPath):
        img = cv2.imread(img, cv2.COLOR_BGR2RGB)

    # 画像を前処理
    input_tensor = preprocess_image(img)

    # ONNXモデルで推論
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    result = session.run([output_name], {input_name: input_tensor})

    # 結果を取得
    feat = result[0]

    if to_array:
        feat = np.array(feat)

    return feat.reshape(-1, _CONFIG_.MODEL_EMB_DIM)


inference = partial(inference_onnx, _MODEL_)