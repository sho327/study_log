from rest_framework import serializers

class InitialSettingRequestSerializer(serializers.Serializer):
    """
    入力：フロントエンドから送られてくるデータの検品
    ※バイナリ画像を扱うため、Multipartリクエスト専用
    """
    user_id_display = serializers.CharField(
        required=True,
        max_length=255,
        help_text="ユーザーID"
    )
    display_name = serializers.CharField(
        required=True,
        max_length=255,
        help_text="表示名"
    )
    bio = serializers.CharField(
        required=False,
        max_length=255,
        help_text="自己紹介"
    )
    icon = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="アイコン"
    )
