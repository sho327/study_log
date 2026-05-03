from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

# --- アカウントモジュール ---
from apps.account.urls import router as account_router

# --- 共通モジュール ---
from apps.common.urls import router as common_router

# --- APIキーモジュール ---
from apps.api_key.urls import router as api_key_router

BASE_API_PATH = "api/v1"

urlpatterns = [
    # admin関連機能
    path("admin/", admin.site.urls),
    # アカウント機能
    path(f"{BASE_API_PATH}/accounts/", include(account_router.urls)),
    path(f"{BASE_API_PATH}/accounts/", include("apps.account.urls")),
    # 共通機能
    path(f"{BASE_API_PATH}/common/", include(common_router.urls)),
    path(f"{BASE_API_PATH}/common/", include("apps.common.urls")),
    # APIキー機能
    path(f"{BASE_API_PATH}/api-keys/", include(api_key_router.urls)),
    path(f"{BASE_API_PATH}/api-keys/", include("apps.api_key.urls")),
]

# 開発環境のみ、メディアファイルを配信する設定を追加
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
