import json
import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from obsidiantime.chat.forms import CustomUserCreationForm
from obsidiantime.chat.models import Message
from obsidiantime.gallery.models import Meme

from .forms import FeedbackCommentForm, FeedbackForm, QuoteFilterForm, QuoteForm
from .models import Feedback, FeedbackComment, Quote, QuoteLike, SiteSettings

logger = logging.getLogger(__name__)


def home(request):
    """Главная страница с рикроллом и чатом"""
    settings = SiteSettings.get_settings()

    # Последние сообщения из чата для главной страницы
    latest_messages = Message.objects.select_related("author").order_by("-created_at")[
        :10
    ]

    context = {
        "settings": settings,
        "latest_messages": latest_messages,
    }
    return render(request, "main/home.html", context)


def quotes_list(request):
    """Список цитат с фильтрацией"""
    form = QuoteFilterForm(request.GET)
    quotes = Quote.objects.filter(is_approved=True).select_related("added_by")

    if form.is_valid():
        search = form.cleaned_data.get("search")
        sort = form.cleaned_data.get("sort")
        author = form.cleaned_data.get("author")

        if search:
            quotes = quotes.filter(
                Q(text__icontains=search) | Q(author__icontains=search)
            )

        if author:
            quotes = quotes.filter(author__icontains=author)

        if sort:
            quotes = quotes.order_by(sort)
        else:
            # Сортировка по умолчанию - сначала новые
            quotes = quotes.order_by("-created_at")
    else:
        # Если форма невалидна, все равно добавляем сортировку по умолчанию
        quotes = quotes.order_by("-created_at")

    # Пагинация
    paginator = Paginator(quotes, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "form": form,
        "page_obj": page_obj,
        "quotes": page_obj.object_list,
    }
    return render(request, "main/quotes_list.html", context)


@login_required
def add_quote(request):
    """Добавление новой цитаты"""
    if request.method == "POST":
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.added_by = request.user
            quote.save()
            messages.success(request, "Цитата успешно добавлена!")
            return redirect("main:quotes_list")
    else:
        form = QuoteForm()

    return render(request, "main/add_quote.html", {"form": form})


def quote_detail(request, pk):
    """Детальный просмотр цитаты"""
    quote = get_object_or_404(Quote, pk=pk, is_approved=True)

    # Увеличиваем счетчик просмотров
    quote.views += 1
    quote.save(update_fields=["views"])

    # Проверяем, лайкнул ли пользователь эту цитату
    user_liked = False
    if request.user.is_authenticated:
        user_liked = QuoteLike.objects.filter(user=request.user, quote=quote).exists()

    context = {
        "quote": quote,
        "user_liked": user_liked,
    }
    return render(request, "main/quote_detail.html", context)


@login_required
@require_POST
def toggle_quote_like(request, pk):
    """AJAX переключение лайка цитаты"""
    quote = get_object_or_404(Quote, pk=pk)
    like, created = QuoteLike.objects.get_or_create(user=request.user, quote=quote)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({"liked": liked, "likes_count": quote.likes_count})


class CustomLoginView(LoginView):
    """Кастомная страница входа"""

    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or "/"


def register(request):
    """Регистрация пользователя"""
    if request.user.is_authenticated:
        return redirect("main:home")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.username}!")
            return redirect("main:home")
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/register.html", {"form": form})


def about(request):
    """Страница о проекте"""

    settings = SiteSettings.get_settings()

    # Статистика
    users_count = User.objects.count()
    messages_count = Message.objects.count()
    memes_count = Meme.objects.filter(is_approved=True).count()
    quotes_count = Quote.objects.filter(is_approved=True).count()

    context = {
        "settings": settings,
        "users_count": users_count,
        "messages_count": messages_count,
        "memes_count": memes_count,
        "quotes_count": quotes_count,
    }
    return render(request, "main/about.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def api_errors(request):
    """
    API endpoint для получения ошибок с фронтенда
    """
    try:
        data = json.loads(request.body)

        # Логируем ошибку
        logger.error(
            "Frontend error: %s - %s",
            data.get("type", "unknown"),
            data.get("message", "No message"),
            extra={
                "error_data": data,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "ip": request.META.get("REMOTE_ADDR", ""),
                "user_id": request.user.id if request.user.is_authenticated else None,
            },
        )

        return JsonResponse({"status": "received"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error("Error processing frontend error: %s", str(e))
        return JsonResponse({"error": "Internal server error"}, status=500)


def feedback(request):
    """Страница обратной связи"""
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback_obj = form.save(commit=False)
            if request.user.is_authenticated:
                feedback_obj.user = request.user
            feedback_obj.save()
            messages.success(
                request,
                "Спасибо за ваше обращение! Мы рассмотрим его в ближайшее время.",
            )
            return redirect("main:feedback")
    else:
        # Предзаполняем форму для авторизованных пользователей
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                "name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
            }
        form = FeedbackForm(initial=initial_data)

    # Статистика для мотивации
    total_feedback = Feedback.objects.count()
    resolved_feedback = Feedback.objects.filter(
        status__in=["resolved", "closed"]
    ).count()

    context = {
        "form": form,
        "total_feedback": total_feedback,
        "resolved_feedback": resolved_feedback,
    }
    return render(request, "main/feedback.html", context)


@login_required
def my_feedback(request):
    """Страница с обращениями пользователя"""
    feedback_list = (
        Feedback.objects.filter(user=request.user)
        .annotate(
            total_comments=Count("comments"),
            public_comments=Count("comments", filter=Q(comments__is_internal=False)),
        )
        .order_by("-created_at")
    )

    # Статистика для пользователя
    total_feedback = feedback_list.count()
    resolved_feedback = feedback_list.filter(status__in=["resolved", "closed"]).count()
    new_feedback = feedback_list.filter(status="new").count()
    in_progress_feedback = feedback_list.filter(status="in_progress").count()

    # Пагинация
    paginator = Paginator(feedback_list, 10)  # 10 обращений на страницу
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "feedback_list": page_obj.object_list,
        "page_obj": page_obj,
        "total_feedback": total_feedback,
        "resolved_feedback": resolved_feedback,
        "new_feedback": new_feedback,
        "in_progress_feedback": in_progress_feedback,
    }
    return render(request, "main/my_feedback.html", context)


@login_required
def feedback_detail(request, pk):
    """Детальный просмотр обращения"""
    feedback = get_object_or_404(Feedback, pk=pk)

    # Проверяем права доступа
    if not request.user.is_staff and feedback.user != request.user:
        messages.error(request, "У вас нет прав для просмотра этого обращения.")
        return redirect("main:my_feedback")

    # Пагинация комментариев
    if request.user.is_staff:
        comments_list = feedback.comments.all().order_by("-created_at")
    else:
        comments_list = feedback.comments.filter(is_internal=False).order_by(
            "-created_at"
        )

    paginator = Paginator(comments_list, 10)  # 10 комментариев на страницу
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Форма для добавления комментария
    if request.method == "POST":
        comment_form = FeedbackCommentForm(request.POST, user=request.user)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.feedback = feedback
            comment.author = request.user
            comment.save()
            messages.success(request, "Комментарий добавлен!")
            return redirect("main:feedback_detail", pk=pk)
        else:
            # Если есть ошибки в форме, показываем её
            show_comment_form = True
    else:
        comment_form = FeedbackCommentForm(user=request.user)
        show_comment_form = False

    # Определяем, может ли пользователь комментировать
    can_comment = request.user.is_staff or feedback.user == request.user

    context = {
        "feedback": feedback,
        "comments": page_obj.object_list,
        "page_obj": page_obj,
        "comment_form": comment_form,
        "can_comment": can_comment,
        "show_comment_form": show_comment_form,
    }
    return render(request, "main/feedback_detail.html", context)


@login_required
def admin_feedback_list(request):
    """Административная панель для управления обращениями"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для доступа к административной панели.")
        return redirect("main:home")

    # Фильтры
    status_filter = request.GET.get("status", "")
    feedback_type_filter = request.GET.get("feedback_type", "")
    search_query = request.GET.get("search", "")

    feedback_list = Feedback.objects.all()

    if status_filter:
        feedback_list = feedback_list.filter(status=status_filter)
    if feedback_type_filter:
        feedback_list = feedback_list.filter(feedback_type=feedback_type_filter)
    if search_query:
        feedback_list = feedback_list.filter(
            Q(subject__icontains=search_query)
            | Q(message__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    # Аннотации для статистики
    feedback_list = feedback_list.annotate(
        total_comments=Count("comments"),
        admin_comments=Count("comments", filter=Q(comments__comment_type="admin")),
        user_comments=Count("comments", filter=Q(comments__comment_type="user")),
    ).order_by("-created_at")

    # Статистика
    total_feedback = Feedback.objects.count()
    new_feedback = Feedback.objects.filter(status="new").count()
    in_progress_feedback = Feedback.objects.filter(status="in_progress").count()
    resolved_feedback = Feedback.objects.filter(status="resolved").count()
    closed_feedback = Feedback.objects.filter(status="closed").count()

    # Пагинация
    paginator = Paginator(feedback_list, 20)  # 20 обращений на страницу
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "feedback_list": page_obj.object_list,
        "page_obj": page_obj,
        "total_feedback": total_feedback,
        "new_feedback": new_feedback,
        "in_progress_feedback": in_progress_feedback,
        "resolved_feedback": resolved_feedback,
        "closed_feedback": closed_feedback,
        "status_filter": status_filter,
        "feedback_type_filter": feedback_type_filter,
        "search_query": search_query,
    }
    return render(request, "main/admin_feedback_list.html", context)


@login_required
def admin_feedback_detail(request, pk):
    """Административный детальный просмотр обращения"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для доступа к административной панели.")
        return redirect("main:home")

    feedback = get_object_or_404(Feedback, pk=pk)

    # Пагинация комментариев
    comments_list = feedback.comments.all().order_by("-created_at")
    paginator = Paginator(comments_list, 10)  # 10 комментариев на страницу
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Форма для добавления комментария
    if request.method == "POST":
        comment_form = FeedbackCommentForm(request.POST, user=request.user)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.feedback = feedback
            comment.author = request.user
            comment.save()

            # Проверяем, это AJAX запрос или обычный
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Комментарий добавлен!",
                        "comment": {
                            "author_name": comment.author.get_full_name()
                            or comment.author.username,
                            "comment": comment.comment,
                            "created_at": comment.created_at.strftime("%d.%m.%Y %H:%M"),
                            "is_admin_comment": comment.is_admin_comment,
                            "is_internal": comment.is_internal,
                        },
                    }
                )
            else:
                messages.success(request, "Комментарий добавлен!")
                return redirect("main:admin_feedback_detail", pk=pk)
        else:
            # Если есть ошибки в форме, показываем её
            show_comment_form = True
    else:
        comment_form = FeedbackCommentForm(user=request.user)
        show_comment_form = False

    context = {
        "feedback": feedback,
        "comments": page_obj.object_list,
        "page_obj": page_obj,
        "comment_form": comment_form,
        "show_comment_form": show_comment_form,
    }
    return render(request, "main/admin_feedback_detail.html", context)


@login_required
def change_feedback_status(request, pk):
    """AJAX изменение статуса обращения"""
    if not request.user.is_staff:
        return JsonResponse(
            {"success": False, "message": "Недостаточно прав"}, status=403
        )

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Метод не разрешен"}, status=405
        )

    try:
        feedback = get_object_or_404(Feedback, pk=pk)

        data = json.loads(request.body)
        new_status = data.get("status")

        if not new_status or new_status not in dict(Feedback.STATUS_CHOICES):
            return JsonResponse(
                {"success": False, "message": "Неверный статус"}, status=400
            )

        # Изменяем статус
        old_status = feedback.status
        feedback.status = new_status
        feedback.save()

        # Добавляем комментарий об изменении статуса
        status_names = dict(Feedback.STATUS_CHOICES)
        comment_text = (
            f"Статус изменен с '{status_names[old_status]}' "
            f"на '{status_names[new_status]}'"
        )

        FeedbackComment.objects.create(
            feedback=feedback,
            author=request.user,
            comment=comment_text,
            is_internal=True,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Статус успешно изменен",
                "new_status": new_status,
                "new_status_display": status_names[new_status],
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Неверный формат данных"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Ошибка: {e!s}"}, status=500)
