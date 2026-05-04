from rest_framework import serializers

# --- アカウントモジュール ---
from apps.account.serializers.account_base import UserMiniResponseSerializer

# --- 共通モジュール ---
from apps.common.models import M_Emoji
from apps.common.serializers.file_resource_base import FileResourceMiniResponseSerializer
from apps.common.serializers.master_emoji_base import MasterEmojiMiniResponseSerializer

# --- ログモジュール ---
from apps.log.models import T_LogComment


class LogCommentBaseSerializer(serializers.ModelSerializer):
    """
    ベース定義：ログコメント用。
    """
    class Meta:
        model = T_LogComment
        fields = "__all__"


class LogCommentAttachmentSerializer(serializers.Serializer):
    """
    ログコメント添付ファイル変換用（中間テーブル R_LogCommentAttachment を介して FileResource を返す）
    """
    def to_representation(self, instance):
        if not instance.file_resource:
            return None
        return FileResourceMiniResponseSerializer(instance.file_resource, context=self.context).data


class LogCommentReactionCountSerializer(serializers.Serializer):
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


class LogCommentMiniResponseSerializer(LogCommentBaseSerializer):
    """
    【最小構成】ログコメント一覧用
    表示項目を最小限に絞る
    """
    # 外部キー対象のリソース情報を展開
    attachments = LogCommentAttachmentSerializer(
        source="log_r_log_comment_attachment_set", 
        many=True, 
        read_only=True
    )
    # 投稿者情報
    user = UserMiniResponseSerializer(read_only=True)

    # リアクション集計
    # シリアライザで計算するとN+1問題で重くなるため、ReadOnlyFieldとして定義し
    # サービス層/ビュー層で .annotate() により付与された値を表示する設計とする
    reaction_counts = serializers.SerializerMethodField()

    class Meta(LogCommentBaseSerializer.Meta):
        # 画面に並べる最低限の項目に絞る
        fields = [
            "id", 
            "content", 
            "attachments",
            "user",
            "reaction_counts",
            "created_at",
        ]

    def get_reaction_counts(self, obj):
        """プリフェッチされたデータをメモリ上で集計する(N+1対策)"""
        # Prefetchにより、既に全件ロードされていることを前提とする
        reactions = obj.log_r_log_comment_reaction_set.all()
        counts = {}
        for r in reactions:
            emoji_id = str(r.emoji_id)
            counts[emoji_id] = counts.get(emoji_id, 0) + 1
        data = [
            {"emoji_id": emoji_id, "count": count} 
            for emoji_id, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
        # LogCommentReactionCountSerializer を使って絵文字情報を展開（コンテキストキャッシュが効く）
        return LogCommentReactionCountSerializer(data, many=True, context=self.context).data


class LogCommentFullResponseSerializer(LogCommentBaseSerializer):
    """
    【最大構成】詳細用
    """
    attachments = LogCommentAttachmentSerializer(
        source="log_r_log_comment_attachment_set", 
        many=True, 
        read_only=True
    )
    user = UserMiniResponseSerializer(read_only=True)

    # リアクション集計
    # シリアライザで計算するとN+1問題で重くなるため、ReadOnlyFieldとして定義し
    # サービス層/ビュー層で .annotate() により付与された値を表示する設計とする
    reaction_counts = serializers.SerializerMethodField()

    class Meta(LogCommentBaseSerializer.Meta):
        fields = "__all__"

    def get_reaction_counts(self, obj):
        """プリフェッチされたデータをメモリ上で集計する(N+1対策)"""
        # Mini側と同じロジックを使用
        return LogCommentMiniResponseSerializer.get_reaction_counts(self, obj)
