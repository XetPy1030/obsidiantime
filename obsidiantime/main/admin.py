from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Feedback,
    FeedbackComment,
    Quote,
    QuoteLike,
    SiteSettings,
    SocialLink,
)

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
        "is_approved",
        "views",
        "likes_count",
        "created_at",
        "get_actions",
    ]
    list_filter = ["created_at", "added_by", "is_approved"]
    search_fields = ["text", "author", "added_by__username"]
    readonly_fields = ["views", "likes_count", "created_at"]
    date_hierarchy = "created_at"
    list_editable = ["is_approved"]

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
                "fields": ("added_by", "views", "likes_count", "is_approved"),
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
        if hasattr(obj, "pk") and obj.pk:
            view_url = reverse("admin:main_quote_change", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Редактировать</a>',
                view_url,
            )
        return ""

    get_actions.short_description = "Действия"

    def save_model(self, request, obj, form, change):
        if not change:  # Если это новая запись
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "platform",
        "url_preview",
        "icon_class",
        "is_active",
        "order",
        "get_actions",
    ]
    list_filter = ["is_active", "platform", "order"]
    search_fields = ["title", "url", "description"]
    list_editable = ["order", "is_active"]
    ordering = ["order"]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("title", "url", "platform"),
            },
        ),
        (
            "Дополнительно",
            {
                "fields": ("description",),
                "classes": ("collapse",),
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
        if hasattr(obj, "pk") and obj.pk:
            view_url = reverse("admin:main_sociallink_change", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Редактировать</a>',
                view_url,
            )
        return ""

    get_actions.short_description = "Действия"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "site_title",
        "site_description_preview",
        "show_rickroll",
        "get_actions",
    ]
    readonly_fields = ["get_actions"]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("site_title", "site_description"),
            },
        ),
        (
            "Рикролл",
            {
                "fields": ("rickroll_video", "show_rickroll"),
            },
        ),
    )

    def site_description_preview(self, obj):
        """Показывает сокращенное описание сайта"""
        if (
            obj.site_description
            and len(obj.site_description) > DESCRIPTION_PREVIEW_LENGTH
        ):
            return f"{obj.site_description[:DESCRIPTION_PREVIEW_TRUNCATE]}..."
        return obj.site_description or "Нет описания"

    site_description_preview.short_description = "Описание сайта"

    def get_actions(self, obj):
        """Показывает кнопки действий"""
        if hasattr(obj, "pk") and obj.pk:
            view_url = reverse("admin:main_sitesettings_change", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Редактировать</a>',
                view_url,
            )
        return ""

    get_actions.short_description = "Действия"

    def has_add_permission(self, request):
        """Запрещаем создание новых записей настроек"""
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление настроек"""
        return False


@admin.register(QuoteLike)
class QuoteLikeAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "quote_preview",
        "created_at",
        "get_actions",
    ]
    list_filter = ["created_at", "user"]
    search_fields = ["user__username", "quote__text", "quote__author"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("user", "quote"),
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

    def quote_preview(self, obj):
        """Показывает сокращенный текст цитаты"""
        if len(obj.quote.text) > TEXT_PREVIEW_LENGTH:
            return f"{obj.quote.text[:TEXT_PREVIEW_TRUNCATE]}..."
        return obj.quote.text

    quote_preview.short_description = "Цитата"

    def get_actions(self, obj):
        """Показывает кнопки действий"""
        if hasattr(obj, "pk") and obj.pk:
            view_url = reverse("admin:main_quotelike_change", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Редактировать</a>',
                view_url,
            )
        return ""

    get_actions.short_description = "Действия"


class FeedbackCommentInline(admin.TabularInline):
    model = FeedbackComment
    extra = 1
    fields = ["author", "comment_type", "comment", "is_internal", "created_at"]
    readonly_fields = ["created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "subject",
        "name",
        "email",
        "feedback_type",
        "status",
        "created_at",
        "is_resolved",
        "comments_count",
        "get_actions",
    ]
    list_filter = ["status", "feedback_type", "created_at", "user"]
    search_fields = ["subject", "message", "name", "email", "user__username"]
    readonly_fields = ["created_at", "updated_at", "is_resolved"]
    date_hierarchy = "created_at"
    list_editable = ["status"]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("name", "email", "feedback_type", "subject", "message"),
            },
        ),
        (
            "Статус и пользователь",
            {
                "fields": ("status", "user"),
            },
        ),
        (
            "Временные метки",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [FeedbackCommentInline]

    def comments_count(self, obj):
        """Показывает количество комментариев"""
        count = obj.comments.count()
        return f"{count} комм."

    comments_count.short_description = "Комментарии"

    def get_actions(self, obj):
        """Показывает кнопки действий"""
        if hasattr(obj, "pk") and obj.pk:
            view_url = reverse("admin:main_feedback_change", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Редактировать</a>',
                view_url,
            )
        return ""

    get_actions.short_description = "Действия"

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            # Можно добавить логику уведомления пользователя об изменении статуса
            pass
        super().save_model(request, obj, form, change)


@admin.register(FeedbackComment)
class FeedbackCommentAdmin(admin.ModelAdmin):
    list_display = [
        "feedback_subject",
        "author",
        "comment_type",
        "comment_preview",
        "is_internal",
        "created_at",
        "get_actions",
    ]
    list_filter = ["comment_type", "is_internal", "created_at", "author"]
    search_fields = ["comment", "feedback__subject", "author__username"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    list_editable = ["is_internal"]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("feedback", "author", "comment_type", "comment"),
            },
        ),
        (
            "Настройки",
            {
                "fields": ("is_internal",),
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

    def feedback_subject(self, obj):
        """Показывает тему обращения"""
        return obj.feedback.subject

    feedback_subject.short_description = "Тема обращения"

    def comment_preview(self, obj):
        """Показывает сокращенный комментарий"""
        if len(obj.comment) > DESCRIPTION_PREVIEW_LENGTH:
            return f"{obj.comment[:DESCRIPTION_PREVIEW_TRUNCATE]}..."
        return obj.comment

    comment_preview.short_description = "Комментарий"

    def get_actions(self, obj):
        """Показывает кнопки действий"""
        if hasattr(obj, "pk") and obj.pk:
            view_url = reverse("admin:main_feedbackcomment_change", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Редактировать</a>',
                view_url,
            )
        return ""

    get_actions.short_description = "Действия"
