# """
# Middleware для отслеживания кастомных метрик
# """
# import time
# from django.utils.deprecation import MiddlewareMixin
# from .metrics import request_duration, user_logins, meme_views
#
#
# class MetricsMiddleware(MiddlewareMixin):
#     """
#     Middleware для отслеживания метрик запросов
#     """
#
#     def process_request(self, request):
#         request.start_time = time.time()
#
#     def process_response(self, request, response):
#         if hasattr(request, 'start_time'):
#             duration = time.time() - request.start_time
#             view_name = getattr(request.resolver_match, 'view_name', 'unknown')
#             method = request.method.lower()
#
#             request_duration.labels(
#                 view=view_name,
#                 method=method
#             ).observe(duration)
#
#         return response
#
#
# class UserMetricsMiddleware(MiddlewareMixin):
#     """
#     Middleware для отслеживания метрик пользователей
#     """
#
#     def process_request(self, request):
#         # Отслеживаем логины пользователей
#         if request.path == '/auth/login/' and request.method == 'POST':
#             if request.user.is_authenticated:
#                 user_logins.labels(status='success').inc()
#             else:
#                 user_logins.labels(status='failed').inc()
#
#
# class MemeMetricsMiddleware(MiddlewareMixin):
#     """
#     Middleware для отслеживания метрик мемов
#     """
#
#     def process_request(self, request):
#         # Отслеживаем просмотры мемов
#         if '/gallery/meme/' in request.path and request.method == 'GET':
#             # Извлекаем ID мема из URL
#             path_parts = request.path.split('/')
#             if len(path_parts) > 3 and path_parts[-2] == 'meme':
#                 meme_id = path_parts[-1]
#                 meme_views.labels(meme_id=meme_id).inc()
