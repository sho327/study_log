from rest_framework import serializers

class LogListRequestSerializer(serializers.Serializer):
    """
    入力：フロントエンドから送られてくるデータの検品
    """
    user_id = serializers.UUIDField(required=True)
    # 複数IDを受け取るためのListField。子要素をUUIDFieldにすることで形式チェックも自動化
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="タグIDのリスト"
    )
    # ページング
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    per_page = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
