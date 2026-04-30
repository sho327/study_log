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
