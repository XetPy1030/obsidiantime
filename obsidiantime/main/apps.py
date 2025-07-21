from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "obsidiantime.main"

    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        import obsidiantime.main.signals  # noqa
