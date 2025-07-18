from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Message(models.Model):
    MESSAGE_TYPES = (
        ("text", "Текстовое сообщение"),
        ("poll", "Голосование"),
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    content = models.TextField(verbose_name="Содержимое")
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        default="text",
        verbose_name="Тип сообщения",
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self):
        if self.message_type == "poll":
            return f"Голосование от {self.author.username}: {self.content[:50]}..."
        return f"{self.author.username}: {self.content[:50]}..."


class Poll(models.Model):
    message = models.OneToOneField(
        Message, on_delete=models.CASCADE, verbose_name="Сообщение"
    )
    question = models.CharField(max_length=500, verbose_name="Вопрос")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    multiple_choice = models.BooleanField(
        default=False, verbose_name="Множественный выбор"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        verbose_name = "Голосование"
        verbose_name_plural = "Голосования"

    def __str__(self):
        return self.question

    @property
    def total_votes(self):
        return PollVote.objects.filter(option__poll=self).count()


class PollOption(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Голосование",
    )
    text = models.CharField(max_length=200, verbose_name="Вариант ответа")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"

    def __str__(self):
        return self.text

    @property
    def vote_count(self):
        return self.votes.count()

    @property
    def vote_percentage(self):
        total = self.poll.total_votes
        if total == 0:
            return 0
        return round((self.vote_count / total) * 100, 1)


class PollVote(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    option = models.ForeignKey(
        PollOption,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Вариант",
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        unique_together = ["user", "option"]
        verbose_name = "Голос"
        verbose_name_plural = "Голоса"

    def __str__(self):
        return f'{self.user.username} голосует за "{self.option.text}"'
