from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from apps.api_key.models import M_ApiKeyScope, R_ApiKeyScope, T_ApiKey

class SoftDeleteFilter(admin.SimpleListFilter):
    title = _('状態')
    parameter_name = 'is_deleted'

    def lookups(self, request, model_admin):
        return (
            ('active', _('有効のみ')),
            ('deleted', _('削除済みのみ')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(deleted_at__isnull=True)
        if self.value() == 'deleted':
            return queryset.filter(deleted_at__isnull=False)
        return queryset

# ------------------------------------------------------------------
# M_ApiKeyScope (APIキースコープマスタ)
# ------------------------------------------------------------------
@admin.register(M_ApiKeyScope)
class M_ApiKeyScopeAdmin(admin.ModelAdmin):
    """
    APIキースコープマスタの管理設定
    """
    list_display = ("code", "name", "description", "created_at", "deleted_at")
    list_filter = (SoftDeleteFilter,)
    search_fields = ("code", "name")
    
    fieldsets = (
        (None, {"fields": ("code", "name", "description")}),
        ("システム情報", {"fields": ("created_method", "updated_method", "created_at", "updated_at", "deleted_at")}),
    )
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.created_method = "admin_panel"
        obj.updated_by = request.user
        obj.updated_method = "admin_panel"
        super().save_model(request, obj, form, change)


# ------------------------------------------------------------------
# R_ApiKeyScope (APIキースコープリレーション: インライン用)
# ------------------------------------------------------------------
class R_ApiKeyScopeInline(admin.TabularInline):
    """
    APIキー詳細画面でスコープを編集するためのインライン
    """
    model = R_ApiKeyScope
    extra = 1
    fields = ("api_key_scope",)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.created_method = "admin_panel"
        obj.updated_by = request.user
        obj.updated_method = "admin_panel"
        super().save_model(request, obj, form, change)


# ------------------------------------------------------------------
# T_ApiKey (APIキー発行トラン)
# ------------------------------------------------------------------
@admin.register(T_ApiKey)
class T_ApiKeyAdmin(admin.ModelAdmin):
    """
    APIキー発行トランの管理設定
    """
    list_display = (
        "name", 
        "user", 
        "client_key", 
        "is_active", 
        "expired_at", 
        "last_used_at",
        "created_at",
        "deleted_at"
    )
    list_filter = (SoftDeleteFilter, "is_active", "revoked_reason", "user")
    search_fields = ("name", "client_key", "user__email", "user__username")
    
    inlines = [R_ApiKeyScopeInline]
    
    fieldsets = (
        ("基本情報", {"fields": ("user", "name", "description")}),
        ("キー情報", {"fields": ("client_key", "hashed_secret", "is_active", "expired_at", "last_used_at")}),
        ("無効化情報", {"fields": ("revoked_reason", "revoked_detail")}),
        ("システム情報", {"fields": ("created_method", "updated_method", "created_at", "updated_at", "deleted_at")}),
    )
    
    # キー情報はAdminからは原則閲覧のみ（ hashed_secret はハッシュ値なので編集不可とするのが安全 ）
    readonly_fields = (
        "client_key", 
        "hashed_secret", 
        "last_used_at", 
        "created_at", 
        "updated_at"
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.created_method = "admin_panel"
        obj.updated_by = request.user
        obj.updated_method = "admin_panel"
        super().save_model(request, obj, form, change)

    # インライン側の保存もAdmin経由の更新情報をセットするためにオーバーライド
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            if not instance.pk: # 新規
                instance.created_by = request.user
                instance.created_method = "admin_panel"
            instance.updated_by = request.user
            instance.updated_method = "admin_panel"
            instance.save()
        formset.save_m2m()
