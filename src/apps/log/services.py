import os
from datetime import datetime
from typing import List, Optional, Union
from django.db import transaction, Prefetch

# --- アカウントモジュール ---
from apps.account.models import M_User

# --- ログモジュール ---
from apps.log.exceptions import LogError, LogNotFoundError, LogCommentNotFoundError
from apps.log.models import (
    T_Log,
    T_LogComment,
    R_LogAttachment,
    R_LogCommentAttachment,
)

# --- 共通モジュール ---
from apps.common.models import T_FileResource, R_ItemTag
from apps.common.services.tag_service import TagService
from apps.common.services.storage_service import StorageService

# --- コアモジュール ---
from core.consts import LOG_METHOD
from core.exceptions.exceptions import ApplicationError
from core.utils.log_helpers import log_output_by_msg_id


class LogService:
    """
    ログ情報の登録/更新/管理を行うサービスクラス
    """

    def __init__(self):
        self.storage_service = StorageService()
        self.tag_service = TagService()

    # ------------------------------------------------------------------
    # 内部ヘルパーメソッド
    # ------------------------------------------------------------------
    def _upload_attachment_files(
        self,
        user: M_User,
        kino_id: str,
        parent_instance: Union[T_Log, T_LogComment],
        files: List,
        attachment_model: Union[type[R_LogAttachment], type[R_LogCommentAttachment]]
    ):
        """添付ファイルを一括処理する。DB失敗時はアップロードしたファイルを物理削除する。"""
        if not files:
            return

        upload_paths = []
        prefix = "log" if isinstance(parent_instance, T_Log) else "log_comment"
        
        try:
            attachment_links = []
            for index, file_obj in enumerate(files):
                # 1. 画像の保存
                path = self.storage_service.upload_file(
                    file_data=file_obj,
                    folder_path=f"{prefix}s/{parent_instance.id}",
                    original_filename=file_obj.name,
                )
                if path:
                    upload_paths.append(path)

                    # 2. 画像リソースの作成
                    file_resource = T_FileResource.objects.create(
                        file_type=T_FileResource.FileType.FILE,
                        file_data=path,
                        file_name=f"{prefix}_attachments_{parent_instance.id}_{index}",
                        created_by=user,
                        created_method=kino_id,
                        updated_by=user,
                        updated_method=kino_id,
                    )

                    # 3. 中間テーブル用データの準備
                    link_params = {
                        "file_resource": file_resource,
                        "order": index,
                        "created_by": user,
                        "created_method": kino_id,
                        "updated_by": user,
                        "updated_method": kino_id,
                    }
                    if isinstance(parent_instance, T_Log):
                        link_params["log"] = parent_instance
                    else:
                        link_params["log_comment"] = parent_instance

                    attachment_links.append(attachment_model(**link_params))

            # 4. 中間テーブルの一括登録
            if attachment_links:
                attachment_model.objects.bulk_create(attachment_links)
            
            # 5. 一括登録完了後、アップロードしたパスリストの返却
            return upload_paths

        except Exception as e:
            # 失敗時に保存した画像を即時削除
            for path in upload_paths:
                self.storage_service.delete_file(path)
            raise e

    def _delete_attachment_files(
        self, 
        file_resources: List[T_FileResource],
    ):
        """実ファイルを物理削除する"""
        for resource in file_resources:
            try:
                if resource.file_data:
                    self.storage_service.delete_file(resource.file_data)
            except Exception as e:
                log_output_by_msg_id(
                    log_id="MSGW001",
                    params=[f"Warning: Failed to delete physical file: {str(e)}"],
                    logger_name=LOG_METHOD.APPLICATION.value,
                )

    # ------------------------------------------------------------------
    # 一覧系サービス
    # ------------------------------------------------------------------
    # ログ一覧取得
    def list_log(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        validated_data: dict,
    ):
        """フィルタリングを考慮したログ一覧を取得する"""
        queryset = T_Log.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).select_related(
            "log_theme",
            "log_category",
        ).prefetch_related(
            "log_r_log_attachment_set__file_resource",
            Prefetch(
                "tag_r_itemtag_set",
                queryset=R_ItemTag.objects.filter(
                    item_type=R_ItemTag.ItemType.LOG,
                    deleted_at__isnull=True,
                    tag__deleted_at__isnull=True,
                ).select_related("tag").order_by("tag__name"),
                to_attr="tags",
            ),
        )

        # フィルタリング
        if validated_data.get("date_from"):
            queryset = queryset.filter(date__gte=validated_data["date_from"])
        if validated_data.get("date_to"):
            queryset = queryset.filter(date__lte=validated_data["date_to"])

        # ソート
        queryset = queryset.order_by("-date", "-created_at")

        return queryset

    # ログコメント一覧取得
    def list_log_comment(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_id: str,
    ):
        """特定のログに紐づくコメント一覧を取得する"""
        queryset = T_LogComment.objects.filter(
            log_id=log_id,
            deleted_at__isnull=True,
        ).select_related(
            "reply_to",
        ).prefetch_related(
            "log_r_log_comment_attachment_set__file_resource",
        ).order_by(
            "created_at",
        )

        return queryset

    # ------------------------------------------------------------------
    # 詳細系サービス
    # ------------------------------------------------------------------
    # ログ詳細取得
    def detail_log(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_id: str,
    ):
        """特定のログ詳細を取得する"""
        try:
            return T_Log.objects.filter(
                id=log_id,
                user=user,
                deleted_at__isnull=True,
            ).select_related(
                "log_theme",
                "log_category",
            ).prefetch_related(
                "log_r_log_attachment_set__file_resource",
                Prefetch(
                    "tag_r_itemtag_set",
                    queryset=R_ItemTag.objects.filter(
                        item_type=R_ItemTag.ItemType.LOG,
                        deleted_at__isnull=True,
                        tag__deleted_at__isnull=True,
                    ).select_related("tag").order_by("tag__name"),
                    to_attr="tags",
                ),
            ).get()
        except T_Log.DoesNotExist:
            raise LogNotFoundError()

    # ログコメント詳細取得
    def detail_log_comment(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        comment_id: str,
    ):
        """特定のコメント詳細を取得する"""
        try:
            return T_LogComment.objects.filter(
                id=comment_id,
                deleted_at__isnull=True,
            ).select_related(
                "reply_to",
            ).prefetch_related(
                "log_r_log_comment_attachment_set__file_resource",
            ).get()
        except T_LogComment.DoesNotExist:
            raise LogCommentNotFoundError()

    # ------------------------------------------------------------------
    # 登録系サービス
    # ------------------------------------------------------------------
    # ログ登録
    def create_log(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        validated_data: dict,
    ):
        """ログを新規登録する"""
        # 1. テーマ/カテゴリを取得
        log_theme = validated_data.get("log_theme_id")
        log_category = validated_data.get("log_category_id")

        # 2. ログ本体の作成
        log: T_Log = T_Log.objects.create(
            user=user,
            log_theme=log_theme,
            log_category=log_category,
            date=validated_data.get("date", date_now.date()),
            duration=validated_data.get("duration", 0),
            content=validated_data.get("content", ""),
            output_url=validated_data.get("output_url", ""),
            created_by=user,
            created_method=kino_id,
            updated_by=user,
            updated_method=kino_id,
        )

        # 3. タグとの紐付け(タグマスタに存在していれば、該当タグマスタのIDを使用、存在しなければタグマスタも新規作成し紐付ける)
        tag_names = validated_data.get("tag_names", [])
        if tag_names:
            self.tag_service.add_tags(
                item_type=R_ItemTag.ItemType.LOG,
                item_id=log.id,
                tag_names=tag_names,
            )

        upload_paths = []
        try:
            # 4. ログに紐づく添付ファイルリストの登録(エラー時はアップロード済みファイルを削除(ロールバック))
            attachment_files = validated_data.get("attachment_files", [])
            if attachment_files:
                upload_paths = self._upload_attachment_files(
                    user=user,
                    kino_id=kino_id,
                    model_instance=log,
                    files=attachment_files,
                    attachment_model=R_LogAttachment,
                )

            return log
        except Exception as e:
            # 失敗時に保存したファイルを即時削除
            for path in upload_paths:
                self.storage_service.delete_file(path)
            raise e

    # ログコメント登録
    def create_log_comment(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_id: str,
        validated_data: dict,
    ):
        """コメントを新規登録する"""
        # 1. ログの取得(存在チェックとロック)
        try:
            log = T_Log.objects.select_for_update().get(
                id=log_id,
                user=user,
                deleted_at__isnull=True,
            )
        except T_Log.DoesNotExist:
            raise LogNotFoundError()

        # 2. コメント本体の作成
        log_comment = T_LogComment.objects.create(
            log=log,
            content=validated_data.get("content", ""),
            reply_to=validated_data.get("reply_to_id", None),
            created_by=user,
            created_method=kino_id,
            updated_by=user,
            updated_method=kino_id,
        )

        upload_paths = []
        try:
            # 3. ログコメントに紐づく添付ファイルリストの登録(エラー時はアップロード済みファイルを削除(ロールバック))
            attachment_files = validated_data.get("attachment_files", [])
            if attachment_files:
                upload_paths = self._upload_attachment_files(
                    user=user,
                    kino_id=kino_id,
                    model_instance=log_comment,
                    files=attachment_files,
                    attachment_model=R_LogCommentAttachment,
                )

            return log_comment
        except Exception as e:
            # 失敗時に保存したファイルを即時削除
            for path in upload_paths:
                self.storage_service.delete_file(path)
            raise e

    # ------------------------------------------------------------------
    # 更新系サービス
    # ------------------------------------------------------------------
    # ログ更新
    def update_log(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_id: str,
        validated_data: dict,
    ):
        """ログ情報を更新する"""
        # 1. ログの取得(存在チェックとロック)
        try:
            log = T_Log.objects.select_for_update().get(
                id=log_id,
                user=user,
                deleted_at__isnull=True,
            )
        except T_Log.DoesNotExist:
            raise LogNotFoundError()

        if "log_theme_id" in validated_data:
            log.log_theme = validated_data["log_theme_id"]
        
        if "log_category_id" in validated_data:
            log.log_category = validated_data["log_category_id"]
        
        if "date" in validated_data:
            log.date = validated_data["date"]
        
        if "duration" in validated_data:
            log.duration = validated_data["duration"]
        
        if "content" in validated_data:
            log.content = validated_data["content"]
        
        if "output_url" in validated_data:
            log.output_url = validated_data["output_url"]
        
        log.updated_method = kino_id
        log.updated_by = user
        log.save()

        # 3. タグとの紐付け(タグマスタに存在していれば、該当タグマスタのIDを使用、存在しなければタグマスタも新規作成し紐付ける)
        tag_names = validated_data.get("tag_names", [])
        if tag_names:
            self.tag_service.add_tags(
                item_type=R_ItemTag.ItemType.LOG,
                item_id=log.id,
                tag_names=tag_names,
            )
            
        
            
        delete_resource_list = []
        try:
            log = T_Log.objects.select_for_update().get(id=log_id, user=user, deleted_at__isnull=True)

            # 1. タグ洗替
            if "tag_ids" in validated_data:
                tags = validated_data.pop("tag_ids")
                R_LogTag.objects.filter(log=log).delete()
                if tags:
                    R_LogTag.objects.bulk_create([
                        R_LogTag(log=log, tag=tag, created_by=user, created_method=kino_id, updated_by=user, updated_method=kino_id)
                        for tag in tags
                    ])

            # 2. 添付ファイル洗替
            if files is not None:
                old_rels = R_LogAttachment.objects.filter(log=log).select_related("file_resource")
                for rel in old_rels:
                    delete_resource_list.append(rel.file_resource)
                
                old_rels.delete()
                for res in delete_resource_list:
                    res.delete()
                
                self._process_attachments(user, kino_id, log, files, R_LogAttachment)

            # 3. フィールド更新
            for attr, value in validated_data.items():
                setattr(log, attr, value)
            log.updated_by = user
            log.updated_method = kino_id
            log.save()

            # 4. 旧実ファイルの物理削除(成功時)
            self._delete_physical_files(delete_resource_list)

            return log
        except T_Log.DoesNotExist:
            raise LogNotFoundError()
        except Exception as e:
            raise e

    @transaction.atomic
    def update_comment(self, date_now: datetime, kino_id: str, user: M_User, comment_id: str, validated_data: dict, files: List = None):
        """コメント情報を更新する"""
        delete_resource_list = []
        try:
            comment = T_LogComment.objects.select_for_update().get(id=comment_id, deleted_at__isnull=True)

            if files is not None:
                old_rels = R_LogCommentAttachment.objects.filter(log_comment=comment).select_related("file_resource")
                for rel in old_rels:
                    delete_resource_list.append(rel.file_resource)
                
                old_rels.delete()
                for res in delete_resource_list:
                    res.delete()
                
                self._process_attachments(user, kino_id, comment, files, R_LogCommentAttachment)

            for attr, value in validated_data.items():
                setattr(comment, attr, value)
            comment.updated_by = user
            comment.updated_method = kino_id
            comment.save()

            self._delete_physical_files(delete_resource_list)

            return comment
        except T_LogComment.DoesNotExist:
            raise LogNotFoundError()
        except Exception as e:
            raise e

    # ------------------------------------------------------------------
    # 削除系サービス
    # ------------------------------------------------------------------

    @transaction.atomic
    def delete_log(self, date_now: datetime, kino_id: str, user: M_User, log_id: str):
        """ログを論理削除する"""
        try:
            log = T_Log.objects.select_for_update().get(id=log_id, user=user, deleted_at__isnull=True)
            
            attachments = R_LogAttachment.objects.filter(log=log).select_related("file_resource")
            for rel in attachments:
                res = rel.file_resource
                res.deleted_at = date_now
                res.updated_by = user
                res.updated_method = kino_id
                res.save()
            
            attachments.delete()
            R_LogTag.objects.filter(log=log).delete()

            log.deleted_at = date_now
            log.updated_by = user
            log.updated_method = kino_id
            log.save()
        except T_Log.DoesNotExist:
            raise LogNotFoundError()

    @transaction.atomic
    def delete_comment(self, date_now: datetime, kino_id: str, user: M_User, comment_id: str):
        """コメントを論理削除する"""
        try:
            comment = T_LogComment.objects.select_for_update().get(id=comment_id, deleted_at__isnull=True)
            
            attachments = R_LogCommentAttachment.objects.filter(log_comment=comment).select_related("file_resource")
            for rel in attachments:
                res = rel.file_resource
                res.deleted_at = date_now
                res.updated_by = user
                res.updated_method = kino_id
                res.save()
            
            attachments.delete()
            
            comment.deleted_at = date_now
            comment.updated_by = user
            comment.updated_method = kino_id
            comment.save()
        except T_LogComment.DoesNotExist:
            raise LogNotFoundError()