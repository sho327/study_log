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


KINO_ID = "user-unfollow"

class UserUnfollowView(BaseAPIView):
    """
    フォロー解除APIクラス
    Create
        Author: Kato Shogo
    """
    permission_classes = [IsAuthenticated]
    account_service = AccountService()

    @logging_process_with_sql
    def post(self, request, target_user_id, *args, **kwargs):
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
            return self.user_unfollow(request, target_user_id, *args, **kwargs)
        except ApplicationError:
            # ApplicationError関連はカスタムエラー処理が設定されている為そのまま親へスローする
            raise
        except DRF_ValidationError as e:
            # DRFバリデーションエラーは専用エラーに差し替える
            raise ValidationError() from e
        except Exception as e:
            # その他想定外エラーの場合もAPIエラーとする
            raise ApplicationError() from e
    
    def user_unfollow(self, request, target_user_id, *args, **kwargs):
        """
        フォロー解除処理
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
        # 2. フォロー解除(サービス実行)
        self.account_service.user_unfollow(
            date_now, 
            KINO_ID, 
            request.user.id,
            target_user_id,
        )
        # 3. レスポンス作成
        # 空であっても「このAPIが何を返すか」がViewの最後を見れば一目でわかるようにする
        # data=Noneまたは空辞書を渡すことで、executeAtだけが入ったレスポンスとなる
        response = self.get_success_map_response(data={})
        # 4. 処理終了ログ出力(アプリケーションログ)
        log_output_by_msg_id(log_id="MSGI004", params=[KINO_ID, ""], logger_name=LOG_METHOD.APPLICATION.value)
        # 5. レスポンス返却
        return response
