import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Visitor(models.Model):
    """Посетитель сайта, давший (или отозвавший) согласие на аналитику"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tracking_visitors",
        verbose_name="Пользователь",
    )
    analytics_consent = models.BooleanField(
        default=False, verbose_name="Согласие на аналитику"
    )
    consent_version = models.CharField(
        max_length=32, blank=True, verbose_name="Версия политики"
    )
    consent_updated_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Согласие изменено"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="Последний IP"
    )
    user_agent = models.TextField(blank=True, verbose_name="User-Agent")
    accept_language = models.CharField(
        max_length=255, blank=True, verbose_name="Accept-Language"
    )
    client_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Данные браузера и устройства",
        help_text="Последний снимок, присланный браузером",
    )
    first_seen_at = models.DateTimeField(
        default=timezone.now, verbose_name="Первый визит"
    )
    last_seen_at = models.DateTimeField(
        default=timezone.now, verbose_name="Последний визит"
    )

    class Meta:
        ordering = ["-last_seen_at"]
        verbose_name = "Посетитель"
        verbose_name_plural = "Посетители"

    def __str__(self):
        owner = self.user.username if self.user else "аноним"
        return f"{str(self.id)[:8]} ({owner})"

    def clear_personal_data(self):
        """Удаляет собранные данные, оставляя только запись о выборе"""
        self.events.all().delete()
        self.ip_address = None
        self.user_agent = ""
        self.accept_language = ""
        self.client_info = {}
        self.user = None


class ConsentLog(models.Model):
    """Журнал изменений согласия — подтверждение того, что и когда выбрал человек"""

    ACTION_CHOICES = [
        ("granted", "Согласие дано"),
        ("withdrawn", "Согласие отозвано"),
    ]

    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name="consent_logs",
        verbose_name="Посетитель",
    )
    action = models.CharField(
        max_length=20, choices=ACTION_CHOICES, verbose_name="Действие"
    )
    policy_version = models.CharField(max_length=32, verbose_name="Версия политики")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.TextField(blank=True, verbose_name="User-Agent")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Запись о согласии"
        verbose_name_plural = "Журнал согласий"

    def __str__(self):
        return f"{self.get_action_display()} — {str(self.visitor_id)[:8]}"


class VisitEvent(models.Model):
    """Событие на странице: просмотр, уход со страницы, клик"""

    EVENT_TYPE_CHOICES = [
        ("pageview", "Просмотр страницы"),
        ("page_leave", "Уход со страницы"),
        ("click", "Клик"),
    ]

    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Посетитель",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tracking_events",
        verbose_name="Пользователь",
    )
    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPE_CHOICES, verbose_name="Тип события"
    )
    page_id = models.CharField(
        max_length=36,
        blank=True,
        verbose_name="ID просмотра",
        help_text="Связывает события одного открытия страницы",
    )
    url = models.CharField(max_length=2048, blank=True, verbose_name="URL")
    path = models.CharField(max_length=1024, blank=True, verbose_name="Путь")
    referrer = models.CharField(max_length=2048, blank=True, verbose_name="Откуда")
    title = models.CharField(max_length=512, blank=True, verbose_name="Заголовок")
    data = models.JSONField(default=dict, blank=True, verbose_name="Данные")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    created_at = models.DateTimeField(
        default=timezone.now, db_index=True, verbose_name="Создано"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Событие"
        verbose_name_plural = "События"
        indexes = [
            models.Index(fields=["visitor", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()}: {self.path}"
