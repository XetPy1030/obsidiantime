# """
# Кастомные метрики для Prometheus
# """
# from prometheus_client import Counter, Histogram, Gauge
#
# # Метрики для пользователей
# user_registrations = Counter(
#     'django_user_registrations_total',
#     'Total number of user registrations',
#     ['status']
# )
#
# user_logins = Counter(
#     'django_user_logins_total',
#     'Total number of user logins',
#     ['status']
# )
#
# # Метрики для галереи
# meme_uploads = Counter(
#     'django_meme_uploads_total',
#     'Total number of meme uploads',
#     ['status']
# )
#
# meme_views = Counter(
#     'django_meme_views_total',
#     'Total number of meme views',
#     ['meme_id']
# )
#
# # Метрики для чата
# chat_messages = Counter(
#     'django_chat_messages_total',
#     'Total number of chat messages',
#     ['room']
# )
#
# # Метрики для обратной связи
# feedback_submissions = Counter(
#     'django_feedback_submissions_total',
#     'Total number of feedback submissions',
#     ['type']
# )
#
# # Метрики производительности
# request_duration = Histogram(
#     'django_request_duration_seconds',
#     'Request duration in seconds',
#     ['view', 'method']
# )
#
# database_query_duration = Histogram(
#     'django_database_query_duration_seconds',
#     'Database query duration in seconds',
#     ['operation']
# )
#
# # Метрики состояния системы
# active_users = Gauge(
#     'django_active_users',
#     'Number of active users'
# )
#
# total_memes = Gauge(
#     'django_total_memes',
#     'Total number of memes in the system'
# )
#
# total_feedback = Gauge(
#     'django_total_feedback',
#     'Total number of feedback items'
# )
