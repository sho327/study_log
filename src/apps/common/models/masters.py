import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords

from core.models import BaseModel


# 絵文字マスタ
class M_Emoji(BaseModel):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID(URLに使用される可能性もあるため、予測できないUUIDで保持する)
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
        verbose_name="絵文字コード",
        db_comment="絵文字コード",
        max_length=50,
    )
    # 表示名
    display_name = models.CharField(
        db_column="display_name",
        verbose_name="表示名",
        db_comment="表示名",
        max_length=10,
        null=True,
        blank=True,
    )

    # django-simple-historyを使用
    # history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "m_emoji"
        db_table_comment = "絵文字マスタ"
        verbose_name = "絵文字マスタ"
        verbose_name_plural = "絵文字マスタ"
        constraints = [
            # 未削除のレコード内でのみ、絵文字コードが重複しないことを保証
            UniqueConstraint(
                fields=["code"],
                condition=Q(deleted_at__isnull=True),
                name="unique_m_emoji_code_active",
            ),
        ]

    def __str__(self):
        # display_nameがない場合でも壊れないように調整
        name = self.display_name if self.display_name else "No Name"
        return f"{self.code} - {name}"


# タグマスタ
class M_Tag(models.Model):
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
    # タグ名
    name = models.CharField(
        db_column="name",
        verbose_name="タグ名",
        db_comment="タグ名",
        max_length=64,
    )

    # テーブル名
    class Meta:
        db_table = "m_tag"
        db_table_comment = "タグマスタ"
        verbose_name = "タグマスタ"
        verbose_name_plural = "タグマスタ"
        constraints = [
            # 未削除のテーマ間でのみnameをユニークにする
            UniqueConstraint(
                fields=["name"],
                condition=Q(deleted_at__isnull=True),
                name="unique_m_tag_name_active",
            ),
        ]

    def __str__(self):
        return f"{self.name}"
