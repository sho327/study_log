import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords
from django.db.models import Count

# --- コアモジュール ---
from core.models import BaseModel

# --- 共通モジュール ---
from apps.common.models import AbstractAttachment, M_Tag, R_ItemTag


# ログトラン
class T_Log(BaseModel):
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
        related_name="user_t_log_set",
    )
    # ログテーママスタ(削除/物理削除の場合はSET_NULL)
    log_theme = models.ForeignKey(
        "log.M_LogTheme",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="log_theme_id",
        verbose_name="ログテーママスタ",
        db_comment="ログテーママスタ",
        on_delete=models.SET_NULL,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="log_theme_t_log_set",
        null=True,
        blank=True,
    )
    # ログカテゴリマスタ(削除/物理削除の場合はSET_NULL)
    log_category = models.ForeignKey(
        "log.M_LogCategory",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="log_category_id",
        verbose_name="ログカテゴリマスタ",
        db_comment="ログカテゴリマスタ",
        on_delete=models.SET_NULL,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="log_category_t_log_set",
        null=True,
        blank=True,
    )
    # 実施日
    date = models.DateField(
        db_column="date",
        verbose_name="実施日",
        db_comment="実施日",
    )
    # 作業時間(分)
    duration = models.PositiveIntegerField(
        db_column="duration",
        verbose_name="作業時間",
        db_comment="作業時間",
    )
    # 内容
    content = models.TextField(
        db_column="content",
        verbose_name="内容",
        db_comment="内容",
        null=True,
        blank=True,
    )
    # 成果物URL
    output_url = models.URLField(
        db_column="output_url",
        verbose_name="成果物URL",
        db_comment="成果物URL",
        null=True,
        blank=True,
    )
    # リアクション
    reactions = models.ManyToManyField(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        # ManyToManyFieldにはdb_columnは通常指定しない（中間テーブルで制御）
        verbose_name="リアクション",
        db_comment="リアクション",
        through="log.R_LogReaction",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        through_fields=("log", "user"),
        related_name="reactions_t_log_set",
    )

    @property
    def tags(self):
        """紐付いているタグのクエリセットを返す"""
        return M_Tag.objects.filter(
            tag_r_itemtag_set__item_type=R_ItemTag.ItemType.LOG,
            tag_r_itemtag_set__item_id=self.id,
            deleted_at__isnull=True,
        )

    @property
    def comment_count(self):
        """有効なコメント数を返す"""
        return self.log_t_log_comment_set.filter(deleted_at__isnull=True).count()

    @property
    def reaction_counts(self):
        """絵文字ごとのリアクション数を集計して返す"""
        return self.log_r_log_reaction_set.filter(
            deleted_at__isnull=True
        ).values("emoji_id").annotate(count=Count("emoji_id")).order_by("-count")

    # 履歴管理不要: django-simple-historyを使用しない
    # history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "t_log"
        db_table_comment = "ログトラン"
        verbose_name = "ログトラン"
        verbose_name_plural = "ログトラン"
        # constraints = [
        #     # 未削除間でのみmemoをユニークにする
        #     UniqueConstraint(
        #         fields=["memo"],
        #         condition=Q(deleted_at__isnull=True),
        #         name="unique_t_log_memo_active",
        #     ),
        # ]

    def __str__(self):
        return f"{self.user} - {self.content[:10] if self.content else ''}..."

# ログコメントトラン
class T_LogComment(BaseModel):
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
    # ログトラン(削除/物理削除の場合はCASCADE)
    log = models.ForeignKey(
        "log.T_Log",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="log_id",
        verbose_name="ログトラン",
        db_comment="ログトラン",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="log_t_log_comment_set",
    )
    # ユーザマスタ(削除/物理削除の場合はCASCADE)
    user = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="user_t_log_comment_set",
    )
    # 内容
    content = models.TextField(
        db_column="content",
        verbose_name="内容",
        db_comment="内容",
        null=True,
        blank=True,
    )
    # 返信先
    reply_to = models.ForeignKey(
        "self",
        db_column="reply_to_id",
        verbose_name="返信先",
        db_comment="返信先",
        on_delete=models.SET_NULL,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="reply_to_t_log_comment_set",
        null=True,
        blank=True,
    )
    # リアクション
    reactions = models.ManyToManyField(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        # ManyToManyFieldにはdb_columnは通常指定しない（中間テーブルで制御）
        verbose_name="リアクション",
        db_comment="リアクション",
        through="log.R_LogCommentReaction",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        through_fields=("log_comment", "user"),
        related_name="reactions_t_log_comment_set",
    )

    @property
    def reaction_counts(self):
        """絵文字ごとのリアクション数を集計して返す"""
        return self.log_r_log_comment_reaction_set.filter(
            deleted_at__isnull=True
        ).values("emoji_id").annotate(count=Count("emoji_id")).order_by("-count")

    # django-simple-historyを使用
    history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "t_log_comment"
        db_table_comment = "ログコメントトラン"
        verbose_name = "ログコメントトラン"
        verbose_name_plural = "ログコメントトラン"
        # constraints = [
        #     # 未削除間でのみmemoをユニークにする
        #     UniqueConstraint(
        #         fields=["memo"],
        #         condition=Q(deleted_at__isnull=True),
        #         name="unique_t_log_memo_active",
        #     ),
        # ]

    def __str__(self):
        return f"{self.content}"