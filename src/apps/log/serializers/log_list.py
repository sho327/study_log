from rest_framework import serializers

class LogListRequestSerializer(serializers.Serializer):
    """
    入力：フロントエンドから送られてくるデータの検品
    """
    mine = serializers.BooleanField(required=False, default=False, help_text="自分のログのみを取得するかどうか")
    date_from = serializers.DateField(required=False, help_text="開始日")
    date_to = serializers.DateField(required=False, help_text="終了日")
    # ページング
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    per_page = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)

