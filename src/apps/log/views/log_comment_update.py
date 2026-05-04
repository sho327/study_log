from datetime import datetime
from django.utils import timezone
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRF_ValidationError

# --- コアモジュール ---
from core.decorators.logging_process_with_sql import logging_process_with_sql
from core.exceptions.exceptions import ApplicationError, ValidationError
from core.utils.date_format import convert_to_site_timezone
from core.utils.log_helpers import log_output_by_msg_id
from core.consts import LOG_METHOD
from core.views import BaseAPIView

# --- ログモジュール ---
from apps.log.serializers.log_comment_update import LogCommentUpdateRequestSerializer
from apps.log.serializers.log_comment_base import LogCommentFullResponseSerializer
from apps.log.services import LogService

KINO_ID = "log-comment-update"


class LogCommentUpdateView(BaseAPIView):
    """
    コメント更新APIクラス
    Create
        Author: Kato Shogo
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    log_service = LogService()

    @logging_process_with_sql
    def post(self, request, log_id, log_comment_id, *args, **kwargs):
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
        """
        try:
            return self.log_comment_update(request, log_id, log_comment_id, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e

    def log_comment_update(self, request, log_id, log_comment_id, *args, **kwargs):
        """
        ログコメント更新処理
        Args:
            request:  HTTPリクエスト
            log_id:   ログID
        """
        date_now: datetime = convert_to_site_timezone(timezone.now())
        # 1. 処理開始ログ出力
        log_output_by_msg_id(
            log_id="MSGI003",
            params=[KINO_ID, str(request.data)],
            logger_name=LOG_METHOD.APPLICATION.value,
        )

        # 2. リクエストデータ検証
        serializer = LogCommentUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 3. サービス実行(コメント登録)
        updated_log_comment = self.log_service.update_log_comment(
            date_now=date_now,
            kino_id=KINO_ID,
            user=request.user,
            log_id=log_id,
            log_comment_id=log_comment_id,
            validated_data=serializer.validated_data,
        )

        # 4. レスポンス作成
        res_serializer = LogCommentFullResponseSerializer(updated_log_comment)
        # get_success_map_responseを使用
        response = self.get_success_map_response(
            data=res_serializer.data,
        )

        # 5. 処理終了ログ出力
        log_output_by_msg_id(
            log_id="MSGI004",
            params=[KINO_ID, str(response.data)],
            logger_name=LOG_METHOD.APPLICATION.value,
        )

        # 6. レスポンス返却
        return response
