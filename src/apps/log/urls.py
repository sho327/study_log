from django.urls import path, include
from rest_framework import routers

from .views.log_list import LogListView
from .views.master_log_theme import M_LogThemeViewSet
from .views.master_log_category import M_LogCategoryViewSet

app_name = "log"

router = routers.DefaultRouter()
router.register("master-log-themes", M_LogThemeViewSet, basename="master-log-theme")
router.register("master-log-categories", M_LogCategoryViewSet, basename="master-log-category")

urlpatterns = [
    # ViewSet関連のURL(CRUD一括)
    path("", include(router.urls)),
    # 個別ログ関連
    path("list/", LogListView.as_view(), name="log-list"),
]
