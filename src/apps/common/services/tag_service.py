import os
from typing import List, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.template.loader import render_to_string
from django.urls import reverse

# --- コアモジュール ---
from core.consts import LOG_METHOD
from core.utils.log_helpers import log_output_by_msg_id
from core.exceptions.exceptions import ExternalServiceError

# --- 共通モジュール ---
from apps.common.models import M_Tag, R_ItemTag


class TagService:
    """
    アプリケーションで発生するタグ関連処理を一括管理するサービス。
    """

    def __init__(self):
        pass
    
    # ------------------------------------------------------------------
    # 一覧取得系サービス※クエリセットを返却
    # ------------------------------------------------------------------
    def get_item_tags_queryset(self, item_type: str, item_id: int) -> QuerySet[R_ItemTag]:
        """
        アイテムタグを取得する。

        Args:
            item_type: アイテム種別
            item_id: アイテムID

        Returns:
            アイテムタグのクエリセット
        """
        return R_ItemTag.objects.filter(
            item_type=item_type,
            item_id=item_id,
        ).select_related("tag")

    # ------------------------------------------------------------------
    # ※その他M_Tagに関するCRUDはModelViewSetで行う※
    # ------------------------------------------------------------------
    
    # ------------------------------------------------------------------
    # その他サービス
    # ------------------------------------------------------------------
    def add_tags(self, item_type: str, item_id: int, tags: List[M_Tag]):
        """
        タグを追加する。
        """
        for tag in tags:
            R_ItemTag.objects.create(
                item_type=item_type,
                item_id=item_id,
                tag=tag,
            )

    def add_tags(self, item_type: str, item_id: int, tag_names: List[str]):
        """
        タグを追加する。
        """
        for tag_name in tag_names:
            tag, created = M_Tag.objects.get_or_create(
                name=tag_name,
            )
            R_ItemTag.objects.create(
                item_type=item_type,
                item_id=item_id,
                tag=tag,
            )
    
    def remove_tags(self, item_type: str, item_id: int, tags: List[M_Tag]):
        """
        タグを削除する。
        """
        R_ItemTag.objects.filter(
            item_type=item_type,
            item_id=item_id,
            tag__in=tags,
        ).delete()

    def remove_tags(self, item_type: str, item_id: int, tag_names: List[str]):
        """
        タグを削除する。
        """
        tags = M_Tag.objects.filter(name__in=tag_names)
        R_ItemTag.objects.filter(
            item_type=item_type,
            item_id=item_id,
            tag__in=tags,
        ).delete()

    