from django.apps import AppConfig


class TrackingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "obsidiantime.tracking"
    verbose_name = "Аналитика посетителей"
