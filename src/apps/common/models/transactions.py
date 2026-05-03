import uuid
from django.utils import timezone
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords

# --- 共通モジュール ---
from core.models import BaseModel

class AbstractAttachment(BaseModel):
    # ファイルリソース(削除/物理削除の場合はCASCADE)
    file_resource = models.ForeignKey(
        "common.T_FileResource",
        db_column="file_resource_id",
        verbose_name="ファイルリソース",
        db_comment="ファイルリソース",
        on_delete=models.CASCADE,
        related_name="file_resource_%(class)s_set",
        null=True,
        blank=True,
    )
    # 並び順
    order = models.IntegerField(
        db_column="order",
        verbose_name="並び順",
        db_comment="並び順",
        default=0
    )
  
    class Meta:
        abstract = True

# ファイルリソーストラン
class T_FileResource(BaseModel):
    # ---------- Consts ----------
    # ファイル種別
    class FileType(models.TextChoices):
        IMAGE = "image", "画像"
        VIDEO = "video", "動画"
        PDF = "pdf", "PDF"
        OTHER = "other", "その他"

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
    # ファイル種別
    file_type = models.CharField(
        db_column="file_type",
        verbose_name="ファイル種別",
        db_comment="ファイル種別",
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
    )
    # ファイル(以下はFileFieldにて用意されている属性)
    #  name(相対パス): DBに保存されている文字列そのもの(例: logs/2026/05/abc.jpg)/MEDIA_ROOTからの相対パス
    #  path(絶対パス): OS上のフルパス(例: /Users/user/project/media/logs/2026/05/abc.jpg)
    #  url(URL): ブラウザからアクセスするためのURL(例: /media/logs/2026/05/abc.jpg)
    #  size(数値): ファイルサイズ(バイト単位)
    #  width, height(数値): 画像の場合の幅と高さ(ピクセル単位)
    file = models.FileField(
        db_column="file",
        verbose_name="ファイル",
        db_comment="ファイル",
        upload_to="file_resource/%Y/%m/%d/",  # 開発時は MEDIA_ROOT/file_resource/ に保存される
        max_length=255,
        null=True,
        blank=True,
    )
    # 外部URL(Spotify/Deezerの画像)
    external_url = models.URLField(
        db_column="external_url",
        verbose_name="外部URL",
        db_comment="外部URL",
        max_length=512,
        null=True,
        blank=True,
    )
    # ファイル名
    file_name = models.CharField(
        db_column="file_name",
        verbose_name="ファイル名",
        db_comment="ファイル名",
        max_length=255,
    )
    # ファイルサイズ
    file_size = models.BigIntegerField(
        db_column="file_size",
        verbose_name="ファイルサイズ",
        db_comment="ファイルサイズ",
        null=True,
        blank=True,
        help_text="単位: Byte"
    )

    @property
    def url(self):
        """
        内部ファイル/外部URL意識せずにURLを取得するためのプロパティ
        """
        if self.external_url:
            return self.external_url
        if self.file:
            return self.file.url
        return None

    # django-simple-historyを使用
    # history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "t_file_resource"
        db_table_comment = "ファイルリソーストラン"
        verbose_name = "ファイルリソーストラン"
        verbose_name_plural = "ファイルリソーストラン"
        constraints = [
            # 未削除のレコード内でのみ、外部リソースが重複しないことを保証
            UniqueConstraint(
                fields=["external_url"],
                # external_urlがnullでない場合のみチェック
                condition=Q(deleted_at__isnull=True) & Q(external_url__isnull=False),
                name="unique_t_file_resource_external_url_active",
            ),
            # 未削除のレコード内でのみ、ファイルが重複しないことを保証
            UniqueConstraint(
                fields=["file"],
                # fileがnullでない場合のみチェック
                condition=Q(deleted_at__isnull=True) & Q(file__isnull=False),
                name="unique_t_file_resource_file_active",
            ),
        ]

    def __str__(self):
        return f"{self.file_name}"
