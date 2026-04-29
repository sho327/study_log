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

# --- APIキーモジュール ---
from apps.api_key.serializers.api_key_update import ApiKeyUpdateRequestSerializer
from apps.api_key.serializers.api_key_base import ApiKeyFullResponseSerializer
from apps.api_key.services import ApiKeyService

KINO_ID = "api-key-update"

class ApiKeyUpdateView(BaseAPIView):
    """
    APIキー更新APIクラス
    Create
        Author: Kato Shogo
    """
    permission_classes = [IsAuthenticated]
    api_key_service = ApiKeyService()

    @logging_process_with_sql
    def put(self, request, api_key_id, *args, **kwargs):
        """
        PUTリクエストを受け付ける。
        Method: PUT
        Args:
            request:  HTTPリクエスト
            *args:    引数
            **kwargs: キーワード引数
        Returns:
            Response: HTTPレスポンス
        Raises:
            InternalServerError: 想定外エラー
        """
        try:
            return self.api_key_update(request, api_key_id, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e
    
    @logging_process_with_sql
    def patch(self, request, api_key_id, *args, **kwargs):
        """
        PATCHリクエストを受け付ける。
        Method: PATCH
        Args:
            request:  HTTPリクエスト
            *args:    引数
            **kwargs: キーワード引数
        Returns:
            Response: HTTPレスポンス
        Raises:
            InternalServerError: 想定外エラー
        """
        try:
            return self.api_key_update(request, api_key_id, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e
    
    def api_key_update(self, request, api_key_id, *args, **kwargs):
        """
        APIキー更新処理
        Args:
            request:  HTTPリクエスト
        """
        date_now: datetime = convert_to_site_timezone(timezone.now())
        # 1. 処理開始ログ出力
        log_output_by_msg_id(
            log_id="MSGI003", 
            params=[KINO_ID, str(request.data)], 
            logger_name=LOG_METHOD.APPLICATION.value
        )

        # 2. リクエストデータ検証
        serializer = ApiKeyUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 3. サービス実行(APIキー更新)
        update_api_key = self.api_key_service.update_api_key(
            date_now=date_now,
            kino_id=KINO_ID,
            user=request.user,
            api_key_id=api_key_id,
            validated_data=serializer.validated_data,
        )

        # 4. レスポンス作成(Full構成を使用)
        res_serializer = ApiKeyFullResponseSerializer(update_api_key)
        # get_success_map_responseを使用
        response = self.get_success_map_response(
            data=res_serializer.data,
        )

        # 5. 処理終了ログ出力
        log_output_by_msg_id(
            log_id="MSGI004", 
            params=[KINO_ID, str(response.data)], 
            logger_name=LOG_METHOD.APPLICATION.value
        )
        
        return response