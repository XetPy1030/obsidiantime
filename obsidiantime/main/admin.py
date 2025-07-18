from django.contrib import admin

from .models import Quote, QuoteLike, SiteSettings, SocialLink

# Constants
TEXT_PREVIEW_LENGTH = 100


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = [
        "text_preview",
        "author",
        "added_by",
        "likes_count",
        "views",
        "is_approved",
        "created_at",
    ]
    list_filter = ["is_approved", "created_at", "added_by"]
    search_fields = ["text", "author", "added_by__username"]
    readonly_fields = ["created_at", "views"]
    list_editable = ["is_approved"]

    def text_preview(self, obj):
        text = obj.text
        if len(text) > TEXT_PREVIEW_LENGTH:
            return text[:TEXT_PREVIEW_LENGTH] + "..."
        return text

    text_preview.short_description = "Текст цитаты"

    def likes_count(self, obj):
        return obj.likes_count

    likes_count.short_description = "Лайки"


@admin.register(QuoteLike)
class QuoteLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "quote_preview", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "quote__text", "quote__author"]
    readonly_fields = ["created_at"]

    def quote_preview(self, obj):
        return f'"{obj.quote.text[:50]}..." - {obj.quote.author}'

    quote_preview.short_description = "Цитата"


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ["title", "platform", "url", "is_active", "order"]
    list_filter = ["platform", "is_active"]
    search_fields = ["title", "description"]
    list_editable = ["is_active", "order"]
    ordering = ["order", "title"]


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ["site_title", "show_rickroll"]
    fields = ["site_title", "site_description", "rickroll_video_url", "show_rickroll"]

    def has_add_permission(self, request):
        # Разрешаем добавление только если настроек еще нет
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление настроек
        return False
