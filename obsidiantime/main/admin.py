from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Quote, SocialLink

# Константы для админки
URL_PREVIEW_LENGTH = 40
URL_PREVIEW_TRUNCATE = 37
DESCRIPTION_PREVIEW_LENGTH = 50
DESCRIPTION_PREVIEW_TRUNCATE = 47
TEXT_PREVIEW_LENGTH = 100
TEXT_PREVIEW_TRUNCATE = 97


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = [
        "text_preview",
        "author",
        "added_by",
        "views",
        "likes_count",
        "created_at",
        "get_actions",
    ]
    list_filter = ["created_at", "added_by"]
    search_fields = ["text", "author", "added_by__username"]
    readonly_fields = ["views", "likes_count", "created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("text", "author"),
            },
        ),
        (
            "Метаданные",
            {
                "fields": ("added_by", "views", "likes_count"),
                "classes": ("collapse",),
            },
        ),
        (
            "Временные метки",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def text_preview(self, obj):
        """Показывает сокращенный текст цитаты"""
        if len(obj.text) > TEXT_PREVIEW_LENGTH:
            return f"{obj.text[:TEXT_PREVIEW_TRUNCATE]}..."
        return obj.text

    text_preview.short_description = "Текст цитаты"

    def get_actions(self, obj):
        """Показывает кнопки действий"""
        view_url = reverse("admin:main_quote_change", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Редактировать</a>',
            view_url,
        )

    get_actions.short_description = "Действия"

    def save_model(self, request, obj, form, change):
        if not change:  # Если это новая запись
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "url_preview",
        "icon_class",
        "is_active",
        "order",
        "get_actions",
    ]
    list_filter = ["is_active", "order"]
    search_fields = ["title", "url"]
    list_editable = ["order", "is_active"]
    ordering = ["order"]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("title", "url", "icon_class"),
            },
        ),
        (
            "Настройки",
            {
                "fields": ("is_active", "order"),
            },
        ),
    )

    def url_preview(self, obj):
        """Показывает сокращенную ссылку"""
        if len(obj.url) > URL_PREVIEW_LENGTH:
            return f"{obj.url[:URL_PREVIEW_TRUNCATE]}..."
        return obj.url

    url_preview.short_description = "URL"

    def get_actions(self, obj):
        """Показывает кнопки действий"""
        view_url = reverse("admin:main_sociallink_change", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Редактировать</a>',
            view_url,
        )

    get_actions.short_description = "Действия"
