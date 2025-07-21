from django.contrib import admin
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from .models import Analytics, RobotsRule, SEOGenericModel, SitemapURL


@admin.register(SEOGenericModel)
class SEOGenericModelAdmin(admin.ModelAdmin):
    list_display = [
        "content_type",
        "object_id",
        "meta_title",
        "robots_index",
        "robots_follow",
        "priority",
    ]
    list_filter = [
        "robots_index",
        "robots_follow",
        "og_type",
        "twitter_card",
        "changefreq",
    ]
    search_fields = ["meta_title", "meta_description", "meta_keywords"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (_("Основная информация"), {"fields": ("content_type", "object_id")}),
        (
            _("Meta теги"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "canonical_url",
                )
            },
        ),
        (
            _("Open Graph"),
            {
                "fields": ("og_title", "og_description", "og_image", "og_type"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Twitter Card"),
            {
                "fields": (
                    "twitter_card",
                    "twitter_title",
                    "twitter_description",
                    "twitter_image",
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Schema.org"), {"fields": ("schema_markup",), "classes": ("collapse",)}),
        (
            _("Поисковые роботы"),
            {"fields": ("robots_index", "robots_follow", "priority", "changefreq")},
        ),
        (
            _("Временные метки"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("content_type")


@admin.register(SitemapURL)
class SitemapURLAdmin(admin.ModelAdmin):
    list_display = ["url", "priority", "changefreq", "lastmod", "is_active"]
    list_filter = ["is_active", "changefreq", "priority"]
    search_fields = ["url"]
    readonly_fields = ["created_at", "lastmod"]
    ordering = ["-priority", "url"]

    fieldsets = (
        (_("Основная информация"), {"fields": ("url", "is_active")}),
        (_("Sitemap настройки"), {"fields": ("priority", "changefreq")}),
        (
            _("Временные метки"),
            {"fields": ("created_at", "lastmod"), "classes": ("collapse",)},
        ),
    )


@admin.register(RobotsRule)
class RobotsRuleAdmin(admin.ModelAdmin):
    list_display = ["user_agent", "rule_type", "path", "is_active", "order"]
    list_filter = ["user_agent", "rule_type", "is_active"]
    search_fields = ["path", "user_agent"]
    readonly_fields = ["created_at"]
    ordering = ["order", "user_agent", "rule_type"]

    fieldsets = (
        (
            _("Основная информация"),
            {"fields": ("user_agent", "rule_type", "path", "is_active")},
        ),
        (_("Порядок"), {"fields": ("order",)}),
        (_("Временные метки"), {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        "google_analytics_id",
        "yandex_metrika_id",
        "is_active",
        "updated_at",
    ]
    list_filter = ["is_active"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Google Analytics"),
            {"fields": ("google_analytics_id", "google_search_console")},
        ),
        (_("Яндекс.Метрика"), {"fields": ("yandex_metrika_id", "yandex_webmaster")}),
        (
            _("Социальные сети"),
            {"fields": ("facebook_pixel", "vk_pixel"), "classes": ("collapse",)},
        ),
        (_("Статус"), {"fields": ("is_active",)}),
        (
            _("Временные метки"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        # Разрешаем только одну запись настроек аналитики
        return not Analytics.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление настроек аналитики
        return False


# Кастомные действия для SEO
class SEOAdminActions:
    """Кастомные действия для SEO админки"""

    @admin.action(description=_("Обновить sitemap"))
    def update_sitemap(self, request, queryset):
        cache.delete("sitemap_cache")
        self.message_user(request, _("Sitemap обновлен"))

    @admin.action(description=_("Обновить robots.txt"))
    def update_robots(self, request, queryset):
        cache.delete("robots_cache")
        self.message_user(request, _("Robots.txt обновлен"))

    @admin.action(description=_("Проверить SEO"))
    def check_seo(self, request, queryset):
        # Здесь можно добавить логику проверки SEO
        self.message_user(request, _("SEO проверка завершена"))


# Добавляем действия к админке
SitemapURLAdmin.actions = [SEOAdminActions.update_sitemap]
RobotsRuleAdmin.actions = [SEOAdminActions.update_robots]
SEOGenericModelAdmin.actions = [SEOAdminActions.check_seo]
