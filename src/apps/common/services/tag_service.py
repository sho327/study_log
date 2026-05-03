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
            deleted_at__isnull=True,
            tag__deleted_at__isnull=True,
        ).select_related("tag").order_by("tag__name")

    # ------------------------------------------------------------------
    # ※その他M_Tagに関するCRUDはModelViewSetで行う※
    # ------------------------------------------------------------------
    
    # ------------------------------------------------------------------
    # その他サービス
    # ------------------------------------------------------------------
    def add_tags(self, item_type: str, item_id: int, tag_names: List[str]):
        """
        タグを追加する。
        """
        # 重複タグの削除(小文字変換/前後の空白削除/空文字列削除)
        unique_tag_names = list(set([tag.strip().lower() for tag in tag_names if tag and tag.strip()]))

        # 重複タグが存在しない場合は終了
        if not unique_tag_names:
            return

        # タグの取得または作成
        tags = []
        for tag_name in unique_tag_names:
            tag = M_Tag.objects.filter(
                name=tag_name,
                deleted_at__isnull=True,
            ).first()
            if not tag:
                tag = M_Tag.objects.create(
                    name=tag_name,
                )
            tags.append(tag)

        # すでに設定済みタグを弾く
        existing_tags = R_ItemTag.objects.filter(
            item_type=item_type,
            item_id=item_id,
            tag__in=tags,
            deleted_at__isnull=True,
            tag__deleted_at__isnull=True,
        ).values_list("tag_id", flat=True)
        tags = [tag for tag in tags if tag.id not in existing_tags]

        # tagsが存在するかチェック
        if not tags:
            return

        # tagsを関連付け
        R_ItemTag.objects.bulk_create(
            [
                R_ItemTag(
                    item_type=item_type,
                    item_id=item_id,
                    tag=tag,
                )
                for tag in tags
            ]
        )
    
    def remove_tags(self, item_type: str, item_id: int, tag_names: List[str]):
        """
        タグを削除する。
        """
        # 重複タグの削除(小文字変換/前後の空白削除/空文字列削除)
        unique_tag_names = list(set([tag.strip().lower() for tag in tag_names if tag and tag.strip()]))

        # 重複タグが存在しない場合は終了
        if not unique_tag_names:
            return
        # タグの存在チェック
        tags = M_Tag.objects.filter(
            name__in=unique_tag_names,
            deleted_at__isnull=True,
        )
        # tagsが存在するかチェック
        if not tags:
            return

        # tagsを削除
        R_ItemTag.objects.filter(
            item_type=item_type,
            item_id=item_id,
            tag__in=tags,
            deleted_at__isnull=True,
            tag__deleted_at__isnull=True,
        ).delete()

    