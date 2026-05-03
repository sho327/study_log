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
from apps.account.serializers.initial_setting import InitialSettingRequestSerializer
from apps.account.serializers.account_base import ProfileFullResponseSerializer

KINO_ID = "initial-setting"

class InitialSettingView(BaseAPIView):
    """
    初期設定APIクラス
    Create
        Author: Kato Shogo
    """
    permission_classes = [IsAuthenticated]
    account_service = AccountService()

    @logging_process_with_sql
    def post(self, request, *args, **kwargs):
        """
        POSTリクエストを受け付ける。
        Method: POST
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
            return self.initial_setting(request, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e
    
    def initial_setting(self, request, *args, **kwargs):
        """
        初期設定処理
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
        # 2. リクエストデータ検証
        initial_setting_serializer = InitialSettingRequestSerializer(data=request.data)
        initial_setting_serializer.is_valid(raise_exception=True)
        # 3. 初期設定(サービス実行)
        result = self.account_service.initial_setting(
            date_now=date_now,
            kino_id=KINO_ID,
            user=request.user,
            **initial_setting_serializer.validated_data
        )
        # 4. レスポンス作成
        # Serializerでフィールドを直接指定しているため、
        # 結果のオブジェクトをそのまま渡すだけで正しくJSONに変換される。
        res_serializer = ProfileFullResponseSerializer(result)
        response = self.get_success_map_response(res_serializer.data)
        # 5. 処理終了ログ出力(アプリケーションログ)
        log_output_by_msg_id(log_id="MSGI004", params=[KINO_ID, str(response.data)], logger_name=LOG_METHOD.APPLICATION.value)
        # 6. レスポンス返却
        return response
