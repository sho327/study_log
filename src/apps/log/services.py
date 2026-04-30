import os
from datetime import datetime
from typing import List, Optional, Union

from django.db import transaction

# --- アカウントモジュール ---
from apps.account.models import M_User

# --- ログモジュール ---
from apps.log.exceptions import LogError, LogNotFoundError, LogCommentNotFoundError
from apps.log.models import (
    T_Log, 
    T_LogComment, 
    R_LogAttachment, 
    R_LogCommentAttachment,
    R_LogTag,
)

# --- 共通モジュール ---
from apps.common.models import T_FileResource
from apps.common.services.storage_service import StorageService
from core.consts import LOG_METHOD
from core.exceptions.exceptions import ApplicationError
from core.utils.log_helpers import log_output_by_msg_id


class LogService:
    """
    ログ情報の登録/更新/管理を行うサービスクラス
    """

    def __init__(self):
        self.storage_service = StorageService()

    # ------------------------------------------------------------------
    # 内部ヘルパーメソッド
    # ------------------------------------------------------------------

    def _upload_attachments(
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
                    folder_path=f"{prefix}/{parent_instance.id}",
                    original_filename=file_obj.name,
                )
                if path:
                    upload_paths.append(path)

                    # 2. 画像リソースの作成
                    file_resource = T_FileResource.objects.create(
                        file_type=T_FileResource.FileType.FILE,
                        file_data=path,
                        file_name=file_obj.name,
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

    def _delete_attachments(,
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
    def list_log(self, date_now: datetime, kino_id: str, user: M_User, **filters):
        """フィルタリングを考慮したログ一覧を取得する"""
        queryset = T_Log.objects.filter(
            user=user, deleted_at__isnull=True
        ).select_related(
            "log_theme",
            "log_category"
        ).prefetch_related(
            "tags",
            "log_r_log_attachment_set__file_resource"
        )

        if filters.get("date_from"):
            queryset = queryset.filter(date__gte=filters["date_from"])
        if filters.get("date_to"):
            queryset = queryset.filter(date__lte=filters["date_to"])

        return queryset.order_by("-date", "-created_at")

    # コメント一覧取得
    def list_comment(self, date_now: datetime, kino_id: str, user: M_User, log_id: str):
        """特定のログに紐づくコメント一覧を取得する"""
        return T_LogComment.objects.filter(
            log_id=log_id, deleted_at__isnull=True
        ).select_related(
            "reply_to"
        ).prefetch_related(
            "log_r_log_comment_attachment_set__file_resource"
        ).order_by(
            "created_at"
        )


    # ------------------------------------------------------------------
    # 詳細系サービス
    # ------------------------------------------------------------------
    # ログ詳細取得
    def detail_log(self, date_now: datetime, kino_id: str, user: M_User, log_id: str):
        """特定のログ詳細を取得する"""
        try:
            return T_Log.objects.filter(
                id=log_id, user=user, deleted_at__isnull=True
            ).select_related("log_theme", "log_category") \
             .prefetch_related("tags", "log_r_log_attachment_set__file_resource") \
             .get()
        except T_Log.DoesNotExist:
            raise LogNotFoundError()

    def detail_comment(self, date_now: datetime, kino_id: str, user: M_User, comment_id: str):
        """特定のコメント詳細を取得する"""
        try:
            return T_LogComment.objects.filter(
                id=comment_id, deleted_at__isnull=True
            ).select_related("reply_to") \
             .prefetch_related("log_r_log_comment_attachment_set__file_resource") \
             .get()
        except T_LogComment.DoesNotExist:
            raise LogNotFoundError()

    # ------------------------------------------------------------------
    # 登録系サービス
    # ------------------------------------------------------------------

    @transaction.atomic
    def create_log(self, date_now: datetime, kino_id: str, user: M_User, validated_data: dict, files: List = None):
        """ログを新規登録する"""
        upload_paths = []
        try:
            # 1. タグデータの分離
            tags = validated_data.pop("tag_ids", [])

            # 2. ログ本体の作成
            log = T_Log.objects.create(
                user=user,
                **validated_data,
                created_by=user,
                created_method=kino_id,
                updated_by=user,
                updated_method=kino_id,
            )

            # 3. タグとの紐付け
            if tags:
                tag_links = [
                    R_LogTag(log=log, tag=tag, created_by=user, created_method=kino_id, updated_by=user, updated_method=kino_id)
                    for tag in tags
                ]
                R_LogTag.objects.bulk_create(tag_links)

            # 4. 添付ファイルの登録 (内部でupload_file実行 & 例外時物理削除)
            if files:
                upload_paths = self._process_attachments(user, kino_id, log, files, R_LogAttachment)

            return log
        except Exception as e:
            # 失敗時に保存した画像を即時削除
            for path in upload_paths:
                self.storage_service.delete_file(path)
            raise e

    @transaction.atomic
    def create_comment(self, date_now: datetime, kino_id: str, user: M_User, validated_data: dict, files: List = None):
        """コメントを新規登録する"""
        upload_paths = []
        try:
            comment = T_LogComment.objects.create(
                **validated_data,
                created_by=user,
                created_method=kino_id,
                updated_by=user,
                updated_method=kino_id,
            )
            if files:
                upload_paths = self._process_attachments(user, kino_id, comment, files, R_LogCommentAttachment)
            return comment
        except Exception as e:
            # 失敗時に保存した画像を即時削除
            for path in upload_paths:
                self.storage_service.delete_file(path)
            raise e

    # ------------------------------------------------------------------
    # 更新系サービス
    # ------------------------------------------------------------------

    @transaction.atomic
    def update_log(self, date_now: datetime, kino_id: str, user: M_User, log_id: str, validated_data: dict, files: List = None):
        """ログ情報を更新する"""
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