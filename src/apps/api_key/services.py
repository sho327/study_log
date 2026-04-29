import secrets
from datetime import datetime, timedelta
from typing import Tuple

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone

# --- アカウントモジュール ---
from apps.account.models import M_User

# --- APIキーモジュール ---
from apps.api_key.exceptions import ApiKeyAlreadyExistsError, ApiKeyNotFoundError
from apps.api_key.models import M_ApiKeyScope, R_ApiKeyScope, T_ApiKey

# --- 共通モジュール ---
from core.consts import LOG_METHOD
from core.utils.log_helpers import log_output_by_msg_id

class ApiKeyService:
    """
    APIキーの登録/更新/管理を行うサービスクラス
    """

    # ------------------------------------------------------------------
    # 一覧取得系サービス
    # ------------------------------------------------------------------
    # APIキー一覧取得
    def list_api_key(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
    ):
        """
        ユーザーに紐付く有効なAPIキー一覧を取得する
        """
        # 自分のデータかつ未削除のものを取得
        return T_ApiKey.objects.filter(
            user=user,
            deleted_at__isnull=True
        ).order_by("-created_at")

    # ------------------------------------------------------------------
    # 詳細取得系サービス
    # ------------------------------------------------------------------
    # APIキー詳細取得
    def get_api_key(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        api_key_id: str,
    ) -> T_ApiKey:
        """
        APIキーの詳細を取得する
        """
        try:
            return T_ApiKey.objects.get(
                id=api_key_id,
                user=user,
                deleted_at__isnull=True
            )
        except T_ApiKey.DoesNotExist as e:
            log_output_by_msg_id(
                log_id="MSGE001",
                params=[f"APIキーが見つかりませんでした。: {str(e)}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            raise ApiKeyNotFoundError()

    # ------------------------------------------------------------------
    # 登録系サービス
    # ------------------------------------------------------------------
    # APIキー登録
    def create_api_key(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        validated_data: dict,
    ) -> Tuple[T_ApiKey, str]:
        """
        APIキーを新規発行する
        戻り値: (作成されたT_ApiKeyインスタンス, 生のシークレットキー)
        """
        # 1. 重複チェック(同一ユーザー内で同じ名前のキーがないか)
        if T_ApiKey.objects.filter(
            user=user,
            name=validated_data["name"],
            deleted_at__isnull=True
        ).exists():
            log_output_by_msg_id(
                log_id="MSGE001",
                params=["APIキー名が既に登録されています。"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            raise ApiKeyAlreadyExistsError()

        # 2. キーの生成
        # client_key: 32文字のランダム文字列
        # secret_key: 32文字のランダム文字列
        client_key = secrets.token_hex(16)
        raw_secret = secrets.token_hex(16)
        expired_at = timezone.now() + timedelta(days=validated_data["duration_days"])
        
        # 3. APIキー本体の作成
        api_key = T_ApiKey.objects.create(
            user=user,
            name=validated_data["name"],
            description=validated_data.get("description"),
            client_key=client_key,
            hashed_secret=make_password(raw_secret), # パスワードと同じ仕組みでハッシュ化
            expired_at=expired_at,
            is_active=True,
            revoked_reason=None,
            revoked_detail=None,
            created_by=user,
            created_method=kino_id,
            updated_by=user,
            updated_method=kino_id,
        )

        # 4. スコープの紐付け
        scope_ids = validated_data.get("scope_ids", [])
        if scope_ids:
            scope_links = [
                R_ApiKeyScope(
                    api_key=api_key,
                    api_key_scope=scope,
                    created_by=user,
                    created_method=kino_id,
                    updated_by=user,
                    updated_method=kino_id,
                )
                for scope in scope_ids
            ]
            R_ApiKeyScope.objects.bulk_create(scope_links)

        return api_key, raw_secret

    # ------------------------------------------------------------------
    # 更新系サービス
    # ------------------------------------------------------------------
    # アーティスト更新
    def update_artist(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        api_key_id: str,
        validated_data: dict,
    ) -> T_ApiKey:
        """
        APIキー情報を更新する
        """
        # 1. 対象の取得
        api_key = self.get_api_key(user, api_key_id)

        # 2. 基本情報の更新
        if "name" in validated_data:
            # 名前を変更する場合の重複チェック
            if T_ApiKey.objects.filter(
                user=user,
                name=validated_data["name"],
                deleted_at__isnull=True
            ).exclude(id=api_key_id).exists():
                raise ApiKeyAlreadyExistsError()
            api_key.name = validated_data["name"]

        if "description" in validated_data:
            api_key.description = validated_data["description"]
        
        if "is_active" in validated_data:
            api_key.is_active = validated_data["is_active"]
            # 無効化される場合は理由などを設定
            if not api_key.is_active:
                api_key.revoked_reason = validated_data["revoked_reason"]
                api_key.revoked_detail = validated_data["revoked_detail"]
            # 有効化される場合は理由などをリセット
            else:
                api_key.revoked_reason = None
                api_key.revoked_detail = None
        
        if "duration_days" in validated_data:
            api_key.expired_at = timezone.now() + timedelta(days=validated_data["duration_days"])

        api_key.updated_by = user
        api_key.updated_method = kino_id
        api_key.save()

        # 3. スコープの更新(洗替方式)
        if "scope_ids" in validated_data:
            # 既存の紐付けを物理削除
            R_ApiKeyScope.objects.filter(api_key=api_key).delete()

            # 新しいスコープを登録
            scope_ids = validated_data["scope_ids"]
            if scope_ids:
                scope_links = [
                    R_ApiKeyScope(
                        api_key=api_key,
                        api_key_scope=scope,
                        created_by=user,
                        created_method=kino_id,
                        updated_by=user,
                        updated_method=kino_id,
                    )
                    for scope in scope_ids
                ]
                R_ApiKeyScope.objects.bulk_create(scope_links)

        return api_key

    # ------------------------------------------------------------------
    # 削除系サービス
    # ------------------------------------------------------------------
    # アーティスト削除
    def delete_artist(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        api_key_id: str,
    ):
        """
        APIキーを論理削除する
        """
        # 1. 対象の取得
        api_key = self.get_api_key(user, api_key_id)

        # 2. 本体を論理削除
        api_key.updated_by = user
        api_key.updated_method = kino_id
        api_key.deleted_at = date_now
        api_key.save()

        # 3. 紐付いているスコープを物理削除 (中間テーブル)
        R_ApiKeyScope.objects.filter(api_key=api_key).delete()

