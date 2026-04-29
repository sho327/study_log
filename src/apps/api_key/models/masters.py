import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords
# --- コアモジュール ---
from core.models import BaseModel


# APIキースコープマスタ
class M_ApiKeyScope(models.Model):
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
    # コード
    code = models.CharField(
        db_column="code",
        verbose_name="コード",
        db_comment="コード",
        max_length=50,
    )
    # スコープ名
    name = models.CharField(
        db_column="name",
        verbose_name="スコープ名",
        db_comment="スコープ名",
        max_length=100,
    )
    # 詳細説明
    description = models.TextField(
        db_column="description",
        verbose_name="詳細説明",
        db_comment="詳細説明",
        null=True,
        blank=True,
    )

    # テーブル名
    class Meta:
        db_table = "m_api_key_scope"
        db_table_comment = "APIキースコープマスタ"
        verbose_name = "APIキースコープマスタ"
        verbose_name_plural = "APIキースコープマスタ"
        constraints = [
            # 未削除のテーマ間でのみcodeをユニークにする
            UniqueConstraint(
                fields=["code"],
                condition=Q(deleted_at__isnull=True),
                name="unique_m_api_key_scope_code_active",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"