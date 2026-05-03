from rest_framework import serializers

# --- アカウントモジュール ---
from apps.account.serializers.account_base import AccountMiniResponseSerializer

# --- 共通モジュール ---
from apps.common.models import M_Emoji
from apps.common.serializers.file_resource_base import FileResourceMiniResponseSerializer
from apps.common.serializers.master_tag_base import MasterTagMiniResponseSerializer
from apps.common.serializers.master_emoji_base import MasterEmojiMiniResponseSerializer

# --- ログモジュール ---
from apps.log.models import T_Log
from apps.log.serializers.master_log_theme_base import MasterLogThemeMiniResponseSerializer
from apps.log.serializers.master_log_category_base import MasterLogCategoryMiniResponseSerializer


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
        # emoji_id からマスター情報を取得して展開
        emoji = M_Emoji.objects.filter(id=obj["emoji_id"]).first()
        if not emoji:
            return None
        return MasterEmojiMiniResponseSerializer(emoji, context=self.context).data


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
    tags = MasterTagMiniResponseSerializer(many=True, read_only=True)
    
    # 投稿者情報
    user = AccountMiniResponseSerializer(read_only=True)

    # 集計情報の展開 (モデルのpropertyを使用)
    comment_count = serializers.IntegerField(read_only=True)
    reaction_counts = LogReactionCountSerializer(many=True, read_only=True)

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
    tags = MasterTagMiniResponseSerializer(many=True, read_only=True)
    
    # 投稿者情報
    user = AccountMiniResponseSerializer(read_only=True)

    # 集計情報の展開
    comment_count = serializers.IntegerField(read_only=True)
    reaction_counts = LogReactionCountSerializer(many=True, read_only=True)

    class Meta(LogBaseSerializer.Meta):
        fields = "__all__"

