from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import (
    CHANGEFREQ_CHOICES,
    CHANGEFREQ_DISPLAY_MAP,
    ROBOTS_RULE_TYPES,
    USER_AGENT_DISPLAY_MAP,
)


class SEOModel(models.Model):
    """Базовая модель для SEO метаданных"""

    meta_title = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_("Meta Title"),
        help_text=_("Заголовок страницы (до 60 символов)"),
    )
    meta_description = models.TextField(
        max_length=160,
        blank=True,
        verbose_name=_("Meta Description"),
        help_text=_("Описание страницы (до 160 символов)"),
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Meta Keywords"),
        help_text=_("Ключевые слова через запятую"),
    )
    canonical_url = models.URLField(
        blank=True,
        verbose_name=_("Canonical URL"),
        help_text=_("Канонический URL страницы"),
    )
    og_title = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_("Open Graph Title"),
        help_text=_("Заголовок для социальных сетей"),
    )
    og_description = models.TextField(
        max_length=160,
        blank=True,
        verbose_name=_("Open Graph Description"),
        help_text=_("Описание для социальных сетей"),
    )
    og_image = models.ImageField(
        upload_to="seo/og_images/",
        blank=True,
        null=True,
        verbose_name=_("Open Graph Image"),
        help_text=_("Изображение для социальных сетей (1200x630px)"),
    )
    og_type = models.CharField(
        max_length=50,
        default="website",
        verbose_name=_("Open Graph Type"),
        help_text=_("Тип контента для социальных сетей"),
    )
    twitter_card = models.CharField(
        max_length=50,
        default="summary_large_image",
        verbose_name=_("Twitter Card Type"),
        help_text=_("Тип карточки Twitter"),
    )
    twitter_title = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_("Twitter Title"),
        help_text=_("Заголовок для Twitter"),
    )
    twitter_description = models.TextField(
        max_length=160,
        blank=True,
        verbose_name=_("Twitter Description"),
        help_text=_("Описание для Twitter"),
    )
    twitter_image = models.ImageField(
        upload_to="seo/twitter_images/",
        blank=True,
        null=True,
        verbose_name=_("Twitter Image"),
        help_text=_("Изображение для Twitter (1200x600px)"),
    )
    schema_markup = models.TextField(
        blank=True,
        verbose_name=_("Schema.org Markup"),
        help_text=_("JSON-LD разметка для поисковых систем"),
    )
    robots_index = models.BooleanField(
        default=True,
        verbose_name=_("Allow Indexing"),
        help_text=_("Разрешить индексацию страницы"),
    )
    robots_follow = models.BooleanField(
        default=True,
        verbose_name=_("Allow Following Links"),
        help_text=_("Разрешить следование по ссылкам"),
    )
    priority = models.FloatField(
        default=0.5,
        verbose_name=_("Sitemap Priority"),
        help_text=_("Приоритет страницы в sitemap (0.0-1.0)"),
    )
    changefreq = models.CharField(
        max_length=20,
        default="weekly",
        choices=CHANGEFREQ_CHOICES,
        verbose_name=_("Change Frequency"),
        help_text=_("Частота изменения страницы"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        verbose_name = _("SEO Metadata")
        verbose_name_plural = _("SEO Metadata")

    def __str__(self):
        return f"SEO: {self.meta_title or 'Untitled'}"

    def get_meta_title(self):
        """Возвращает meta title или заголовок по умолчанию"""
        return self.meta_title or getattr(self, "title", "ObsidianTime")

    def get_meta_description(self):
        """Возвращает meta description или описание по умолчанию"""
        return self.meta_description or getattr(self, "description", "")

    def get_og_title(self):
        """Возвращает Open Graph title"""
        return self.og_title or self.get_meta_title()

    def get_og_description(self):
        """Возвращает Open Graph description"""
        return self.og_description or self.get_meta_description()

    def get_twitter_title(self):
        """Возвращает Twitter title"""
        return self.twitter_title or self.get_meta_title()

    def get_twitter_description(self):
        """Возвращает Twitter description"""
        return self.twitter_description or self.get_meta_description()


class SEOGenericModel(SEOModel):
    """Универсальная модель SEO для любых объектов"""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Generic SEO Metadata")
        verbose_name_plural = _("Generic SEO Metadata")
        unique_together = ("content_type", "object_id")

    def __str__(self):
        return f"SEO for {self.content_type.model}: {self.object_id}"


class SitemapURL(models.Model):
    """Модель для управления URL в sitemap"""

    url = models.CharField(max_length=255, unique=True)
    priority = models.FloatField(default=0.5)
    changefreq = models.CharField(
        max_length=20,
        default="weekly",
        choices=[
            ("always", "Always"),
            ("hourly", "Hourly"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly"),
            ("never", "Never"),
        ],
    )
    lastmod = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Sitemap URL")
        verbose_name_plural = _("Sitemap URLs")
        ordering = ["-priority", "url"]

    def __str__(self):
        return self.url

    def get_full_url(self):
        """Возвращает полный URL с доменом"""
        site = Site.objects.get_current()
        return f"https://{site.domain}{self.url}"

    def is_valid_priority(self):
        """Проверяет, что приоритет в допустимом диапазоне"""
        return 0.0 <= self.priority <= 1.0

    def get_changefreq_display(self):
        """Возвращает человекочитаемое название частоты изменения"""
        return CHANGEFREQ_DISPLAY_MAP.get(self.changefreq, self.changefreq)


class RobotsRule(models.Model):
    """Модель для управления robots.txt"""

    user_agent = models.CharField(
        max_length=100,
        default="*",
        verbose_name=_("User Agent"),
        help_text=_("User agent для правила (например, *, Googlebot)"),
    )
    rule_type = models.CharField(
        max_length=10, choices=ROBOTS_RULE_TYPES, verbose_name=_("Rule Type")
    )
    path = models.CharField(
        max_length=255,
        verbose_name=_("Path"),
        help_text=_("Путь для правила (например, /admin/)"),
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Robots Rule")
        verbose_name_plural = _("Robots Rules")
        ordering = ["order", "user_agent", "rule_type"]

    def __str__(self):
        return f"{self.user_agent}: {self.rule_type} {self.path}"

    def get_rule_text(self):
        """Возвращает текст правила для robots.txt"""
        return f"{self.rule_type.title()}: {self.path}"

    def is_global_rule(self):
        """Проверяет, является ли правило глобальным"""
        return self.user_agent == "*"

    def get_user_agent_display(self):
        """Возвращает человекочитаемое название user agent"""
        return USER_AGENT_DISPLAY_MAP.get(self.user_agent, self.user_agent)


class Analytics(models.Model):
    """Модель для хранения настроек аналитики"""

    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Google Analytics ID"),
        help_text=_("ID отслеживания Google Analytics (G-XXXXXXXXXX)"),
    )
    yandex_metrika_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Yandex Metrika ID"),
        help_text=_("ID счетчика Яндекс.Метрики"),
    )
    google_search_console = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Google Search Console"),
        help_text=_("Код подтверждения Google Search Console"),
    )
    yandex_webmaster = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Yandex Webmaster"),
        help_text=_("Код подтверждения Яндекс.Вебмастер"),
    )
    facebook_pixel = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Facebook Pixel ID"),
        help_text=_("ID пикселя Facebook"),
    )
    vk_pixel = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("VK Pixel ID"),
        help_text=_("ID пикселя ВКонтакте"),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Analytics Settings")
        verbose_name_plural = _("Analytics Settings")

    def __str__(self):
        return "Analytics Settings"

    @classmethod
    def get_settings(cls):
        """Возвращает настройки аналитики"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def has_google_analytics(self):
        """Проверяет, настроен ли Google Analytics"""
        return bool(self.google_analytics_id and self.is_active)

    def has_yandex_metrika(self):
        """Проверяет, настроена ли Яндекс.Метрика"""
        return bool(self.yandex_metrika_id and self.is_active)

    def has_facebook_pixel(self):
        """Проверяет, настроен ли Facebook Pixel"""
        return bool(self.facebook_pixel and self.is_active)

    def has_vk_pixel(self):
        """Проверяет, настроен ли VK Pixel"""
        return bool(self.vk_pixel and self.is_active)

    def get_active_analytics(self):
        """Возвращает список активных аналитических систем"""
        analytics = []
        if self.has_google_analytics():
            analytics.append("Google Analytics")
        if self.has_yandex_metrika():
            analytics.append("Яндекс.Метрика")
        if self.has_facebook_pixel():
            analytics.append("Facebook Pixel")
        if self.has_vk_pixel():
            analytics.append("VK Pixel")
        return analytics
