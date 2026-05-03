from rest_framework import serializers
import json

# --- ログモジュール ---
from apps.log.models import T_Log, M_LogTheme, M_LogCategory

class LogUpdateRequestSerializer(serializers.Serializer):
    """
    入力：フロントエンドから送られてくるデータの検品
    ※バイナリ画像を扱うため、Multipartリクエスト専用
    """
    date = serializers.DateField(required=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    content = serializers.CharField(required=False, allow_null=True)
    output_url = serializers.CharField(required=False, allow_null=True)
    
    # formDataとしてUUIDFieldで受け取り、各種validate側で個別検証を行う
    log_theme_id = serializers.UUIDField(required=False, allow_null=True)
    log_category_id = serializers.UUIDField(required=False, allow_null=True)
    # 画像はリストで受け取る
    attachment_files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_null=True,
        allow_empty=True,
    )

    def validate_log_theme_id(self, value):
        """log_theme_idを手動で検証・取得する"""
        if not value:
            return None
        
        # valueはUUIDFieldにより既にUUID化されているはず
        if not isinstance(value, uuid.UUID):
            raise serializers.ValidationError("log_theme_idはUUID形式である必要があります。")

        user = self.context['request'].user
        # IDから有効なテーマを取得
        theme = M_LogTheme.objects.filter(
            id=value, 
            user=user, 
            deleted_at__isnull=True
        ).first()
        if not theme:
            raise serializers.ValidationError("log_theme_idは有効なテーマIDである必要があります。")
        return theme
    
    def validate_log_category_id(self, value):
        """log_category_idを手動で検証・取得する"""
        if not value:
            return None
        
        # valueはUUIDFieldにより既にUUID化されているはず
        if not isinstance(value, uuid.UUID):
            raise serializers.ValidationError("log_category_idはUUID形式である必要があります。")

        user = self.context['request'].user
        # IDから有効なカテゴリを取得
        category = M_LogCategory.objects.filter(
            id=value, 
            user=user, 
            deleted_at__isnull=True
        ).first()
        if not category:
            raise serializers.ValidationError("log_category_idは有効なカテゴリIDである必要があります。")
        return category
