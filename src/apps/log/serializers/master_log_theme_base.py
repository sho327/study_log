from rest_framework import serializers

# --- ログモジュール ---
from apps.log.models import M_LogTheme

class MasterLogThemeBaseSerializer(serializers.ModelSerializer):
    """
    ベース定義:モデルとの紐付けだけを行う。
    直接は使わず、継承して利用する。
    """
    class Meta:
        model = M_LogTheme
        fields = "__all__" # 基本は全フィールド対象

class MasterLogThemeMiniResponseSerializer(MasterLogThemeBaseSeriali):
    """
    【最小構成】一覧用
    Metaを上書きして、IDと名称だけに絞り込む
    """
    class Meta(MasterLogThemeBaseSeriali.Meta):
        fields = [
            "id",  
            "name",
        ]

class MasterLogThemeFullResponseSerializer(MasterLogThemeBaseSeriali):
    """
    【最大構成】詳細用
    Baseの定義(__all__)をそのまま使い、モデルの変更に自動追従させる
    """
    pass