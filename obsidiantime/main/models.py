from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Quote(models.Model):
    text = models.TextField(verbose_name="Текст цитаты")
    author = models.CharField(max_length=200, verbose_name="Автор цитаты")
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Добавил")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")
    is_approved = models.BooleanField(default=True, verbose_name="Одобрено")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Цитата"
        verbose_name_plural = "Цитаты"

    def __str__(self):
        return f'"{self.text[:50]}..." - {self.author}'

    @property
    def likes_count(self):
        return self.quote_likes.count()


class QuoteLike(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name="quote_likes",
        verbose_name="Цитата",
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        unique_together = ["user", "quote"]
        verbose_name = "Лайк цитаты"
        verbose_name_plural = "Лайки цитат"

    def __str__(self):
        return f"{self.user.username} лайкнул цитату {self.quote.id}"


class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ("twitch", "Twitch"),
        ("youtube", "YouTube"),
        ("telegram", "Telegram"),
        ("discord", "Discord"),
        ("vk", "VKontakte"),
        ("other", "Другое"),
    ]

    platform = models.CharField(
        max_length=20, choices=PLATFORM_CHOICES, verbose_name="Платформа"
    )
    url = models.URLField(verbose_name="Ссылка")
    title = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Социальная ссылка"
        verbose_name_plural = "Социальные ссылки"

    def __str__(self):
        return f"{self.get_platform_display()}: {self.title}"

    @property
    def icon_class(self):
        icons = {
            "twitch": "fab fa-twitch",
            "youtube": "fab fa-youtube",
            "telegram": "fab fa-telegram",
            "discord": "fab fa-discord",
            "vk": "fab fa-vk",
        }
        return icons.get(self.platform, "fas fa-link")


class SiteSettings(models.Model):
    site_title = models.CharField(
        max_length=100, default="ObsidianTime", verbose_name="Название сайта"
    )
    site_description = models.TextField(blank=True, verbose_name="Описание сайта")
    rickroll_video_url = models.URLField(
        default="https://www.youtube.com/embed/dQw4w9WgXcQ",
        verbose_name="Ссылка на рикролл видео",
    )
    show_rickroll = models.BooleanField(default=True, verbose_name="Показывать рикролл")

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return self.site_title

    def save(self, *args, **kwargs):
        # Гарантируем что существует только одна запись настроек
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError("Настройки сайта уже существуют")
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
