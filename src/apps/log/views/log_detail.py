from datetime import datetime
from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRF_ValidationError

# --- コアモジュール ---
from core.decorators.logging_process_with_sql import logging_process_with_sql
from core.consts import LOG_METHOD
from core.utils.log_helpers import log_output_by_msg_id
from core.utils.date_format import convert_to_site_timezone
from core.exceptions.exceptions import ApplicationError, ValidationError
from core.views import BaseAPIView

# --- ログモジュール ---
from apps.log.serializers.log_base import LogFullResponseSerializer
from apps.log.services import LogService

KINO_ID = "log-detail"

class LogDetailView(BaseAPIView):
    """
    ログ詳細取得APIクラス
    Create
        Author: Kato Shogo
    """
    permission_classes = [IsAuthenticated]
    log_service = LogService()

    @logging_process_with_sql
    def get(self, request, log_id: str, *args, **kwargs):
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
            return self.log_detail(request, log_id, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e
    
    def log_detail(self, request, log_id: str, *args, **kwargs):
        """
        ログ詳細取得処理
        Args:
            request:  HTTPリクエスト
        """
        date_now: datetime = convert_to_site_timezone(timezone.now())
        # 1. 処理開始ログ出力(GETなのでクエリパラメータを出力)
        log_output_by_msg_id(
            log_id="MSGI003", 
            params=[KINO_ID, ""], 
            logger_name=LOG_METHOD.APPLICATION.value
        )
        
        # 2. サービス実行(一覧データ取得)
        # Service側で select_related('spotify_image') 等のN+1対策がなされたQuerySetを取得
        log = self.log_service.detail_log(
            date_now=date_now,
            kino_id=KINO_ID,
            user=request.user,
            log_id=log_id,
        )

        # 3. レスポンス作成(Full構成を使用)
        res_serializer = LogFullResponseSerializer(log)
        # get_success_map_response を使用し、results/countを含む共通フォーマットを生成
        response = self.get_success_map_response(
            data=res_serializer.data
        )

        # 4. 処理終了ログ出力
        log_output_by_msg_id(
            log_id="MSGI004", 
            params=[KINO_ID, str(response.data)], 
            logger_name=LOG_METHOD.APPLICATION.value
        )
        
        return response
    