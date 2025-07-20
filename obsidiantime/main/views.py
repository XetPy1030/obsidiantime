from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from obsidiantime.chat.forms import CustomUserCreationForm
from obsidiantime.chat.models import Message
from obsidiantime.gallery.models import Meme

from .forms import QuoteFilterForm, QuoteForm
from .models import Quote, QuoteLike, SiteSettings


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
