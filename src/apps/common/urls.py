# coding: utf-8
from django.urls import path, include
from rest_framework import routers

# --- 共通モジュール ---
from .views.master_emoji import M_EmojiViewSet
from .views.master_tag import M_TagViewSet

app_name = "common"

router = routers.DefaultRouter()
router.register("master_emojis", M_EmojiViewSet, basename='master_emojis')
router.register("master_tags", M_TagViewSet, basename='master_tags')

urlpatterns = [
    # ViewSet関連のURL(CRUD一括)
    path('', include(router.urls)),
]