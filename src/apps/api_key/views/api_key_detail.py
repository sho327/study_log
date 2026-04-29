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
from apps.api_key.serializers.api_key_base import ApiKeyFullResponseSerializer
from apps.api_key.services import ApiKeyService

KINO_ID = "api-key-detail"

class ApiKeyDetailView(BaseAPIView):
    """
    APIキー詳細取得APIクラス
    Create
        Author: Kato Shogo
    """
    permission_classes = [IsAuthenticated]
    api_key_service = ApiKeyService()

    @logging_process_with_sql
    def get(self, request, artist_id, *args, **kwargs):
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
        """
        try:
            return self.api_key_detail(request, api_key_id, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e
    
    def api_key_detail(self, request, api_key_id, *args, **kwargs):
        """
        APIキー詳細取得処理
        Args:
            request:  HTTPリクエスト
        """
        date_now: datetime = convert_to_site_timezone(timezone.now())
        # 1. 処理開始ログ出力(GETなのでクエリパラメータを出力)
        log_output_by_msg_id(
            log_id="MSGI003", 
            params=[KINO_ID, f"ID: {api_key_id}"], 
            logger_name=LOG_METHOD.APPLICATION.value
        )
        
        # 3. サービス実行(APIキー詳細取得)
        api_key = self.api_key_service.detail_api_key(
            date_now=date_now,
            kino_id=KINO_ID,
            user=request.user,
            api_key_id=api_key_id,
        )

        # 4. レスポンス作成(Full構成を使用)
        res_serializer = ApiKeyFullResponseSerializer(api_key)
        # get_success_map_responseを使用
        response = self.get_success_map_response(
            data=res_serializer.data,
        )

        # 5. 処理終了ログ出力
        log_output_by_msg_id(
            log_id="MSGI004", 
            params=[KINO_ID, f"ID: {api_key_id}"], 
            logger_name=LOG_METHOD.APPLICATION.value
        )

        return response