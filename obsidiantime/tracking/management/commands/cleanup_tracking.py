from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from obsidiantime.tracking.models import VisitEvent, Visitor


class Command(BaseCommand):
    help = "Удаляет данные аналитики старше срока хранения из политики"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=settings.TRACKING["RETENTION_DAYS"],
            help="Срок хранения в днях (по умолчанию TRACKING['RETENTION_DAYS'])",
        )

    def handle(self, *args, **options):
        border = timezone.now() - timedelta(days=options["days"])

        events_deleted, _ = VisitEvent.objects.filter(created_at__lt=border).delete()
        visitors_deleted, _ = Visitor.objects.filter(last_seen_at__lt=border).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Удалено событий: {events_deleted}, "
                f"записей (посетители со связанными данными): {visitors_deleted}"
            )
        )
