from rest_framework import serializers

# --- APIキーモジュール ---
from apps.api_key.serializers.api_key_base import ApiKeyFullResponseSerializer
from apps.api_key.models import M_ApiKeyScope, T_ApiKey


class ApiKeyCreateRequestSerializer(serializers.Serializer):
    """
    入力：フロントエンドから送られてくるデータの検品
    """
    name = serializers.CharField(
        max_length=64,
        required=True,
    )
    description = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
    )
    duration_days = serializers.IntegerField(
        required=True,
        min_value=1,
    )

    # ※PrimaryKeyRelatedFieldを利用
    # serializers.PrimaryKeyRelatedFieldのqueryset にフィルタをかけている場合、
    # DRFはバリデーション時(is_valid()実行時)に以下の挙動を行う
    # 1. DB問い合わせ: 送られてきたIDが、指定されたqueryset内に既に存在するか確認(論理削除も考慮)
    # 2. 自動エラー応答: 存在しない(または論理削除済み)IDだった場合、DRFは自動的に「400 Bad Request」を返す
    scope_ids = serializers.PrimaryKeyRelatedField(
        queryset=M_ApiKeyScope.objects.filter(deleted_at__isnull=True),
        many=True,
        required=True,
    )

class ApiKeyCreateResponseSerializer(ApiKeyFullResponseSerializer):
    """
    出力：フロントエンドに返すデータのフォーマット
    ※シークレットキーを返すために継承＋フィールド追加
    """
    raw_secret_key = serializers.CharField(read_only=True)
