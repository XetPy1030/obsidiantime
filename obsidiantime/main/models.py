from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Constants
QUOTE_PREVIEW_LENGTH = 50


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
        return f'"{self.text[:QUOTE_PREVIEW_LENGTH]}..." - {self.author}'

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
        ("donationalerts", "DonationAlerts"),
        ("boosty", "Boosty"),
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
            "donationalerts": "fas fa-heart",
            "boosty": "simple-icons--boosty",
        }
        return icons.get(self.platform, "fas fa-link")


class SiteSettings(models.Model):
    site_title = models.CharField(
        max_length=100, default="ObsidianTime", verbose_name="Название сайта"
    )
    site_description = models.TextField(blank=True, verbose_name="Описание сайта")
    rickroll_video = models.FileField(
        upload_to="videos/",
        blank=True,
        null=True,
        verbose_name="Видео для рикролла",
        help_text="Загрузите видео файл (MP4, WebM, OGG)",
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


class Feedback(models.Model):
    """Модель для обратной связи"""

    FEEDBACK_TYPE_CHOICES = [
        ("suggestion", "Предложение"),
        ("bug", "Сообщение об ошибке"),
        ("question", "Вопрос"),
        ("compliment", "Благодарность"),
        ("other", "Другое"),
    ]

    STATUS_CHOICES = [
        ("new", "Новое"),
        ("in_progress", "В обработке"),
        ("resolved", "Решено"),
        ("closed", "Закрыто"),
    ]

    name = models.CharField(max_length=100, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    feedback_type = models.CharField(
        max_length=20, choices=FEEDBACK_TYPE_CHOICES, verbose_name="Тип обращения"
    )
    subject = models.CharField(max_length=200, verbose_name="Тема")
    message = models.TextField(verbose_name="Сообщение")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратная связь"

    def __str__(self):
        return f"{self.get_feedback_type_display()}: {self.subject} ({self.name})"

    @property
    def is_resolved(self):
        return self.status in ["resolved", "closed"]

    @property
    def public_comments_count(self):
        """Количество публичных комментариев"""
        return self.comments.filter(is_internal=False).count()

    @property
    def admin_comments_count(self):
        """Количество комментариев администраторов"""
        return self.comments.filter(comment_type="admin").count()

    @property
    def user_comments_count(self):
        """Количество комментариев пользователей"""
        return self.comments.filter(comment_type="user").count()


class FeedbackComment(models.Model):
    """Комментарии к обращениям"""

    COMMENT_TYPE_CHOICES = [
        ("user", "Пользователь"),
        ("admin", "Администратор"),
    ]

    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Обращение",
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    comment_type = models.CharField(
        max_length=10,
        choices=COMMENT_TYPE_CHOICES,
        default="user",
        verbose_name="Тип комментария",
    )
    comment = models.TextField(verbose_name="Комментарий")
    is_internal = models.BooleanField(
        default=False,
        verbose_name="Внутренний комментарий",
        help_text="Если отмечено, комментарий виден только администраторам",
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Комментарий к обращению"
        verbose_name_plural = "Комментарии к обращениям"

    def __str__(self):
        return f"Комментарий к обращению {self.feedback.id} от {self.author.username}"

    def save(self, *args, **kwargs):
        # Автоматически определяем тип комментария
        if self.author.is_staff:
            self.comment_type = "admin"
        else:
            self.comment_type = "user"
        super().save(*args, **kwargs)

    @property
    def is_admin_comment(self):
        return self.comment_type == "admin"

    @property
    def is_user_comment(self):
        return self.comment_type == "user"
