import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords
# --- コアモジュール ---
from core.models import BaseModel
# --- 共通モジュール ---
from apps.common.models import AbstractAttachment


# ログ添付ファイルリレーション
class R_LogAttachment(AbstractAttachment):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与
    # ログトラン(削除/物理削除の場合はCASCADE)
    log = models.ForeignKey(
        "log.T_Log",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="log_id",
        verbose_name="ログトラン",
        db_comment="ログトラン",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="log_r_log_attachment_set",
    )
    # 継承元: ファイルリソース(削除/物理削除の場合はCASCADE)/file_resource
    # 継承元: 並び順/order

    # 履歴管理不要: django-simple-historyを使用しない
    # history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "r_log_attachment"
        db_table_comment = "ログ添付ファイルリレーション"
        verbose_name = "ログ添付ファイルリレーション"
        verbose_name_plural = "ログ添付ファイルリレーション"
        constraints = [
            # 未削除のトークン間でのみlog/file_resourceをユニークにする
            UniqueConstraint(
                fields=["log", "file_resource"],
                condition=Q(deleted_at__isnull=True),
                name="unique_r_log_attachment_log_file_resource_active",
            ),
        ]

    def __str__(self):
        return f"{self.log} - {self.file_resource}"


# ログリアクションリレーション
class R_LogReaction(BaseModel):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与
    # ログトラン(削除/物理削除の場合はCASCADE)
    log = models.ForeignKey(
        "log.T_Log",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="log_id",
        verbose_name="ログトラン",
        db_comment="ログトラン",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="log_r_log_reaction_set",
    )
    # ユーザマスタ(削除/物理削除の場合はSET_NULL)
    user = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.SET_NULL,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="user_r_log_reaction_set",
        null=True,
        blank=True,
    )
    # 絵文字(削除/物理削除の場合はCASCADE)
    emoji = models.ForeignKey(
        "common.M_Emoji",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="emoji_id",
        verbose_name="絵文字",
        db_comment="絵文字",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="emoji_r_log_reaction_set",
    )

    # django-simple-historyを使用
    # history = HistoricalRecords()

    class Meta:
        db_table = "r_log_reaction"
        db_table_comment = "ログリアクションリレーション"
        verbose_name = "ログリアクションリレーション"
        verbose_name_plural = "ログリアクションリレーション"
        constraints = [
            UniqueConstraint(
                fields=["log", "user", "emoji"],
                condition=Q(deleted_at__isnull=True),
                name="unique_r_log_reaction_log_user_emoji_active",
            ),
        ]


# ログコメント添付ファイルリレーション
class R_LogCommentAttachment(AbstractAttachment):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与
    # ログコメントトラン(削除/物理削除の場合はCASCADE)
    log_comment = models.ForeignKey(
        "log.T_LogComment",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="log_comment_id",
        verbose_name="ログコメントトラン",
        db_comment="ログコメントトラン",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="log_r_log_comment_attachment_set",
    )
    # 継承元: ファイルリソース(削除/物理削除の場合はCASCADE)/file_resource
    # 継承元: 並び順/order

    # 履歴管理不要: django-simple-historyを使用しない
    # history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "r_log_comment_attachment"
        db_table_comment = "ログコメント添付ファイルリレーション"
        verbose_name = "ログコメント添付ファイルリレーション"
        verbose_name_plural = "ログコメント添付ファイルリレーション"
        constraints = [
            # 未削除のトークン間でのみlog/file_resourceをユニークにする
            UniqueConstraint(
                fields=["log_comment", "file_resource"],
                condition=Q(deleted_at__isnull=True),
                name="unique_r_log_comment_attachment_log_comment_file_resource_active",
            ),
        ]

    def __str__(self):
        return f"{self.log_comment} - {self.file_resource}"

# ログコメントリアクションリレーション
class R_LogCommentReaction(BaseModel):
    # ---------- Consts ----------
    # ---------- Fields ----------
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与
    # ログコメントトラン(削除/物理削除の場合はCASCADE)
    log_comment = models.ForeignKey(
        "log.T_LogComment",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="log_comment_id",
        verbose_name="ログコメントトラン",
        db_comment="ログコメントトラン",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="log_r_log_comment_attachment_set",
    )
    # ユーザマスタ(削除/物理削除の場合はSET_NULL)
    user = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.SET_NULL,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="user_r_log_comment_reaction_set",
        null=True,
        blank=True,
    )
    # 絵文字(削除/物理削除の場合はCASCADE)
    emoji = models.ForeignKey(
        "common.M_Emoji",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="emoji_id",
        verbose_name="絵文字",
        db_comment="絵文字",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: 「参照先インスタンス.[related_name]」/通常参照は「本インスタンス.参照先モデル名(_id)」で取得可能)
        related_name="emoji_r_log_comment_reaction_set",
    )

    # django-simple-historyを使用
    # history = HistoricalRecords()

    class Meta:
        db_table = "r_log_comment_reaction"
        db_table_comment = "ログコメントリアクションリレーション"
        verbose_name = "ログコメントリアクションリレーション"
        verbose_name_plural = "ログコメントリアクションリレーション"
        constraints = [
            UniqueConstraint(
                fields=["log_comment", "user", "emoji"],
                condition=Q(deleted_at__isnull=True),
                name="unique_r_log_reaction_log_user_emoji_active",
            ),
        ]