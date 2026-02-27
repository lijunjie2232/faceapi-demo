import onnxruntime as ort

from .FaceRecModel import register_model

@register_model("onnx")
@register_model("facenet")
def load_onnx_model(weight, *args, **kwargs):
    """
    ONNXモデルをロードする

    引数:
        onnx_model_path: ONNXモデルファイルのパス

    戻り値:
        ONNXセッションオブジェクト
    """
    session = ort.InferenceSession(weight)
    return session