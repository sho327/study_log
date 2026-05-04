from rest_framework import serializers

# --- アカウントモジュール ---
from apps.account.serializers.account_base import UserMiniResponseSerializer

# --- 共通モジュール ---
from apps.common.models import M_Emoji
from apps.common.serializers.file_resource_base import FileResourceMiniResponseSerializer
from apps.common.serializers.master_tag_base import MasterTagMiniResponseSerializer
from apps.common.serializers.master_emoji_base import MasterEmojiMiniResponseSerializer

# --- ログモジュール ---
from apps.log.models import T_Log
from apps.log.serializers.master_log_theme_base import MasterLogThemeMiniResponseSerializer
from apps.log.serializers.master_log_category_base import MasterLogCategoryMiniResponseSerializer
from apps.log.serializers.log_comment_base import LogCommentMiniResponseSerializer


class LogBaseSerializer(serializers.ModelSerializer):
    """
    ベース定義：ログ用。
    """
    class Meta:
        model = T_Log
        fields = "__all__"


class LogAttachmentSerializer(serializers.Serializer):
    """
    ログ添付ファイル変換用（中間テーブル R_LogAttachment を介して FileResource を返す）
    """
    def to_representation(self, instance):
        if not instance.file_resource:
            return None
        return FileResourceMiniResponseSerializer(instance.file_resource, context=self.context).data


class LogReactionCountSerializer(serializers.Serializer):
    """
    リアクション集計結果のシリアライズ用
    """
    emoji = serializers.SerializerMethodField()
    count = serializers.IntegerField()

    def get_emoji(self, obj):
        # シリアライザのコンテキストを利用して、一度取得した絵文字情報を使い回す(N+1対策)
        emojis = self.context.get('_emoji_cache')
        if emojis is None:
            # 初回のみ全件取得してコンテキストに保持(削除されていないもの)
            emojis = {str(e.id): e for e in M_Emoji.objects.filter(deleted_at__isnull=True)}
            self.context['_emoji_cache'] = emojis
        emoji_instance = emojis.get(str(obj["emoji_id"]))
        if not emoji_instance:
            return None
        return MasterEmojiMiniResponseSerializer(emoji_instance, context=self.context).data


class LogMiniResponseSerializer(LogBaseSerializer):
    """
    【最小構成】ログ一覧用
    表示項目を最小限に絞る
    """
    # マスター情報の展開
    log_theme = MasterLogThemeMiniResponseSerializer(read_only=True)
    log_category = MasterLogCategoryMiniResponseSerializer(read_only=True)
    
    # 添付ファイルの展開
    attachments = LogAttachmentSerializer(
        source="log_r_log_attachment_set", 
        many=True, 
        read_only=True
    )
    
    # タグの展開(モデルのpropertyを使用)
    # サービス層で手動プリフェッチ(prefetched_tags)されている場合はそれを利用する
    tags = serializers.SerializerMethodField()
    
    # 投稿者情報
    user = UserMiniResponseSerializer(read_only=True)

    # 集計情報の展開
    # シリアライザで計算するとN+1問題で重くなるため、ReadOnlyFieldとして定義し
    # サービス層/ビュー層で .annotate() により付与された値を表示する設計とする
    comment_count = serializers.ReadOnlyField() 
    # サービス層で .prefetch_related("log_r_reaction_set") される想定
    reaction_counts = serializers.SerializerMethodField()

    class Meta(LogBaseSerializer.Meta):
        fields = [
            "id", 
            "date",
            "duration",
            "content",
            "log_theme",
            "log_category",
            "attachments",
            "tags",
            "user",
            "comment_count",
            "reaction_counts",
            "created_at",
        ]

    def get_tags(self, obj):
        """手動プリフェッチされたタグを優先的に返す"""
        tags = getattr(obj, "prefetched_tags", obj.tags)
        return MasterTagMiniResponseSerializer(tags, many=True, context=self.context).data


    def get_reaction_counts(self, obj):
        """プリフェッチされたデータをメモリ上で集計する(N+1対策)"""
        # Prefetchにより、既に全件ロードされていることを前提とする
        reactions = obj.log_r_log_reaction_set.all()
        counts = {}
        for r in reactions:
            emoji_id = str(r.emoji_id)
            counts[emoji_id] = counts.get(emoji_id, 0) + 1
        data = [
            {"emoji_id": emoji_id, "count": count} 
            for emoji_id, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
        # LogReactionCountSerializer を使って絵文字情報を展開（コンテキストキャッシュが効く）
        return LogReactionCountSerializer(data, many=True, context=self.context).data



class LogFullResponseSerializer(LogBaseSerializer):
    """
    【最大構成】詳細用
    """
    log_theme = MasterLogThemeMiniResponseSerializer(read_only=True)
    log_category = MasterLogCategoryMiniResponseSerializer(read_only=True)
    
    attachments = LogAttachmentSerializer(
        source="log_r_log_attachment_set", 
        many=True, 
        read_only=True
    )
    
    # タグの展開(モデルのpropertyを使用)
    tags = serializers.SerializerMethodField()
    # 投稿者情報
    user = UserMiniResponseSerializer(read_only=True)


    # 集計情報の展開
    # シリアライザで計算するとN+1問題で重くなるため、ReadOnlyFieldとして定義し
    # サービス層/ビュー層で .annotate() により付与された値を表示する設計とする
    comment_count = serializers.ReadOnlyField()
    reaction_counts = serializers.SerializerMethodField()

    # コメント一覧の展開
    # サービス層で .prefetch_related("log_t_log_comment_set") される想定
    comments = LogCommentMiniResponseSerializer(
        source="log_t_log_comment_set", 
        many=True, 
        read_only=True
    )

    class Meta(LogBaseSerializer.Meta):
        fields = "__all__"

    def get_tags(self, obj):
        """手動プリフェッチされたタグを優先的に返す"""
        return LogMiniResponseSerializer.get_tags(self, obj)

    def get_reaction_counts(self, obj):
        """プリフェッチされたデータをメモリ上で集計する(N+1対策)"""
        # Mini側と同じロジックを使用
        return LogMiniResponseSerializer.get_reaction_counts(self, obj)





