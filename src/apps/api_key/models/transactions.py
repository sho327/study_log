import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords
# --- コアモジュール ---
from core.models import BaseModel

# APIキー発行トラン
class T_ApiKey(BaseModel):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID(URLに使用される可能性もあるため、予測できないUUIDで保持する)
    id = models.UUIDField(
        db_column="id",
        verbose_name="ID",
        db_comment="ID",
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    # ユーザマスタ(削除/物理削除の場合はCASCADE)
    user = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="user_t_api_key_set",
    )
    # クライアントキー
    client_key = models.CharField(
        db_column="client_key",
        verbose_name="クライアントキー",
        db_comment="クライアントキー",
        max_length=64,
    )
    # ハッシュ化シークレットキー
    hashed_secret = models.CharField(
        db_column="hashed_secret",
        verbose_name="ハッシュ化シークレットキー",
        db_comment="ハッシュ化シークレットキー",
        max_length=128,
    )
    # 有効フラグ
    is_active = models.BooleanField(
        db_column="is_active",
        verbose_name="有効フラグ",
        db_comment="有効フラグ",
        db_default=True,
        default=True,
    )
    # トークン有効期限
    expired_at = models.DateTimeField(
        db_column="expired_at",
        verbose_name="トークン有効期限",
        db_comment="トークン有効期限",
    )
    # 最終使用日時
    last_used_at = models.DateTimeField(
        db_column="last_used_at",
        verbose_name="最終使用日時",
        db_comment="最終使用日時",
        null=True,
        blank=True,
    )

    # 履歴管理不要: django-simple-historyを使用しない
    # history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "t_api_key"
        db_table_comment = "APIキー発行トラン"
        verbose_name = "APIキー発行トラン"
        verbose_name_plural = "APIキー発行トラン"
        constraints = [
            # 未削除のトークン間でのみclient_keyをユニークにする
            UniqueConstraint(
                fields=["client_key"],
                condition=Q(deleted_at__isnull=True),
                name="unique_t_api_key_client_key_active",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.client_key[:10]}..."
