import os
import uuid
from pathlib import Path
from django.conf import settings
from typing import Any, BinaryIO, List, Optional, Union

# --- コアモジュール ---
from core.consts import LOG_METHOD
from core.utils.log_helpers import log_output_by_msg_id
from core.exceptions.exceptions import ExternalServiceError

# --- 共通モジュール ---
from apps.common.models import T_FileResource


class StorageService:
    def __init__(self):
        # settings.py の MEDIA_ROOT を使用する
        self.base_path = Path(settings.MEDIA_ROOT)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_file(
        self, 
        file_data: BinaryIO, 
        folder_path: str, 
        original_filename: str
    ) -> Optional[str]:
        try:
            # 拡張子の取得 (.png, .jpg など)
            extension = os.path.splitext(original_filename)[1]
            # UUIDで新しいファイル名を生成
            new_filename = f"{uuid.uuid4()}{extension}"

            target_dir = self.base_path / folder_path
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / new_filename
            
            # デバッグログ出力
            log_output_by_msg_id(
                log_id="MSGD001",
                params=[f"DEBUG: ファイルがアップロードされます。 保存先パス: {file_path.absolute()}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )

            # 保存
            with open(file_path, "wb") as f:
                # file_dataがInMemoryUploadedFileの場合はread()で取得
                f.write(file_data.read())

            # DB保存用のパスを返す
            return f"{folder_path}/{new_filename}"

        except Exception as e:
            # エラーログ出力
            log_output_by_msg_id(
                log_id="MSGE001",
                params=[f"ファイルの保存に失敗しました。 error: {str(e)}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            raise ExternalServiceError()

    def delete_file(
        self, 
        file_url: str
    ) -> bool:
        try:
            # 1. URLパス(相対パス)から Path オブジェクトを作成
            # 念のため '/' を取り除く
            relative_path = Path(file_url.lstrip("/"))
            
            # 2. base_path を結合して絶対パス(または正しい相対パス)を生成
            file_path = self.base_path / relative_path

            # デバッグログ出力
            log_output_by_msg_id(
                log_id="MSGD001",
                params=[f"DEBUG: ファイルが削除されます。 削除対象パス: {file_path.absolute()}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            
            if file_path.exists():
                os.remove(file_path)
                return True
            
            # 警告ログ出力
            log_output_by_msg_id(
                log_id="MSGW001",
                params=[f"削除対象ファイルが存在しませんでした。(ファイルを削除せず処理は続行されます。) 削除対象パス: {file_path.absolute()}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            return False
        except Exception as e:
            # エラーログ出力
            log_output_by_msg_id(
                log_id="MSGE001",
                params=[f"ファイルの削除に失敗しました。 error: {str(e)}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            raise ExternalServiceError()

    def upload_resource(
        self,
        user: Any,
        kino_id: str,
        file_obj: Any,
        folder_path: str,
        file_type: str = T_FileResource.FileType.OTHER,
        file_name: Optional[str] = None,
    ) -> T_FileResource:
        """単一ファイルをアップロードし、T_FileResourceを作成して返す"""
        path = self.upload_file(
            file_data=file_obj,
            folder_path=folder_path,
            original_filename=file_obj.name,
        )
        if not path:
            # エラーログ出力
            log_output_by_msg_id(
                log_id="MSGE001",
                params=[f"ファイルのアップロードに失敗しました。"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            raise ExternalServiceError()

        try:
            resource = T_FileResource.objects.create(
                file_type=file_type,
                file=path,
                file_name=file_name or file_obj.name,
                file_size=file_obj.size,
                created_by=user,
                created_method=kino_id,
                updated_by=user,
                updated_method=kino_id,
            )
            return resource
        except Exception as e:
            # エラーログ出力
            log_output_by_msg_id(
                log_id="MSGE001",
                params=[f"ファイルリソースの登録に失敗しました。 error: {str(e)}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            # DB作成失敗時は、アップロードした物理ファイルを削除
            self.delete_file(path)
            raise e

    def upload_resources(
        self,
        user: Any,
        kino_id: str,
        files: List[Any],
        folder_path: str,
        file_type: str = T_FileResource.FileType.OTHER,
        file_name_prefix: str = "file",
    ) -> List[T_FileResource]:
        """複数ファイルをアップロードし、T_FileResourceのリストを返す。一つでも失敗したらアップロード済みのファイルを全削除。"""
        resources = []
        uploaded_paths = []
        try:
            for index, file_obj in enumerate(files):
                path = self.upload_file(
                    file_data=file_obj,
                    folder_path=folder_path,
                    original_filename=file_obj.name,
                )
                if not path:
                    # エラーログ出力
                    log_output_by_msg_id(
                        log_id="MSGE001",
                        params=[f"アップロードされたファイルのうち、一部のファイルの保存に失敗しました。 ファイル名: {file_obj.name}"],
                        logger_name=LOG_METHOD.APPLICATION.value,
                    )
                    raise ExternalServiceError()
                uploaded_paths.append(path)
                resource = T_FileResource.objects.create(
                    file_type=file_type,
                    file=path,
                    file_name=f"{file_name_prefix}_{index}",
                    file_size=file_obj.size,
                    created_by=user,
                    created_method=kino_id,
                    updated_by=user,
                    updated_method=kino_id,
                )
                resources.append(resource)
            return resources
        except Exception as e:
            # エラーログ出力
            log_output_by_msg_id(
                log_id="MSGE001",
                params=[f"ファイルの保存 または DB登録に失敗しました。 error: {str(e)}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            # 途中で失敗した場合は、今回のループで保存した物理ファイルをすべて削除
            for path in uploaded_paths:
                self.delete_file(path)
            raise e

    def delete_resources(
        self, 
        resources: Union[List[T_FileResource], Any]
    ) -> None:
        """T_FileResourceのリスト(QuerySet等)を受け取り、実ファイルとレコードを両方削除する"""
        if not resources:
            return

        # QuerySet等の場合はリスト化
        if not isinstance(resources, list):
            resources = list(resources)

        # 1. 実ファイルのパスを収集
        file_paths = [r.file.name for r in resources if r.file]

        # 2. レコードの物理削除(CASCADE設定により、中間テーブルのリレーションも削除される)
        resource_ids = [r.id for r in resources]
        T_FileResource.objects.filter(
            id__in=resource_ids,
        ).delete()

        # 3. 実ファイルの物理削除
        for path in file_paths:
            self.delete_file(path)
