from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

#  共通モジュール ---
from apps.common.models import T_FileResource, M_Emoji, M_Tag, R_ItemTag

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
# M_Emoji (絵文字マスタ)
# ------------------------------------------------------------------
@admin.register(M_Emoji)
class M_EmojiAdmin(admin.ModelAdmin):
    """
    絵文字マスタの管理設定
    """
    list_display = ("code", "display_name", "created_at", "deleted_at")
    list_filter = (SoftDeleteFilter, "deleted_at")
    search_fields = ("code", "display_name")
    readonly_fields = ("id", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        # 新規作成時 (change=False)
        if not change:
            # if not obj.updated_by:
            #     obj.updated_by = request.user
            # if not obj.updated_method:
            #     obj.updated_method = "admin_panel"
            
            # admin新規時は以下とする
            obj.created_by = request.user
            obj.created_method = "admin_panel"
            obj.updated_by = request.user
            obj.updated_method = "admin_panel"
        
        # 更新時(change=True)
        else:
            # 「更新時」は既存の値が入っているので、「手動でクリアされて空になった場合」や「意図的に上書きしたい場合」を考える必要がある
            # 基本的に「Adminで誰かが保存した」というログなら、強制的に上書きしても良いケースが多い？
            # ※「空の場合だけ自動セット」にしたいなら以下のようにする
            # if not obj.updated_by:
            #     obj.updated_by = request.user
            # if not obj.updated_method:
            #     obj.updated_method = "admin_panel"
            
            # admin更新時は以下とする
            obj.updated_by = request.user
            obj.updated_method = "admin_panel"
        
        super().save_model(request, obj, form, change)

# ------------------------------------------------------------------
# M_Tag (タグマスタ)
# ------------------------------------------------------------------
@admin.register(M_Tag)
class M_TagAdmin(admin.ModelAdmin):
    """
    タグマスタの管理設定
    """
    list_display = ("name", "created_at", "deleted_at")
    list_filter = (SoftDeleteFilter, "deleted_at")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        # 新規作成時 (change=False)
        if not change:
            # if not obj.updated_by:
            #     obj.updated_by = request.user
            # if not obj.updated_method:
            #     obj.updated_method = "admin_panel"
            
            # admin新規時は以下とする
            obj.created_by = request.user
            obj.created_method = "admin_panel"
            obj.updated_by = request.user
            obj.updated_method = "admin_panel"
        
        # 更新時(change=True)
        else:
            # 「更新時」は既存の値が入っているので、「手動でクリアされて空になった場合」や「意図的に上書きしたい場合」を考える必要がある
            # 基本的に「Adminで誰かが保存した」というログなら、強制的に上書きしても良いケースが多い？
            # ※「空の場合だけ自動セット」にしたいなら以下のようにする
            # if not obj.updated_by:
            #     obj.updated_by = request.user
            # if not obj.updated_method:
            #     obj.updated_method = "admin_panel"
            
            # admin更新時は以下とする
            obj.updated_by = request.user
            obj.updated_method = "admin_panel"
        
        super().save_model(request, obj, form, change)

# ------------------------------------------------------------------
# T_FileResource (ファイルリソース管理)
# ------------------------------------------------------------------
@admin.register(T_FileResource)
class T_FileResourceAdmin(admin.ModelAdmin):
    """
    画像・PDF等のファイルリソース管理
    """
    list_display = ("file_name", "file_type", "display_preview", "file_size_kb", "created_at", "deleted_at")
    list_filter = (SoftDeleteFilter, "file_type", "deleted_at")
    search_fields = ("file_name",)
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("基本情報", {
            "fields": ("id", "file_name", "file_type")
        }),
        ("リソース実体", {
            "fields": ("file", "file_size")
        }),
        ("システム情報", {
            "fields": ("created_method", "updated_method", "created_at", "updated_at", "deleted_at")
        }),
    )

    def display_preview(self, obj):
        """管理画面上で画像のプレビューを表示"""
        if obj.url:
            return format_html('<img src="{}" style="width: 50px; height: auto; border-radius: 4px;" />', obj.url)
        return "-"
    display_preview.short_description = "プレビュー"

    def file_size_kb(self, obj):
        """バイト表記をKB表記に変換して表示"""
        if obj.file_size:
            return f"{round(obj.file_size / 1024, 2)} KB"
        return "-"
    file_size_kb.short_description = "サイズ"

    def save_model(self, request, obj, form, change):
        # 新規作成時 (change=False)
        if not change:
            # if not obj.updated_by:
            #     obj.updated_by = request.user
            # if not obj.updated_method:
            #     obj.updated_method = "admin_panel"
            
            # admin新規時は以下とする
            obj.created_by = request.user
            obj.created_method = "admin_panel"
            obj.updated_by = request.user
            obj.updated_method = "admin_panel"
        
        # 更新時(change=True)
        else:
            # 「更新時」は既存の値が入っているので、「手動でクリアされて空になった場合」や「意図的に上書きしたい場合」を考える必要がある
            # 基本的に「Adminで誰かが保存した」というログなら、強制的に上書きしても良いケースが多い？
            # ※「空の場合だけ自動セット」にしたいなら以下のようにする
            # if not obj.updated_by:
            #     obj.updated_by = request.user
            # if not obj.updated_method:
            #     obj.updated_method = "admin_panel"
            
            # admin更新時は以下とする
            obj.updated_by = request.user
            obj.updated_method = "admin_panel"
        
        super().save_model(request, obj, form, change)

# ------------------------------------------------------------------
# R_ItemTag (アイテムタグリレーション)
# ------------------------------------------------------------------
@admin.register(R_ItemTag)
class R_ItemTagAdmin(admin.ModelAdmin):
    """
    アイテムタグリレーションの管理設定
    """
    list_display = ("item_type", "item_id", "tag", "created_at", "deleted_at")
    list_filter = (SoftDeleteFilter, "item_type", "deleted_at")
    search_fields = ("item_id", "tag__name")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        # 新規作成時 (change=False)
        if not change:
            # if not obj.updated_by:
            #     obj.updated_by = request.user
            # if not obj.updated_method:
            #     obj.updated_method = "admin_panel"
            
            # admin新規時は以下とする
            obj.created_by = request.user
            obj.created_method = "admin_panel"
            obj.updated_by = request.user
            obj.updated_method = "admin_panel"
        
        # 更新時(change=True)
        else:
            # 「更新時」は既存の値が入っているので、「手動でクリアされて空になった場合」や「意図的に上書きしたい場合」を考える必要がある
            # 基本的に「Adminで誰かが保存した」というログなら、強制的に上書きしても良いケースが多い？
            # ※「空の場合だけ自動セット」にしたいなら以下のようにする
            # if not obj.updated_by:
            #     obj.updated_by = request.user
            # if not obj.updated_method:
            #     obj.updated_method = "admin_panel"
            
            # admin更新時は以下とする
            obj.updated_by = request.user
            obj.updated_method = "admin_panel"
        
        super().save_model(request, obj, form, change)
