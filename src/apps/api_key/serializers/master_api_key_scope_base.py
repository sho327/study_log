from rest_framework import serializers

# --- APIキーモジュール ---
from apps.api_key.models import M_ApiKeyScope

class MasterApiKeyScopeBaseSerializer(serializers.ModelSerializer):
    """
    ベース定義：モデルとの紐付けだけを行う。
    直接は使わず、継承して利用する。
    """
    class Meta:
        model = M_ApiKeyScope
        fields = "__all__" # 基本は全フィールド対象

class MasterApiKeyScopeMiniResponseSerializer(MasterApiKeyScopeBaseSerializer):
    """
    【最小構成】一覧用
    Metaを上書きして、IDと名称だけに絞り込む
    """
    class Meta(MasterApiKeyScopeBaseSerializer.Meta):
        fields = [
            "id",  
            "code", 
            "name",
        ]

class MasterApiKeyScopeFullResponseSerializer(MasterApiKeyScopeBaseSerializer):
    """
    【最大構成】詳細用
    Baseの定義（__all__）をそのまま使い、モデルの変更に自動追従させる
    """
    pass
