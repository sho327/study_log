import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords
# --- コアモジュール ---
from core.models import BaseModel

# ログテーママスタ
class M_LogTheme(BaseModel):
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
    # ユーザマスタ(削除/物理削除の場合はCASCADE)
    user = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="user_m_log_theme_set",
    )
    # ログテーマ名
    name = models.CharField(
        db_column="name",
        verbose_name="ログテーマ名",
        db_comment="ログテーマ名",
        max_length=64,
    )

    # テーブル名
    class Meta:
        db_table = "m_log_theme"
        db_table_comment = "ログテーママスタ"
        verbose_name = "ログテーママスタ"
        verbose_name_plural = "ログテーママスタ"
        constraints = [
            # 未削除のテーマ間でのみnameをユニークにする
            UniqueConstraint(
                fields=["name"],
                condition=Q(deleted_at__isnull=True),
                name="unique_m_log_theme_name_active",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.name}"


# ログカテゴリマスタ
class M_LogCategory(BaseModel):
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
    # ユーザマスタ(削除/物理削除の場合はCASCADE)
    user = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="user_m_log_category_set",
    )
    # ログカテゴリ名
    name = models.CharField(
        db_column="name",
        verbose_name="ログカテゴリ名",
        db_comment="ログカテゴリ名",
        max_length=64,
    )

    # テーブル名
    class Meta:
        db_table = "m_log_category"
        db_table_comment = "ログカテゴリマスタ"
        verbose_name = "ログカテゴリマスタ"
        verbose_name_plural = "ログカテゴリマスタ"
        constraints = [
            # 未削除のテーマ間でのみnameをユニークにする
            UniqueConstraint(
                fields=["name"],
                condition=Q(deleted_at__isnull=True),
                name="unique_m_log_category_name_active",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.name}"