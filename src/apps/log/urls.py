from django.urls import path, include
from rest_framework import routers

from .views.log_list import LogListView
from .views.log_detail import LogDetailView
from .views.log_create import LogCreateView
from .views.log_update import LogUpdateView
from .views.log_delete import LogDeleteView
from .views.log_comment_list import LogCommentListView
from .views.log_comment_detail import LogCommentDetailView
from .views.log_comment_create import LogCommentCreateView
from .views.log_comment_update import LogCommentUpdateView
from .views.log_comment_delete import LogCommentDeleteView
from .views.log_add_reaction import LogAddReactionView
from .views.log_remove_reaction import LogRemoveReactionView
from .views.master_log_theme import M_LogThemeViewSet
from .views.master_log_category import M_LogCategoryViewSet

app_name = "log"

router = routers.DefaultRouter()
router.register("master-log-themes", M_LogThemeViewSet, basename="master-log-theme")
router.register("master-log-categories", M_LogCategoryViewSet, basename="master-log-category")

urlpatterns = [
    # ViewSet関連のURL(CRUD一括)
    path("", include(router.urls)),
    # ログ関連
    path("list/", LogListView.as_view(), name="log-list"),
    path("create/", LogCreateView.as_view(), name="log-create"),
    path("<uuid:log_id>/", LogDetailView.as_view(), name="log-detail"),
    path("<uuid:log_id>/update/", LogUpdateView.as_view(), name="log-update"),
    path("<uuid:log_id>/delete/", LogDeleteView.as_view(), name="log-delete"),
    path("<uuid:log_id>/reaction/add/<uuid:emoji_id>/", LogAddReactionView.as_view(), name="log-add-reaction"),
    path("<uuid:log_id>/reaction/remove/<uuid:emoji_id>/", LogRemoveReactionView.as_view(), name="log-remove-reaction"),
    # コメント関連
    path("<uuid:log_id>/comments/list/", LogCommentListView.as_view(), name="log-comment-list"),
    path("<uuid:log_id>/comments/create/", LogCommentCreateView.as_view(), name="log-comment-create"),
    path("<uuid:log_id>/comments/<uuid:log_comment_id>/", LogCommentDetailView.as_view(), name="log-comment-detail"),
    path("<uuid:log_id>/comments/<uuid:log_comment_id>/update/", LogCommentUpdateView.as_view(), name="log-comment-update"),
    path("<uuid:log_id>/comments/<uuid:log_comment_id>/delete/", LogCommentDeleteView.as_view(), name="log-comment-delete"),
    path("<uuid:log_id>/comments/<uuid:log_comment_id>/reaction/add/<uuid:emoji_id>/", LogAddReactionView.as_view(), name="log-comment-add-reaction"),
    path("<uuid:log_id>/comments/<uuid:log_comment_id>/reaction/remove/<uuid:emoji_id>/", LogRemoveReactionView.as_view(), name="log-comment-remove-reaction"),
]
