from django.urls import path, include
from rest_framework import routers

# --- APIキーモジュール ---
from apps.api_key.views.master_api_key_scope import M_ApiKeyScopeViewSet
from apps.api_key.views.api_key_list import ApiKeyListView
from apps.api_key.views.api_key_detail import ApiKeyDetailView
from apps.api_key.views.api_key_create import ApiKeyCreateView
from apps.api_key.views.api_key_update import ApiKeyUpdateView
from apps.api_key.views.api_key_delete import ApiKeyDeleteView

app_name = "api_key"

router = routers.DefaultRouter()
router.register("master_api_key_scopes", M_ApiKeyScopeViewSet, basename='master_api_key_scopes')

urlpatterns = [
    # ViewSet関連のURL(CRUD一括)
    path('', include(router.urls)),
    # 個別APIキー関連
    path('list/', ApiKeyListView.as_view(), name='api_key_list'),
    path('create/', ApiKeyCreateView.as_view(), name='api_key_create'),
    path('<uuid:api_key_id>/', ApiKeyDetailView.as_view(), name='api_key_detail'),
    path('<uuid:api_key_id>/update/', ApiKeyUpdateView.as_view(), name='api_key_update'),
    path('<uuid:api_key_id>/delete/', ApiKeyDeleteView.as_view(), name='api_key_delete'),
]