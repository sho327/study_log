from collections import defaultdict
from datetime import datetime

from django.utils import timezone

# --- アカウントモジュール ---
from apps.account.models import M_User
from apps.artist.exceptions import ArtistAlreadyExistsError, ArtistNotFoundError

# --- APIキーモジュール ---
from apps.api_key.models import T_ApiKey

# --- 共通モジュール ---
from apps.common.models import T_FileResource
from core.consts import LOG_METHOD
from core.exceptions.exceptions import ApplicationError
from core.utils.log_helpers import log_output_by_msg_id

class ApiKeyService:
    """
    APIキーの登録/更新/管理を行うサービスクラス
    """

    # ------------------------------------------------------------------
    # 一覧取得系サービス
    # ------------------------------------------------------------------
    # APIキー一覧取得
    def list_api_key(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
    ):
        """
        APIキー一覧取得
        """
        # 1. 基本クエリ(自分かつ未削除)
        queryset = T_Artist.objects.filter(
            user=user, 
            deleted_at__isnull=True
        )
        # 2. ソート
        return queryset.order_by("-created_at")

    # ------------------------------------------------------------------
    # 登録系サービス
    # ------------------------------------------------------------------
    # APIキー登録
    def create_api_key(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        validated_data,
    ):
        """APIキーを新規登録する"""
        # 1. 重複チェック(論理削除されていない同一SpotifyIDがないか)
        if T_Artist.objects.filter(
            user=user,
            spotify_id=validated_data["spotify_id"],
            deleted_at__isnull=True,
        ).exists():
            raise ArtistAlreadyExistsError()

        # 関連マスタの存在チェック
        # ※コンテキスト、タグに関してはシリアライザ(PrimaryKeyRelatedField)にて存在チェック済みのため不要

        # 2. 画像リソース(T_FileResource)の作成
        spotify_image = None
        if validated_data.get("icon_url"):
            spotify_image = T_FileResource.objects.create(
                file_type=T_FileResource.FileType.IMAGE,
                external_url=validated_data["icon_url"],
                file_name=f"spotify_{validated_data['spotify_name']}_image_{date_now.strftime('%Y%m%d')}",
                created_by=user,
                created_method=kino_id,
                updated_by=user,
                updated_method=kino_id,
            )

        # 3. 外部ID(MBID/DeezerID)の取得処理(名寄せ)
        linked_ids = self._link_external_ids(
            name=validated_data["spotify_name"],
            spotify_id=validated_data["spotify_id"]
        )

        # 4. アーティスト本体の作成
        artist = T_Artist.objects.create(
            user=user,
            spotify_id=validated_data["spotify_id"],
            spotify_name=validated_data["spotify_name"],
            display_name=validated_data["display_name"],
            external_icon=spotify_image,
            deezer_id=linked_ids["deezer_id"],
            is_deezer_autoset=linked_ids["is_deezer_autoset"],
            # lastfmの取得はパフォーマンスと要調整(取得をコメントアウト)したいので、「.get()」で最悪Noneで登録させる
            lastfm_name=linked_ids.get("lastfm_name"),
            mbid=linked_ids["mbid"],
            is_mbid_autoset=linked_ids["is_mbid_autoset"],
            # validated_data['context_id'] は既にモデルインスタンスになっている
            context=validated_data.get("context_id"),
            created_by=user,
            created_method=kino_id,
            updated_by=user,
            updated_method=kino_id,
        )

        # 5. タグの紐付け(中間テーブルR_ArtistTagの作成)
        tags = validated_data.get("tag_ids", [])
        if tags:
            tag_links = [
                R_ArtistTag(
                    artist=artist,
                    tag=tag,
                    created_by=user,
                    created_method=kino_id,
                    updated_by=user,
                    updated_method=kino_id,
                )
                for tag in tags
            ]
            R_ArtistTag.objects.bulk_create(tag_links)

        return artist

    # ------------------------------------------------------------------
    # 更新系サービス
    # ------------------------------------------------------------------
    # アーティスト更新
    def update_artist(
        self,
        date_now: datetime,
        kino_id: str,
        user: M_User,
        artist_id,
        validated_data,
    ):
        """アーティストを新規登録する"""
        # 1. 対象の取得(存在チェック)
        try:
            artist: T_Artist = T_Artist.objects.select_for_update().get(
                id=artist_id, user=user, deleted_at__isnull=True
            )
        except T_Artist.DoesNotExist:
            raise ArtistNotFoundError()

        # 2. その他のフィールド更新 
        if "mbid" in validated_data:
            artist.mbid = validated_data["mbid"]
            artist.is_mbid_autoset = False
        
        if "deezer_id" in validated_data:
            artist.deezer_id = validated_data["deezer_id"]
            artist.is_deezer_autoset = False

        if "context_id" in validated_data:
            artist.context = validated_data["context_id"]

        artist.updated_method = kino_id
        artist.updated_by = user
        artist.save()

        # 3. タグの更新(洗替方式)
        if "tag_ids" in validated_data:  # validated_dataに含まれているときのみ更新
            # 既存の紐付けを物理削除(中間テーブルなので物理削除)
            R_ArtistTag.objects.filter(artist=artist).delete()

            # 新しいタグを登録
            tags = validated_data["tag_ids"]
            if tags:
                tag_links = [
                    R_ArtistTag(
                        artist=artist,
                        tag=tag,
                        created_by=user,
                        created_method=kino_id,
                        updated_by=user,
                        updated_method=kino_id,
                    )
                    for tag in tags
                ]
                R_ArtistTag.objects.bulk_create(tag_links)

        return artist

    # ------------------------------------------------------------------
    # 削除系サービス
    # ------------------------------------------------------------------
    # アーティスト削除
    def delete_artist(
        self, 
        date_now: datetime, 
        kino_id: str, 
        user: M_User, 
        artist_id
    ):
        """アーティストを論理削除する"""
        # 1. 対象の取得
        # 自分のデータ かつ すでに削除されていないものを対象にする
        try:
            artist: T_Artist = T_Artist.objects.select_for_update().get(
                id=artist_id, user=user, deleted_at__isnull=True
            )
        except T_Artist.DoesNotExist:
            raise ArtistNotFoundError()

        # 2. 紐付いている画像の論理削除
        # external_icon(ForeignKey)が存在する場合、そのレコードも論理削除する
        if artist.external_icon:
            image_res = artist.external_icon
            image_res.updated_by = user
            image_res.updated_method = kino_id
            image_res.deleted_at = date_now
            image_res.save()

        # 3. アーティスト本体の論理削除処理
        # deleted_at を入れることで、以降のfilter(deleted_at__isnull=True)から除外される
        artist.updated_by = user
        artist.updated_method = kino_id
        artist.deleted_at = date_now
        artist.save()

        # 4. タグの更新(中間テーブルは物理削除)
        # カスケード削除されない中間テーブルのレコードを掃除
        R_ArtistTag.objects.filter(artist=artist).delete()
