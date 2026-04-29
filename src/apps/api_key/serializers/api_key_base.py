from rest_framework import serializers

# --- APIキーモジュール ---
from apps.api_key.models import T_ApiKey
from apps.api_key.serializers.master_api_key_scope_base import MasterApiKeyScopeMiniResponseSerializer

class ApiKeyBaseSerializer(serializers.ModelSerializer):
    """
    ベース定義：モデルとの紐付けだけを行う。
    直接は使わず、継承して利用する。
    """
    class Meta:
        model = T_ApiKey
        fields = "__all__" # 基本は全フィールド対象

class ApiKeyMiniResponseSerializer(ApiKeyBaseSerializer):
    """
    【最小構成】一覧用
    Metaを上書きして、IDと名称だけに絞り込む
    """
    class Meta(ApiKeyBaseSerializer.Meta):
        fields = [
            "id", 
            "name"
        ]

class ApiKeyFullResponseSerializer(ApiKeyBaseSerializer):
    """
    【最大構成】詳細用
    基本モデルの全フィールド。
    ただし、外部キー先のIDだけでなく中身(オブジェクト)を返したい項目だけ上書き。
    """

    # Mini系のシリアライザを再利用し中身を展開
    scopes = MasterApiKeyScopeMiniResponseSerializer(many=True, read_only=True)

    class Meta(ApiKeyBaseSerializer.Meta):
        # Baseの fields = '__all__' を継承。
        # 上記で定義したscopesは自動的にこの「__all__」の中で差し替わる。
        depth = 0  # 勝手な展開を防ぐため0を推奨。展開は上記のように明示的に書く。
