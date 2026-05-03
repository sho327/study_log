from rest_framework import status

# --- コアモジュール ---
from core.exceptions.exceptions import ApplicationError

class LogError(ApplicationError):
    """
    ログ(Log)ドメインにおける全てのビジネス例外の基底クラス。
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message_id = "ERR_LOG_000"
    message = "Log Error"
    detail = "ログ関連の処理中にエラーが発生しました。"

# --------------------------------------------------
# 登録・重複系 (409)
# --------------------------------------------------

# --------------------------------------------------
# 参照・整合性系 (404)
# --------------------------------------------------

class LogNotFoundError(LogError):
    """指定されたログトランが見つからない場合に発生"""
    status_code = status.HTTP_404_NOT_FOUND
    message_id = "ERR_LOG_001"
    message = "Log Not Found Error"
    detail = "指定されたログ情報が見つかりません。"

class LogCommentNotFoundError(LogError):
    """指定されたログコメントトランが見つからない場合に発生"""
    status_code = status.HTTP_404_NOT_FOUND
    message_id = "ERR_LOG_002"
    message = "Log Comment Not Found Error"
    detail = "指定されたロクコメンド情報が見つかりません。"

class LogReactionConflictError(LogError):
    """指定されたログリアクションが既に追加されている場合に発生"""
    status_code = status.HTTP_409_CONFLICT
    message_id = "ERR_LOG_003"
    message = "Log Reaction Conflict Error"
    detail = "指定されたログリアクションは既に追加されています。"

class LogCommentReactionConflictError(LogError):
    """指定されたロクコメントリアクションが既に追加されている場合に発生"""
    status_code = status.HTTP_409_CONFLICT
    message_id = "ERR_LOG_004"
    message = "Log Comment Reaction Conflict Error"
    detail = "指定されたロクコメントリアクションは既に追加されています。"
