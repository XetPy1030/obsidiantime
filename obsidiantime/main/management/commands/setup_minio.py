import json

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Setup MinIO bucket and configure permissions"

    def handle(self, *args, **options):
        if not getattr(settings, "USE_S3", False):
            self.stdout.write(
                self.style.ERROR("S3 is not enabled. Set USE_S3=true in environment.")
            )
            return

        endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        if not endpoint_url:
            self.stdout.write(
                self.style.ERROR(
                    "AWS_S3_ENDPOINT_URL not configured. "
                    "This command is for MinIO setup."
                )
            )
            return

        try:
            # Создаем S3 клиент для MinIO
            s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            bucket_name = settings.AWS_STORAGE_BUCKET_NAME

            # Проверяем существует ли bucket
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                self.stdout.write(
                    self.style.WARNING(f'Bucket "{bucket_name}" already exists.')
                )
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "404":
                    # Bucket не существует, создаем его
                    self.stdout.write(f'Creating bucket "{bucket_name}"...')
                    s3_client.create_bucket(Bucket=bucket_name)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Bucket "{bucket_name}" created successfully!'
                        )
                    )
                else:
                    raise e

            # Настраиваем политику bucket для публичного чтения
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}/media/*"],
                    }
                ],
            }

            s3_client.put_bucket_policy(
                Bucket=bucket_name, Policy=json.dumps(bucket_policy)
            )

            self.stdout.write(self.style.SUCCESS("MinIO setup completed successfully!"))
            self.stdout.write("MinIO Console: http://localhost:9001")
            self.stdout.write(f"Username: {settings.AWS_ACCESS_KEY_ID}")
            self.stdout.write(f"Password: {settings.AWS_SECRET_ACCESS_KEY}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error setting up MinIO: {e}"))
            self.stdout.write("Make sure MinIO is running and accessible.")
