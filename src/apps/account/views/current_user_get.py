from datetime import datetime
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRF_ValidationError

# --- コアモジュール ---
from core.decorators.logging_process_with_sql import logging_process_with_sql
from core.consts import LOG_METHOD
from core.utils.log_helpers import log_output_by_msg_id
from core.utils.date_format import convert_to_site_timezone
from core.exceptions.exceptions import ApplicationError, ValidationError
from core.views import BaseAPIView

# --- アカウントモジュール ---
from apps.account.services import AccountService
from apps.account.serializers.account_base import UserMeResponseSerializer

KINO_ID = "current-user-get"

class CurrentUserGetView(BaseAPIView):
    """
    現在のユーザー情報を取得するAPIクラス
    Create
        Author: Kato Shogo
    """
    permission_classes = [IsAuthenticated]
    account_service = AccountService()

    @logging_process_with_sql
    def get(self, request, *args, **kwargs):
        """
        GETリクエストを受け付ける。
        Method: GET
        Args:
            request:  HTTPリクエスト
            *args:    引数
            **kwargs: キーワード引数
        Returns:
            Response: HTTPレスポンス
        Raises:
            InternalServerError: 想定外エラー
        Create
            Author: Kato Shogo
        """
        try:
            return self.current_user_get(request, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e
    
    def current_user_get(self, request, *args, **kwargs):
        """
        現在のユーザー情報を取得する
        Args:
            request:  HTTPリクエスト
            *args:    引数
            **kwargs: キーワード引数
        Create
            Author: Kato Shogo
        """
        date_now: datetime = convert_to_site_timezone(timezone.now())
        # 1. 処理開始ログ出力(アプリケーションログ)
        log_output_by_msg_id(log_id="MSGI003", params=[KINO_ID, ""], logger_name=LOG_METHOD.APPLICATION.value)
        # 2. サービス実行(現在のユーザー情報を取得)
        result: M_User = self.account_service.current_user_get(
            date_now=date_now,
            kino_id=KINO_ID,
            user=request.user
        )
        # 3. レスポンス作成
        # Serializerでフィールドを直接指定しているため、
        # 結果のオブジェクトをそのまま渡すだけで正しくJSONに変換される。
        res_serializer = UserMeResponseSerializer(result)
        response = self.get_success_map_response(res_serializer.data)
        # 4. 処理終了ログ出力(アプリケーションログ)
        log_output_by_msg_id(log_id="MSGI004", params=[KINO_ID, str(response.data)], logger_name=LOG_METHOD.APPLICATION.value)
        # 5. レスポンス返却
        return response
