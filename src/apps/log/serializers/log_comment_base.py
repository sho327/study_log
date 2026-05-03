from rest_framework import serializers

# --- アカウントモジュール ---
from apps.account.serializers.account_base import AccountMiniResponseSerializer

# --- 共通モジュール ---
from apps.common.serializers.file_resource_base import FileResourceMiniResponseSerializer

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
    user = AccountMiniResponseSerializer(source="created_by", read_only=True)

    class Meta(LogCommentBaseSerializer.Meta):
        # 画面に並べる最低限の項目に絞る
        fields = [
            "id", 
            "content", 
            "attachments",
            "user",
            "created_at",
        ]


class LogCommentFullResponseSerializer(LogCommentBaseSerializer):
    """
    【最大構成】詳細用
    """
    attachments = LogCommentAttachmentSerializer(
        source="log_r_log_comment_attachment_set", 
        many=True, 
        read_only=True
    )
    user = AccountMiniResponseSerializer(source="created_by", read_only=True)

    class Meta(LogCommentBaseSerializer.Meta):
        fields = "__all__"

