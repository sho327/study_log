from rest_framework import serializers
from django.db.models import Sum

# --- 共通モジュール ---
from apps.common.serializers.file_resource_base import FileResourceMiniResponseSerializer

# --- アカウントモジュール ---
from apps.account.models import M_User, T_Profile


class UserBaseSerializer(serializers.ModelSerializer):
    """
    ベース定義：モデルとの紐付けだけを行う。
    """
    class Meta:
        model = M_User
        fields = "__all__"

class ProfileBaseSerializer(serializers.ModelSerializer):
    """
    ベース定義：モデルとの紐付けだけを行う。
    """
    class Meta:
        model = T_Profile
        fields = "__all__"

# ---------------------------------------------------------
# T_Profile
# ---------------------------------------------------------
class ProfileFullResponseSerializer(ProfileBaseSerializer):
    """
    プロフィールの全情報を返す役割（プロフィール編集画面や詳細画面用）
    """
    status_display = serializers.CharField(source='get_status_code_display', read_only=True)

    class Meta(ProfileBaseSerializer.Meta):
        fields = [
            "user_id_display",
            "display_name",
            "bio",
            "icon",
            "is_setup_completed",
            "status_code",
            "status_display",
        ]

# ---------------------------------------------------------
# M_User
# ---------------------------------------------------------
class UserMeResponseSerializer(UserBaseSerializer):
    """
    【自分専用】ログイン直後の初期データ等
    """
    profile = ProfileFullResponseSerializer(source="user_t_profile_set", read_only=True)
    
    class Meta(UserBaseSerializer.Meta):
        fields = [
            "id",
            "email",
            "last_login",
            "is_active",
            "is_staff",
            "is_superuser",
            "profile",
        ]

class UserMiniResponseSerializer(UserBaseSerializer):
    """
    【最小構成】フォローリストや検索結果などで使用
    ※ProfileMiniを用意しない代わりにフィールドを直接指定
    """
    display_name = serializers.CharField(source="user_t_profile_set.display_name", read_only=True)
    user_id_display = serializers.CharField(source="user_t_profile_set.user_id_display", read_only=True)
    icon_url = serializers.SerializerMethodField()

    class Meta(UserBaseSerializer.Meta):
        fields = [
            "id",
            "user_id_display",
            "display_name",
            "icon_url",
        ]

    def get_icon_url(self, obj):
        # OneToOneField(T_Profile)のアイコンURLを取得
        profile = getattr(obj, "user_t_profile_set", None)
        if profile and profile.icon:
            return profile.icon.url
        return None

class UserFullResponseSerializer(UserBaseSerializer):
    """
    他人のプロフィール詳細表示用
    """
    profile = ProfileFullResponseSerializer(source="user_t_profile_set", read_only=True)
    
    # サービス層でannotateして付与する想定（N+1回避）
    follow_count = serializers.ReadOnlyField()
    follower_count = serializers.ReadOnlyField()
    is_following = serializers.ReadOnlyField() # 閲覧ユーザーがフォロー中か

    class Meta(UserBaseSerializer.Meta):
        fields = [
            "id",
            "profile",
            "follow_count",
            "follower_count",
            "is_following",
        ]



