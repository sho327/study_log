from rest_framework import status

# --- コアモジュール ---
from core.exceptions.exceptions import ApplicationError

class ApiKeyError(ApplicationError):
    """
    APIキー（ApiKey）ドメインにおける全てのビジネス例外の基底クラス。
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message_id = "ERR_APIKEY_000"
    message = "ApiKey Error"
    detail = "APIキー関連の処理中にエラーが発生しました。"

# --------------------------------------------------
# 登録・重複系 (409)
# --------------------------------------------------

class ApiKeyAlreadyExistsError(ApiKeyError):
    """同一ユーザーが既に同じAPIキー名(name)を登録している場合に発生"""
    status_code = status.HTTP_409_CONFLICT
    message_id = "ERR_APIKEY_001"
    message = "ApiKey Already Exists Error"
    detail = "このAPIキーは既に登録されています。"

# --------------------------------------------------
# 参照・整合性系 (404)
# --------------------------------------------------

class ApiKeyNotFoundError(ApiKeyError):
    """指定されたAPIキー発行トランが見つからない場合に発生"""
    status_code = status.HTTP_404_NOT_FOUND
    message_id = "ERR_APIKEY_002"
    message = "ApiKey Not Found Error"
    detail = "指定されたAPIキー情報が見つかりません。"
