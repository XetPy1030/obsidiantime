import io
import logging

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from PIL import Image

# Constants
COMMENT_PREVIEW_LENGTH = 50

# Получаем логгер для этого модуля
logger = logging.getLogger(__name__)


class Meme(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to="memes/%Y/%m/%d/", verbose_name="Изображение")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    is_approved = models.BooleanField(default=True, verbose_name="Одобрено")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Мем"
        verbose_name_plural = "Мемы"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Сначала сохраняем объект
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Оптимизируем изображение только для новых объектов
        if is_new and self.image:
            try:
                self.image.seek(0)
                img = Image.open(self.image)

                img_format = img.format or "JPEG"
                max_size = (800, 600)
                needs_resize = img.width > max_size[0] or img.height > max_size[1]
                if needs_resize:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                output = io.BytesIO()
                if img_format == "JPEG":
                    img.save(output, format="JPEG", optimize=True, quality=85)
                elif img_format == "PNG":
                    img.save(output, format="PNG", optimize=True)
                else:
                    img.save(output, format=img_format, optimize=True)

                output.seek(0)

                new_image = ContentFile(output.getvalue())

                self.image.save(self.image.name, new_image, save=False)

                super().save(update_fields=["image"])

            except Exception as e:
                logger.error(
                    f"Ошибка при оптимизации изображения для мема '{self.title}': {e}",
                    exc_info=True,
                )

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def dislikes_count(self):
        return self.dislikes.count()

    def get_rating(self):
        return self.likes_count - self.dislikes_count


class Like(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    meme = models.ForeignKey(
        Meme, on_delete=models.CASCADE, related_name="likes", verbose_name="Мем"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        unique_together = ["user", "meme"]
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"

    def __str__(self):
        return f"{self.user.username} лайкнул {self.meme.title}"


class Dislike(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    meme = models.ForeignKey(
        Meme, on_delete=models.CASCADE, related_name="dislikes", verbose_name="Мем"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        unique_together = ["user", "meme"]
        verbose_name = "Дизлайк"
        verbose_name_plural = "Дизлайки"

    def __str__(self):
        return f"{self.user.username} дизлайкнул {self.meme.title}"


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    meme = models.ForeignKey(
        Meme, on_delete=models.CASCADE, related_name="comments", verbose_name="Мем"
    )
    content = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return f"{self.author.username}: {self.content[:COMMENT_PREVIEW_LENGTH]}..."
