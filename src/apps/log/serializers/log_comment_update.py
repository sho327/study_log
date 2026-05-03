from rest_framework import serializers
import json

# --- ログモジュール ---
from apps.log.models import T_LogComment

class LogCommentUpdateRequestSerializer(serializers.Serializer):
    """
    入力：フロントエンドから送られてくるデータの検品
    ※バイナリ画像を扱うため、Multipartリクエスト専用
    ※Serializer生成時に、context={'log_id': log_id}を設定することが必須
    """
    def __init__(self, *args, **kwargs):
        # 親クラスの__init__を呼び出す
        super().__init__(*args, **kwargs)
        
        # contextからlog_idを取得
        log_id = kwargs.get('context', {}).get('log_id')
        
        if not log_id:
            raise ValueError("LogCommentCreateRequestSerializer は context['log_id'] が必須です")
        
        # log_idを使った処理や属性設定を行う場合
        # self.log_id = log_id

    content = serializers.CharField(required=False, allow_null=True)

    # formDataとしてUUIDFieldで受け取り、各種validate側で個別検証を行う
    reply_to_id = serializers.UUIDField(required=False, allow_null=True)
    # 画像はリストで受け取る
    attachment_files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_null=True,
        allow_empty=True,
    )

    def validate_reply_to_id(self, value):
        """reply_to_idを手動で検証・取得する"""
        if not value:
            return None
        
        # valueはUUIDFieldにより既にUUID化されているはず
        if not isinstance(value, uuid.UUID):
            raise serializers.ValidationError("reply_to_idはUUID形式である必要があります。")

        # IDからコメントを取得
        reply_to = T_LogComment.objects.filter(
            id=value,
            log_id=self.context['log_id'],
            deleted_at__isnull=True
        ).first()
        if not reply_to:
            raise serializers.ValidationError("reply_to_idは有効なコメントIDである必要があります。")
        return reply_to
