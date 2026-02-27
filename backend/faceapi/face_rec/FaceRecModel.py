class FaceRecModel:
    """
    モデルクラスを管理し、登録されたモデルのインスタンスを提供するレジストリ。
    """

    _models = {}

    @classmethod
    def register(cls, name):
        """
        指定された名前でモデルクラスを登録するデコレータ。

        引数:
            name (str): モデルを登録する名前

        戻り値:
            function: デコレータ関数
        """

        def decorator(model_class):
            cls._models[name] = model_class
            model_class.name = name
            return model_class

        return decorator

    @classmethod
    def get_model(cls, name, *args, **kwargs):
        """
        登録されたモデルのインスタンスを取得。

        引数:
            name (str): インスタンス化するモデルの名前
            *args: モデルコンストラクタに渡す引数
            **kwargs: モデルコンストラクタに渡すキーワード引数

        戻り値:
            object: 要求されたモデルのインスタンス

        例外:
            ValueError: モデル名が登録されていない場合
        """
        if name not in cls._models:
            raise ValueError(f"モデル '{name}' は登録されていません。")

        model_class = cls._models[name]
        return model_class(*args, **kwargs)

    @classmethod
    def list_models(cls):
        """
        登録されたすべてのモデル名をリスト表示。

        戻り値:
            list: 登録されたモデル名のリスト
        """
        return list(cls._models.keys())

    @classmethod
    def has_model(cls, name):
        """
        モデルが登録されているか確認。

        引数:
            name (str): 確認するモデルの名前

        戻り値:
            bool: モデルが登録されている場合はTrue、それ以外はFalse
        """
        return name in cls._models


# 外部使用のための便利な関数を作成
register_model = FaceRecModel.register
get_model = FaceRecModel.get_model
list_models = FaceRecModel.list_models
has_model = FaceRecModel.has_model
