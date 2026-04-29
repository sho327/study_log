import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords
# --- コアモジュール ---
from core.models import BaseModel


# APIキースコープリレーション
class R_ApiKeyScope(BaseModel):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与
    # APIキー発行トラン(削除/物理削除の場合はCASCADE)
    api_key = models.ForeignKey(
        "api_key.T_ApiKey",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="api_key",
        verbose_name="APIキー発行トラン",
        db_comment="APIキー発行トラン",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="log_r_api_key_scope_set",
    )
    # APIキースコープマスタ(削除/物理削除の場合はCASCADE)
    api_key_scope = models.ForeignKey(
        "api_key.M_ApiKeyScope",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="api_key_scope_id",
        verbose_name="APIキースコープマスタ",
        db_comment="APIキースコープマスタ",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="api_key_scope_r_api_key_scope_set",
    )

    # django-simple-historyを使用
    # history = HistoricalRecords()

    class Meta:
        db_table = "r_api_key_scope"
        db_table_comment = "APIキースコープリレーション"
        verbose_name = "APIキースコープリレーション"
        verbose_name_plural = "APIキースコープリレーション"
        constraints = [
            UniqueConstraint(
                fields=["api_key", "api_key_scope"],
                condition=Q(deleted_at__isnull=True),
                name="unique_r_api_key_scope_api_key_api_key_scope_active",
            ),
        ]
