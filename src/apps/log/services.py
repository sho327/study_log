import os
from datetime import datetime
from typing import List, Optional, Union
from django.db import transaction, Prefetch
from django.db.models import Count, Q, QuerySet

# --- アカウントモジュール ---
from apps.account.models import M_User

# --- ログモジュール ---
from apps.log.exceptions import (
    LogError, 
    LogNotFoundError, 
    LogCommentNotFoundError, 
    LogReactionConflictError, 
    LogCommentReactionConflictError
)
from apps.log.models import (
    T_Log,
    T_LogComment,
    R_LogAttachment,
    R_LogCommentAttachment,
    R_LogReaction,
    R_LogCommentReaction,
)

# --- 共通モジュール ---
from apps.common.models import M_Emoji, T_FileResource, R_ItemTag
from apps.common.services.tag_service import TagService
from apps.common.services.storage_service import StorageService
from apps.common.exceptions import EmojiNotFoundError

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
        """添付ファイルを一括処理する。"""
        if not files:
            return []

        prefix = "log" if isinstance(parent_instance, T_Log) else "log_comment"
        
        # StorageServiceの一括アップロードを使用
        file_resources = self.storage_service.upload_resources(
            user=user,
            kino_id=kino_id,
            files=files,
            folder_path=f"{prefix}s/{parent_instance.id}",
            file_type=T_FileResource.FileType.FILE,
            file_name_prefix=f"{prefix}_attachments_{parent_instance.id}",
        )

        # 中間テーブル(リレーション)の作成
        attachment_links = []
        for index, resource in enumerate(file_resources):
            link_params = {
                "file_resource": resource,
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

        if attachment_links:
            attachment_model.objects.bulk_create(attachment_links)
        
        return file_resources

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
        ).annotate(
            # コメント数の集計(N+1対策)
            # Countを使用することで、コメントの削除チェックなどを行わずに、
            # 未削除のコメントのみを事前に集計し、シリアライザ内でのループ処理時にN+1が発生しないようにする
            comment_count=Count(
                "log_t_log_comment_set",
                filter=Q(log_t_log_comment_set__deleted_at__isnull=True),
                distinct=True
            )
        ).prefetch_related(
            "log_r_log_attachment_set__file_resource",
            # リアクションの一括取得(シリアライザでのメモリ集計用)
            # Prefetchを使用することで、未削除のリアクションのみを事前に取得し、
            # シリアライザ内でのループ処理時にN+1が発生しないようにする
            Prefetch(
                "log_r_log_reaction_set",
                queryset=R_LogReaction.objects.filter(deleted_at__isnull=True)
            ),
            # タグの一括取得
            # Prefetchを使用することで、タグの削除チェックなどを行わずに、
            # 未削除のタグのみを事前に取得し、シリアライザ内でのループ処理時にN+1が発生しないようにする
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
            # リアクションの一括取得(シリアライザでのメモリ集計用)
            # Prefetchを使用することで、未削除のリアクションのみを事前に取得し、
            # シリアライザ内でのループ処理時にN+1が発生しないようにする
            Prefetch(
                "log_r_log_comment_reaction_set",
                queryset=R_LogCommentReaction.objects.filter(deleted_at__isnull=True)
            )
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
            ).annotate(
                # コメント数の集計(N+1対策)
                # Countを使用することで、コメントの削除チェックなどを行わずに、
                # 未削除のコメントのみを事前に集計し、シリアライザ内でのループ処理時にN+1が発生しないようにする
                comment_count=Count(
                    "log_t_log_comment_set",
                    filter=Q(log_t_log_comment_set__deleted_at__isnull=True),
                    distinct=True
                )
            ).prefetch_related(
                "log_r_log_attachment_set__file_resource",
                # リアクションの一括取得(シリアライザでのメモリ集計用)
                # Prefetchを使用することで、未削除のリアクションのみを事前に取得し、
                # シリアライザ内でのループ処理時にN+1が発生しないようにする
                Prefetch(
                    "log_r_log_reaction_set",
                    queryset=R_LogReaction.objects.filter(deleted_at__isnull=True)
                ),
                # コメント階層全体の最適化取得
                # Prefetchを使用することで、コメント/返信コメント、添付ファイル、リアクションをまとめて取得し、
                # シリアライザ内でのループ処理時にN+1が発生しないようにする
                Prefetch(
                    "log_t_log_comment_set",
                    queryset=T_LogComment.objects.filter(
                        deleted_at__isnull=True
                    ).select_related("created_by").prefetch_related(
                        Prefetch(
                            "log_r_log_comment_attachment_set",
                            queryset=R_LogCommentAttachment.objects.filter(deleted_at__isnull=True).select_related("file_resource")
                        ),
                        Prefetch(
                            "log_r_log_comment_reaction_set",
                            queryset=R_LogCommentReaction.objects.filter(deleted_at__isnull=True)
                        )
                    )
                ),
                # タグの一括取得
                # Prefetchを使用することで、タグの削除チェックなどを行わずに、
                # 未削除のタグのみを事前に取得し、シリアライザ内でのループ処理時にN+1が発生しないようにする
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
                # リアクションの一括取得(シリアライザでのメモリ集計用)
                # Prefetchを使用することで、未削除のリアクションのみを事前に取得し、
                # シリアライザ内でのループ処理時にN+1が発生しないようにする
                Prefetch(
                    "log_r_log_comment_reaction_set",
                    queryset=R_LogCommentReaction.objects.filter(deleted_at__isnull=True)
                )
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
            self.tag_service.upsert_tags_by_names(
                item_type=R_ItemTag.ItemType.LOG,
                item_id=log.id,
                tag_names=tag_names,
            )

        new_resources = []
        try:
            # 4. ログに紐づく添付ファイルリストの登録
            attachment_files = validated_data.get("attachment_files", [])
            if attachment_files:
                new_resources = self._upload_attachment_files(
                    user=user,
                    kino_id=kino_id,
                    parent_instance=log,
                    files=attachment_files,
                    attachment_model=R_LogAttachment,
                )

            return log
        except Exception as e:
            # 失敗時に保存したリソースを即時削除
            self.storage_service.delete_resources(new_resources)
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
        # SELECT * FROM t_log WHERE id = '...' FOR UPDATE; を実行し、トランザクション中のロックを取得する
        # 「数値を増減させる」「設定を書き換える」など、同時に実行されるとデータが矛盾してしまう可能性がある更新処理の直前に使う
        # ※コメント中はログの削除をさせない※
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

        new_resources = []
        try:
            # 3. ログコメントに紐づく添付ファイルリストの登録
            attachment_files = validated_data.get("attachment_files", [])
            if attachment_files:
                new_resources = self._upload_attachment_files(
                    user=user,
                    kino_id=kino_id,
                    parent_instance=log_comment,
                    files=attachment_files,
                    attachment_model=R_LogCommentAttachment,
                )

            return log_comment
        except Exception as e:
            # 失敗時に保存したリソースを即時削除
            self.storage_service.delete_resources(new_resources)
            raise e

    # ------------------------------------------------------------------
    # 更新系サービス
    # ------------------------------------------------------------------
    # ログ更新
    # ※注意※ validated_dataに「attachment_files」が含まれる場合、関連付けされているリソースを洗替
    # = 既存のリソースを全て削除 -> 新しいリソースを全件登録(空リストで添付ファイル無しにも可能)
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
        # SELECT * FROM t_log WHERE id = '...' FOR UPDATE; を実行し、トランザクション中のロックを取得する
        # 「数値を増減させる」「設定を書き換える」など、同時に実行されるとデータが矛盾してしまう可能性がある更新処理の直前に使う
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

        # 2. タグの紐付け(洗替方式)
        self.tag_service.remove_all_tags(
            item_type=R_ItemTag.ItemType.LOG,
            item_id=log.id,
        )
        tag_names = validated_data.get("tag_names", [])
        if tag_names:
            # タグとの紐付け(タグマスタに存在していれば、該当タグマスタのIDを使用、存在しなければタグマスタも新規作成し紐付ける)
            self.tag_service.upsert_tags_by_names(
                item_type=R_ItemTag.ItemType.LOG,
                item_id=log.id,
                tag_names=tag_names,
            )

        # 3. 添付ファイルの紐付け(洗替方式)
        new_resources = []
        old_resources = []
        try:
            # 3. 添付ファイルの紐付け(洗替方式: キーが存在する場合のみ実行)
            if "attachment_files" in validated_data:
                # 3-1. 物理削除用に古いリソースを保持
                old_resources = [
                    rel.file_resource 
                    for rel in R_LogAttachment.objects.filter(log=log, deleted_at__isnull=True).select_related("file_resource")
                    if rel.file_resource
                ]
                
                # 3-2. DB上の古いリレーションを削除
                R_LogAttachment.objects.filter(
                    log=log, 
                    deleted_at__isnull=True
                ).delete()

                # 3-3. 新しい添付ファイルがある場合はアップロードし、レコードを新規作成
                attachment_files = validated_data.get("attachment_files", [])
                if attachment_files:
                    new_resources = self._upload_attachment_files(
                        user=user,
                        kino_id=kino_id,
                        parent_instance=log,
                        files=attachment_files,
                        attachment_model=R_LogAttachment,
                    )

            # 4. 監査用情報の更新
            log.updated_by = user
            log.updated_method = kino_id
            log.save()

            # 5. 旧リソースの物理削除(成功時のみ実行)
            if old_resources:
                self.storage_service.delete_resources(old_resources)

            return log
        except Exception as e:
            # 失敗時に、今回新しく作成したリソースをロールバック(物理削除)
            self.storage_service.delete_resources(new_resources)
            raise e

    # ログコメント更新
    # ※注意※ validated_dataに「attachment_files」が含まれる場合、関連付けされているリソースを洗替
    # = 既存のリソースを全て削除 -> 新しいリソースを全件登録(空リストで添付ファイル無しにも可能)
    def update_log_comment(
        self, 
        date_now: datetime, 
        kino_id: str, 
        user: M_User, 
        log_id: str,
        log_comment_id: str,
        validated_data: dict,
    ):
        """コメント情報を更新する"""
        # 1. ログの取得(存在チェックとロック)
        # SELECT * FROM t_log WHERE id = '...' FOR UPDATE; を実行し、トランザクション中のロックを取得する
        # 「数値を増減させる」「設定を書き換える」など、同時に実行されるとデータが矛盾してしまう可能性がある更新処理の直前に使う
        # ※コメント中はログの削除をさせない※
        try:
            log = T_Log.objects.select_for_update().get(
                id=log_id,
                user=user,
                deleted_at__isnull=True,
            )
        except T_Log.DoesNotExist:
            raise LogNotFoundError()
        
        # 2. コメントの取得(存在チェックとロック)
        # SELECT * FROM t_log WHERE id = '...' FOR UPDATE; を実行し、トランザクション中のロックを取得する
        # 「数値を増減させる」「設定を書き換える」など、同時に実行されるとデータが矛盾してしまう可能性がある更新処理の直前に使う
        try:
            log_comment = T_LogComment.objects.select_for_update().get(
                id=log_comment_id, 
                log=log,
                deleted_at__isnull=True
            )
        except T_LogComment.DoesNotExist:
            raise LogCommentNotFoundError()
        
        if "content" in validated_data:
            log_comment.content = validated_data["content"]
        
        if "reply_to_id" in validated_data:
            log_comment.reply_to = validated_data["reply_to_id"]

        new_resources = []
        old_resources = []
        try:
            # 3. 添付ファイルの紐付け(洗替方式: キーが存在する場合のみ実行)
            if "attachment_files" in validated_data:
                # 3-1. 物理削除用に古いリソースを保持
                old_resources = [
                    rel.file_resource 
                    for rel in R_LogCommentAttachment.objects.filter(log_comment=log_comment, deleted_at__isnull=True).select_related("file_resource")
                    if rel.file_resource
                ]
                
                # 3-2. DB上の古いリレーションを削除
                R_LogCommentAttachment.objects.filter(
                    log_comment=log_comment,
                    deleted_at__isnull=True
                ).delete()

                # 3-3. 新しい添付ファイルがある場合はアップロードし、レコードを新規作成
                attachment_files = validated_data.get("attachment_files", [])
                if attachment_files:
                    new_resources = self._upload_attachment_files(
                        user=user,
                        kino_id=kino_id,
                        parent_instance=log_comment,
                        files=attachment_files,
                        attachment_model=R_LogCommentAttachment,
                    )

            # 4. 監査用情報の更新
            log_comment.updated_by = user
            log_comment.updated_method = kino_id
            log_comment.save()

            # 5. 旧リソースの物理削除(成功時のみ実行)
            if old_resources:
                self.storage_service.delete_resources(old_resources)

            return log_comment
        except Exception as e:
            # 失敗時に、今回新しく作成したリソースをロールバック(物理削除)
            self.storage_service.delete_resources(new_resources)
            raise e

    # ------------------------------------------------------------------
    # 削除系サービス
    # ------------------------------------------------------------------
    # ログ削除
    def delete_log(
        self, 
        date_now: datetime, 
        kino_id: str, 
        user: M_User, 
        log_id: str,
    ):
        """ログを論理削除する"""
         # 1. ログの取得(存在チェックとロック)
        # SELECT * FROM t_log WHERE id = '...' FOR UPDATE; を実行し、トランザクション中のロックを取得する
        # 「数値を増減させる」「設定を書き換える」など、同時に実行されるとデータが矛盾してしまう可能性がある更新処理の直前に使う
        try:
            log = T_Log.objects.select_for_update().get(
                id=log_id,
                user=user,
                deleted_at__isnull=True,
            )
        except T_Log.DoesNotExist:
            raise LogNotFoundError()
        
        # 2. タグの紐付け削除
        self.tag_service.remove_all_tags(
            item_type=R_ItemTag.ItemType.LOG,
            item_id=log.id,
        )

        # 3. リアクションの紐付け削除
        R_LogReaction.objects.filter(
            log=log,
            deleted_at__isnull=True,
        ).delete()

        # 4. コメントに関連するデータの論理削除
        comments = T_LogComment.objects.filter(
            log=log,
            deleted_at__isnull=True,
        )
        comment_ids = list(comments.values_list("id", flat=True))
        
        # 物理削除用にリソースを保持
        comment_resources = []
        if comment_ids:
            comment_resources = [
                rel.file_resource 
                for rel in R_LogCommentAttachment.objects.filter(log_comment_id__in=comment_ids, deleted_at__isnull=True).select_related("file_resource")
                if rel.file_resource
            ]

            # 4-1. コメントのリアクション削除
            R_LogCommentReaction.objects.filter(
                log_comment_id__in=comment_ids,
                deleted_at__isnull=True,
            ).delete()

            # 4-2. コメント本体の論理削除
            comments.update(
                updated_by=user,
                updated_method=kino_id,
                deleted_at=date_now,
            )

        # 5. ログ自体のリソース保持(削除用)
        log_resources = [
            rel.file_resource 
            for rel in R_LogAttachment.objects.filter(log=log, deleted_at__isnull=True).select_related("file_resource")
            if rel.file_resource
        ]

        try:
            # 6. 監査用情報の更新と論理削除
            log.updated_by = user
            log.updated_method = kino_id
            log.deleted_at = date_now
            log.save()

            # 7. 添付ファイルの物理削除(成功時のみ実行)
            self.storage_service.delete_resources(comment_resources)
            self.storage_service.delete_resources(log_resources)

            return log
        except Exception as e:
            raise e

    # ログコメント削除
    def delete_log_comment(
        self, 
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_id: str,
        log_comment_id: str,
    ):
        """コメントを論理削除する"""
        # 1. ログの取得(存在チェックとロック)
        # SELECT * FROM t_log WHERE id = '...' FOR UPDATE; を実行し、トランザクション中のロックを取得する
        # 「数値を増減させる」「設定を書き換える」など、同時に実行されるとデータが矛盾してしまう可能性がある更新処理の直前に使う
        # ※コメント中はログの削除をさせない※
        try:
            log = T_Log.objects.select_for_update().get(
                id=log_id,
                user=user,
                deleted_at__isnull=True,
            )
        except T_Log.DoesNotExist:
            raise LogNotFoundError()
        
        # 2. コメントの取得(存在チェックとロック)
        # SELECT * FROM t_log WHERE id = '...' FOR UPDATE; を実行し、トランザクション中のロックを取得する
        # 「数値を増減させる」「設定を書き換える」など、同時に実行されるとデータが矛盾してしまう可能性がある更新処理の直前に使う
        try:
            log_comment = T_LogComment.objects.select_for_update().get(
                id=log_comment_id, 
                log=log,
                deleted_at__isnull=True
            )
        except T_LogComment.DoesNotExist:
            raise LogCommentNotFoundError()
        
        # 3. リアクションの紐付け削除
        R_LogCommentReaction.objects.filter(
            log_comment=log_comment,
            deleted_at__isnull=True,
        ).delete()

        # 4. 添付リソースの取得(削除用)
        old_resources = [
            rel.file_resource 
            for rel in R_LogCommentAttachment.objects.filter(log_comment=log_comment, deleted_at__isnull=True).select_related("file_resource")
            if rel.file_resource
        ]
        
        try:
            # 5. 監査用情報の更新と論理削除
            log_comment.updated_by = user
            log_comment.updated_method = kino_id
            log_comment.deleted_at = date_now
            log_comment.save()

            # 6. 添付ファイルの物理削除(成功時のみ実行)
            self.storage_service.delete_resources(old_resources)

            return log_comment
        except Exception as e:
            raise e
    
    # ------------------------------------------------------------------
    # その他サービス
    # ------------------------------------------------------------------
    # ログへのリアクション追加
    def add_log_reaction(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_id: str,
        emoji_id: str,
    ):
        """ログにリアクションを追加する"""
        # 1. ログの存在確認(存在チェックのみでロックはかけない)
        try:
            log = T_Log.objects.get(
                id=log_id,
                deleted_at__isnull=True,
            )
        except T_Log.DoesNotExist:
            raise LogNotFoundError()
        
        # 2. 絵文字マスタの存在確認(存在チェックのみでロックはかけない)
        try:
            emoji = M_Emoji.objects.get(
                id=emoji_id,
                deleted_at__isnull=True,
            )
        except M_Emoji.DoesNotExist:
            raise EmojiNotFoundError()
        
        # 3. 既存の有効なリアクションの存在確認(重複してリアクション追加しないため)
        try:
            R_LogReaction.objects.get(
                log=log,
                user=user,
                emoji=emoji,
                deleted_at__isnull=True,
            )
        except R_LogReaction.DoesNotExist:
            raise LogReactionConflictError()

        # 4. リアクションの登録
        reaction = R_LogReaction.objects.create(
            log=log,
            user=user,
            emoji=emoji,
            created_by=user,
            created_method=kino_id,
            updated_by=user,
            updated_method=kino_id,
        )
        return reaction

    # ログへのリアクション削除
    def remove_log_reaction(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_id: str,
        emoji_id: str,
    ):
        """ログからリアクションを削除(論理削除)する"""
        # 1. ログの存在確認(存在チェックのみでロックはかけない)
        try:
            log = T_Log.objects.get(
                id=log_id,
                deleted_at__isnull=True,
            )
        except T_Log.DoesNotExist:
            raise LogNotFoundError()
        
        # 2. 絵文字マスタの存在確認(存在チェックのみでロックはかけない)
        try:
            emoji = M_Emoji.objects.get(
                id=emoji_id,
                deleted_at__isnull=True,
            )
        except M_Emoji.DoesNotExist:
            raise EmojiNotFoundError()
        
        # 3. リアクションの論理削除
        count = R_LogReaction.objects.filter(
            log=log,
            user=user,
            emoji=emoji,
            deleted_at__isnull=True,
        ).update(
            updated_by=user,
            updated_method=kino_id,
            deleted_at=date_now,
        )
        return count > 0

    # ログコメントへのリアクション追加
    def add_log_comment_reaction(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_comment_id: str,
        emoji_id: str,
    ):
        """ログコメントにリアクションを追加する"""
        # 1. ログコメントの存在確認(存在チェックのみでロックはかけない)
        try:
            log_comment = T_LogComment.objects.get(
                id=log_comment_id,
                deleted_at__isnull=True,
            )
        except T_LogComment.DoesNotExist:
            raise LogCommentNotFoundError()

        # 2. 絵文字マスタの存在確認(存在チェックのみでロックはかけない)
        try:
            emoji = M_Emoji.objects.get(
                id=emoji_id,
                deleted_at__isnull=True,
            )
        except M_Emoji.DoesNotExist:
            raise EmojiNotFoundError()
        
        # 3. 既存の有効なリアクションの存在確認(重複してリアクション追加しないため)
        try:
            R_LogCommentReaction.objects.get(
                log_comment=log_comment,
                user=user,
                emoji=emoji,
                deleted_at__isnull=True,
            )
        except R_LogCommentReaction.DoesNotExist:
            raise LogCommentReactionConflictError()

        # 4. リアクションの登録
        reaction = R_LogCommentReaction.objects.create(
            log_comment=log_comment,
            user=user,
            emoji=emoji,
            created_by=user,
            created_method=kino_id,
            updated_by=user,
            updated_method=kino_id,
        )
        return reaction

    # ログコメントへのリアクション削除
    def remove_log_comment_reaction(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        log_comment_id: str,
        emoji_id: str,
    ):
        """ログコメントからリアクションを削除(論理削除)する"""
        # 1. ログコメントの存在確認(存在チェックのみでロックはかけない)
        try:
            log_comment = T_LogComment.objects.get(
                id=log_comment_id,
                deleted_at__isnull=True,
            )
        except T_LogComment.DoesNotExist:
            raise LogCommentNotFoundError()

        # 2. 絵文字マスタの存在確認(存在チェックのみでロックはかけない)
        try:
            emoji = M_Emoji.objects.get(
                id=emoji_id,
                deleted_at__isnull=True,
            )
        except M_Emoji.DoesNotExist:
            raise EmojiNotFoundError()
            
        # 3. リアクションの論理削除
        count = R_LogCommentReaction.objects.filter(
            log_comment=log_comment,
            user=user,
            emoji=emoji,
            deleted_at__isnull=True,
        ).update(
            updated_by=user,
            updated_method=kino_id,
            deleted_at=date_now,
        )
        return count > 0