from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from PIL import Image

# Constants
COMMENT_PREVIEW_LENGTH = 50


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
        super().save(*args, **kwargs)

        # Оптимизируем изображение
        if self.image:
            img = Image.open(self.image.path)

            # Изменяем размер если изображение слишком большое
            max_size = (800, 600)
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(self.image.path, optimize=True, quality=85)

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
