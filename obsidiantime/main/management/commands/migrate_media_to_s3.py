import os

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Migrate local media files to S3 storage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without actually doing it",
        )

    def handle(self, *args, **options):  # noqa: PLR0912
        dry_run = options["dry_run"]

        if not getattr(settings, "USE_S3", False):
            self.stdout.write(
                self.style.ERROR("S3 is not enabled. Set USE_S3=true in environment.")
            )
            return

        self.stdout.write("Starting media files migration to S3...")

        migrated_count = 0
        error_count = 0

        # Получаем все модели с FileField/ImageField
        for model in apps.get_models():
            file_fields = []
            for field in model._meta.get_fields():
                if hasattr(field, "upload_to") and hasattr(field, "storage"):
                    file_fields.append(field)

            if not file_fields:
                continue

            self.stdout.write(f"Processing model: {model.__name__}")

            for obj in model.objects.all():
                for field in file_fields:
                    field_file = getattr(obj, field.name)

                    if not field_file:
                        continue

                    # Проверяем, существует ли файл локально
                    local_path = os.path.join(settings.MEDIA_ROOT, field_file.name)

                    if not os.path.exists(local_path):
                        continue

                    if dry_run:
                        self.stdout.write(f"  Would migrate: {field_file.name}")
                        migrated_count += 1
                        continue

                    try:
                        # Читаем локальный файл
                        with open(local_path, "rb") as local_file:
                            content = local_file.read()

                        # Проверяем, не существует ли уже файл в S3
                        if not default_storage.exists(field_file.name):
                            # Сохраняем в S3
                            default_storage.save(field_file.name, ContentFile(content))
                            self.stdout.write(
                                self.style.SUCCESS(f"  Migrated: {field_file.name}")
                            )
                            migrated_count += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  Already exists: {field_file.name}"
                                )
                            )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"  Error migrating {field_file.name}: {e}"
                            )
                        )
                        error_count += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run completed. Would migrate {migrated_count} files."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Migration completed. Migrated {migrated_count} files with "
                    f"{error_count} errors."
                )
            )

            if error_count == 0:
                self.stdout.write(
                    "\nYou can now safely remove local media files after "
                    "verifying the migration."
                )
