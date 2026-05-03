import uuid
from django.utils import timezone
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords

# --- 共通モジュール ---
from core.models import BaseModel

class AbstractSimpleReaction(BaseModel):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与
    # ユーザマスタ(削除/物理削除の場合はSET_NULL)
    user = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.SET_NULL,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="user_%(class)s_set",
        null=True,
        blank=True,
    )
  
    class Meta:
        abstract = True

class AbstractEmojiReaction(BaseModel):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与
    # ユーザマスタ(削除/物理削除の場合はSET_NULL)
    user = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.SET_NULL,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="user_%(class)s_set",
        null=True,
        blank=True,
    )
    # 絵文字(削除/物理削除の場合はCASCADE)
    emoji = models.ForeignKey(
        "common.M_Emoji",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="emoji_id",
        verbose_name="絵文字",
        db_comment="絵文字",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="emoji_%(class)s_set",
    )
  
    class Meta:
        abstract = True


# アイテムタグリレーション
class R_ItemTag(BaseModel):
    # ---------- Consts ----------
    # 紐付け先アイテム種別
    class ItemType(models.TextChoices):
        LOG = "LOG", "ログ"

    # ---------- Fields ----------
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与
    # タグ(削除/物理削除の場合はCASCADE)
    item_type = models.CharField(
        db_column="item_type",
        verbose_name="アイテム種別",
        db_comment="アイテム種別",
        max_length=20,
        choices=ItemType.choices,
    )
    # タグ(削除/物理削除の場合はCASCADE)
    item_id = models.BigIntegerField(
        db_column="item_id",
        verbose_name="アイテムID",
        db_comment="アイテムID",
    )
    # タグ(削除/物理削除の場合はCASCADE)
    tag = models.ForeignKey(
        "common.M_Tag",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="tag_id",
        verbose_name="タグ",
        db_comment="タグ",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="tag_%(class)s_set",
    )
  
    # django-simple-historyを使用
    # history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "r_item_tag"
        db_table_comment = "アイテムタグリレーション"
        verbose_name = "アイテムタグリレーション"
        verbose_name_plural = "アイテムタグリレーション"
        constraints = [
            # 未削除のレコード内でのみ、アイテムタグリレーションが重複しないことを保証
            UniqueConstraint(
                fields=["item_type", "item_id", "tag"],
                condition=Q(deleted_at__isnull=True),
                name="unique_r_item_tag_item_type_item_id_tag_active",
            ),
        ]

    def __str__(self):
        return f"{self.item_type} - {self.item_id} - {self.tag}"
