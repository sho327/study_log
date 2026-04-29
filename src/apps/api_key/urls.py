from django.urls import path, include
from rest_framework import routers

# --- APIキーモジュール ---
from apps.api_key.views.master_api_key_scope import M_ApiKeyScopeViewSet

app_name = "api_key"

router = routers.DefaultRouter()
router.register("master_api_key_scopes", M_ApiKeyScopeViewSet, basename='master_api_key_scopes')

urlpatterns = [
    # ViewSet関連のURL(CRUD一括)
    path('', include(router.urls)),
]