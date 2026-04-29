from rest_framework import serializers

# --- APIキーモジュール ---
from apps.api_key.models import M_ApiKeyScope, T_ApiKey


class ApiKeyUpdateRequestSerializer(serializers.Serializer):
    """
    入力：フロントエンドから送られてくるデータの検品
    """
    name = serializers.CharField(
        max_length=64,
        required=False,
    )
    description = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
    )
    duration_days = serializers.IntegerField(
        required=False, 
        default=365, 
        min_value=1,
    )
    is_active = serializers.BooleanField(
        required=False,
        default=True,
    )
    revoked_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    revoked_detail = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    # ※PrimaryKeyRelatedFieldを利用
    # serializers.PrimaryKeyRelatedFieldのqueryset にフィルタをかけている場合、
    # DRFはバリデーション時(is_valid()実行時)に以下の挙動を行う
    # 1. DB問い合わせ: 送られてきたIDが、指定されたqueryset内に既に存在するか確認(論理削除も考慮)
    # 2. 自動エラー応答: 存在しない(または論理削除済み)IDだった場合、DRFは自動的に「400 Bad Request」を返す
    scope_ids = serializers.PrimaryKeyRelatedField(
        queryset=M_ApiKeyScope.objects.filter(deleted_at__isnull=True),
        many=True,
        required=False,
    )

    def validate_revoked_reason(self, value):
        """
        is_activeがFalse(無効)の場合、無効化理由の選択肢として正しいものが設定されているか
        """
        if self.initial_data.get("is_active") is False and not value:
            raise serializers.ValidationError("無効化理由を選択してください。")
        elif self.initial_data.get("is_active") is False and value not in T_ApiKey.RevokedReason.values:
            raise serializers.ValidationError("無効化理由が不正です。")
        return value

