# """
# Сигналы для отслеживания событий в приложении
# """
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from django.contrib.auth.models import User
# from django.contrib.auth.signals import user_logged_in, user_logged_out
# from obsidiantime.gallery.models import Meme
# from obsidiantime.main.models import Feedback
# from .metrics import (
#     user_registrations, meme_uploads, feedback_submissions,
#     total_memes, total_feedback, active_users
# )
#
#
# @receiver(post_save, sender=User)
# def track_user_registration(sender, instance, created, **kwargs):
#     """Отслеживает регистрацию новых пользователей"""
#     if created:
#         user_registrations.labels(status='success').inc()
#         # Обновляем метрику активных пользователей
#         active_users_count = User.objects.filter(is_active=True).count()
#         active_users.set(active_users_count)
#
#
# @receiver(user_logged_in)
# def track_user_login(sender, request, user, **kwargs):
#     """Отслеживает успешные логины пользователей"""
#     user_logins.labels(status='success').inc()
#
#
# @receiver(post_save, sender=Meme)
# def track_meme_upload(sender, instance, created, **kwargs):
#     """Отслеживает загрузку мемов"""
#     if created:
#         meme_uploads.labels(status='success').inc()
#         # Обновляем метрику общего количества мемов
#         memes_count = Meme.objects.count()
#         total_memes.set(memes_count)
#
#
# @receiver(post_delete, sender=Meme)
# def track_meme_deletion(sender, instance, **kwargs):
#     """Отслеживает удаление мемов"""
#     meme_uploads.labels(status='deleted').inc()
#     # Обновляем метрику общего количества мемов
#     memes_count = Meme.objects.count()
#     total_memes.set(memes_count)
#
#
# @receiver(post_save, sender=Feedback)
# def track_feedback_submission(sender, instance, created, **kwargs):
#     """Отслеживает отправку обратной связи"""
#     if created:
#         feedback_submissions.labels(type=instance.type).inc()
#         # Обновляем метрику общего количества обратной связи
#         feedback_count = Feedback.objects.count()
#         total_feedback.set(feedback_count)
#
#
# # Импортируем user_logins из metrics
# from .metrics import user_logins
