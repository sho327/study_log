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

# --- APIキーモジュール ---
from apps.api_key.serializers.api_key_list import ApiKeyListRequestSerializer
from apps.api_key.serializers.api_key_base import ApiKeyMiniResponseSerializer
from apps.api_key.services import ApiKeyService

KINO_ID = "api-key-list"

class ApiKeyListView(BaseAPIView):
    """
    APIキー一覧取得APIクラス
    Create
        Author: Kato Shogo
    """
    permission_classes = [IsAuthenticated]
    api_key_service = ApiKeyService()

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
        """
        try:
            return self.api_key_list(request, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e
    
    def api_key_list(self, request, *args, **kwargs):
        """
        APIキー一覧取得処理
        Args:
            request:  HTTPリクエスト
        """
        date_now: datetime = convert_to_site_timezone(timezone.now())
        # 1. 処理開始ログ出力(GETなのでクエリパラメータを出力)
        log_output_by_msg_id(
            log_id="MSGI003", 
            params=[KINO_ID, str(request.query_params)], 
            logger_name=LOG_METHOD.APPLICATION.value
        )

        # 2. リクエストデータ検証
        # GETなのでrequest.query_paramsを渡す
        serializer = ApiKeyListRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # リクエストデータ変数化
        per_page = serializer.validated_data.get("per_page")
        page = serializer.validated_data.get("page")
        
        # 3. サービス実行(一覧データ取得)
        # Service側で select_related('spotify_image') 等のN+1対策がなされたQuerySetを取得
        queryset = self.api_key_service.list_api_key(
            date_now=date_now,
            kino_id=KINO_ID,
            user=request.user,
        )

        # 4. ページング処理
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        # 5. レスポンス作成(Mini構成を使用)
        # many=Trueでリスト形式としてシリアライズ
        res_serializer = ApiKeyMiniResponseSerializer(page_obj.object_list, many=True)
        # get_success_list_response を使用し、results/countを含む共通フォーマットを生成
        response = self.get_success_list_response(
            data=res_serializer.data,
            count=paginator.count
        )

        # 6. 処理終了ログ出力
        log_output_by_msg_id(
            log_id="MSGI004", 
            params=[KINO_ID, f"page: {page}, count: {paginator.count}"], 
            logger_name=LOG_METHOD.APPLICATION.value
        )
        
        return response