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
    def upsert_tags_by_names(self, item_type: str, item_id: int, tag_names: List[str]):
        """
        タグ名をもとにタグをUPSERTする。
        """
        # 重複タグの削除(小文字変換/前後の空白削除/空文字列削除)
        unique_tag_names = list(set([tag.strip().lower() for tag in tag_names if tag and tag.strip()]))

        # 重複タグが存在しない場合は終了
        if not unique_tag_names:
            return

        # 既存のタグを一括取得
        existing_tags = M_Tag.objects.filter(
            name__in=unique_tag_names,
            deleted_at__isnull=True,
        )
        existing_tag_names = {t.name for t in existing_tags}

        # 存在しないタグを作成
        new_tag_names = [name for name in unique_tag_names if name not in existing_tag_names]
        if new_tag_names:
            M_Tag.objects.bulk_create(
                [
                    M_Tag(
                        name=name,
                    ) 
                    for name in new_tag_names
                ],
                ignore_conflicts=True
            )
            # 新規作成分を含めて再取得
            all_tags = list(M_Tag.objects.filter(
                name__in=unique_tag_names,
                deleted_at__isnull=True,
            ))
        else:
            all_tags = list(existing_tags)

        # すでに設定済みタグを弾く
        already_linked_tag_ids = R_ItemTag.objects.filter(
            item_type=item_type,
            item_id=item_id,
            tag__in=all_tags,
            deleted_at__isnull=True,
            tag__deleted_at__isnull=True,
        ).values_list("tag_id", flat=True)

        tags_to_link = [tag for tag in all_tags if tag.id not in already_linked_tag_ids]

        # 紐付けが必要なタグが存在するかチェック
        if not tags_to_link:
            return

        # tagsを関連付け
        R_ItemTag.objects.bulk_create(
            [
                R_ItemTag(
                    item_type=item_type,
                    item_id=item_id,
                    tag=tag,
                )
                for tag in tags_to_link
            ]
        )
    
    def remove_tags_by_names(self, item_type: str, item_id: int, tag_names: List[str]):
        """
        タグ名をもとにタグを削除する。
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
        ).delete()

    def remove_all_tags(self, item_type: str, item_id: int):
        """
        タグを全削除する。
        """
        # タグの削除
        R_ItemTag.objects.filter(
            item_type=item_type,
            item_id=item_id,
            deleted_at__isnull=True,
        ).delete()

    