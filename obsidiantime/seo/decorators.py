from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def staff_required(view_func):
    """Декоратор для проверки, что пользователь является персоналом"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_staff:
            messages.error(request, "У вас нет прав для доступа к этой странице.")
            return redirect("main:home")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def seo_admin_required(view_func):
    """Декоратор для проверки прав доступа к SEO админке"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_staff:
            messages.error(
                request, "Доступ к SEO админке разрешен только администраторам."
            )
            return redirect("main:home")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def seo_analytics_required(view_func):
    """Декоратор для проверки прав доступа к аналитике"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_staff:
            messages.error(
                request,
                "Доступ к настройкам аналитики разрешен только администраторам.",
            )
            return redirect("main:home")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
