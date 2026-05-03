import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from simple_history.models import HistoricalRecords
# --- コアモジュール ---
from core.models import BaseModel

# フォローリレーション
class R_Follow(BaseModel):
    # フォロワー/ユーザマスタ(削除/物理削除の場合はCASCADE)
    follower = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="follower_id",
        verbose_name="フォロワー/ユーザマスタ",
        db_comment="フォロワー/ユーザマスタ",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: m_user_instance.profile/通常参照はt_profile_instance.user_id(_id)で取得可能)
        related_name="follower_r_follow_set",
    )
    # フォロー実行者/ユーザマスタ(削除/物理削除の場合はCASCADE)
    followee = models.ForeignKey(
        "account.M_User",  # 循環参照対策(文字で定義することで、後での紐付けとする)
        db_column="followee_id",
        verbose_name="フォロー実行者/ユーザマスタ",
        db_comment="フォロー実行者/ユーザマスタ",
        on_delete=models.CASCADE,
        # 逆参照名を定義(例: m_user_instance.profile/通常参照はt_profile_instance.user_id(_id)で取得可能)
        related_name="followee_r_follow_set",
    )

    class Meta:
        db_table = "r_follow"
        db_table_comment = "フォローリレーション"
        verbose_name = "フォローリレーション"
        verbose_name_plural = "フォローリレーション"
        constraints = [
            # アクティブな (is_active=True) かつ 未削除の (deleted_at__isnull=True) ユーザー間でのみ user_id がユニーク
            UniqueConstraint(
                fields=["follower", "followee"],
                condition=Q(deleted_at__isnull=True),
                name="unique_r_follow_follower_followee_active",
            ),
        ]
    
    def __str__(self):
        return f"{self.follower} {self.followee}"