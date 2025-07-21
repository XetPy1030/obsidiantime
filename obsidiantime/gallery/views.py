import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, MemeFilterForm, MemeUploadForm
from .models import Dislike, Like, Meme

logger = logging.getLogger(__name__)


def gallery_list(request):
    """Список мемов с фильтрацией"""
    form = MemeFilterForm(request.GET)
    memes = (
        Meme.objects.filter(is_approved=True)
        .select_related("author")
        .annotate(
            total_likes=Count("likes"),
            total_dislikes=Count("dislikes"),
            total_comments=Count("comments"),
        )
    )

    if form.is_valid():
        search = form.cleaned_data.get("search")
        sort = form.cleaned_data.get("sort")
        author = form.cleaned_data.get("author")

        if search:
            memes = memes.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        if author:
            memes = memes.filter(author__username__icontains=author)

        if sort:
            if sort == "-views":
                memes = memes.order_by("-views")
            elif sort == "title":
                memes = memes.order_by("title")
            else:
                memes = memes.order_by(sort)
        else:
            # Сортировка по умолчанию - сначала новые
            memes = memes.order_by("-created_at")
    else:
        # Если форма невалидна, все равно добавляем сортировку по умолчанию
        memes = memes.order_by("-created_at")

    # Пагинация
    paginator = Paginator(memes, 12)  # 12 мемов на страницу для красивой сетки
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Получаем информацию о лайках пользователя
    user_likes = set()
    user_dislikes = set()
    if request.user.is_authenticated:
        user_likes = set(
            Like.objects.filter(
                user=request.user, meme__in=page_obj.object_list
            ).values_list("meme_id", flat=True)
        )

        user_dislikes = set(
            Dislike.objects.filter(
                user=request.user, meme__in=page_obj.object_list
            ).values_list("meme_id", flat=True)
        )

    context = {
        "form": form,
        "page_obj": page_obj,
        "memes": page_obj.object_list,
        "user_likes": user_likes,
        "user_dislikes": user_dislikes,
    }
    return render(request, "gallery/gallery_list.html", context)


@login_required
def upload_meme(request):
    """Загрузка нового мема"""
    if request.method == "POST":
        form = MemeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save(commit=False)
            meme.author = request.user
            meme.save()
            messages.success(request, "Мем успешно загружен!")
            return redirect("gallery:meme_detail", pk=meme.pk)
    else:
        form = MemeUploadForm()

    return render(request, "gallery/upload_meme.html", {"form": form})


def meme_detail(request, pk):
    """Детальный просмотр мема"""
    meme = get_object_or_404(Meme, pk=pk, is_approved=True)

    # Увеличиваем счетчик просмотров
    meme.views += 1
    meme.save(update_fields=["views"])

    # Получаем комментарии
    comments = meme.comments.select_related("author").order_by("-created_at")

    # Проверяем реакции пользователя
    user_liked = False
    user_disliked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(user=request.user, meme=meme).exists()
        user_disliked = Dislike.objects.filter(user=request.user, meme=meme).exists()

    # Форма для комментариев
    comment_form = CommentForm()

    context = {
        "meme": meme,
        "comments": comments,
        "comment_form": comment_form,
        "user_liked": user_liked,
        "user_disliked": user_disliked,
    }
    return render(request, "gallery/meme_detail.html", context)


@login_required
@require_POST
def toggle_like(request, pk):
    """AJAX переключение лайка"""
    meme = get_object_or_404(Meme, pk=pk)

    # Удаляем дизлайк если есть
    Dislike.objects.filter(user=request.user, meme=meme).delete()

    # Переключаем лайк
    like, created = Like.objects.get_or_create(user=request.user, meme=meme)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse(
        {
            "liked": liked,
            "disliked": False,
            "likes_count": meme.likes_count,
            "dislikes_count": meme.dislikes_count,
            "rating": meme.get_rating(),
        }
    )


@login_required
@require_POST
def toggle_dislike(request, pk):
    """AJAX переключение дизлайка"""
    meme = get_object_or_404(Meme, pk=pk)

    # Удаляем лайк если есть
    Like.objects.filter(user=request.user, meme=meme).delete()

    # Переключаем дизлайк
    dislike, created = Dislike.objects.get_or_create(user=request.user, meme=meme)

    if not created:
        dislike.delete()
        disliked = False
    else:
        disliked = True

    return JsonResponse(
        {
            "liked": False,
            "disliked": disliked,
            "likes_count": meme.likes_count,
            "dislikes_count": meme.dislikes_count,
            "rating": meme.get_rating(),
        }
    )


@login_required
def add_comment(request, pk):
    """Добавление комментария к мему"""
    meme = get_object_or_404(Meme, pk=pk, is_approved=True)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.meme = meme
            comment.save()
            messages.success(request, "Комментарий добавлен!")
        else:
            messages.error(request, "Ошибка при добавлении комментария.")

    return redirect("gallery:meme_detail", pk=pk)


def top_memes(request):
    """Топ мемов по рейтингу"""
    memes = (
        Meme.objects.filter(is_approved=True)
        .select_related("author")
        .annotate(
            total_likes=Count("likes"),
            total_dislikes=Count("dislikes"),
            rating=Count("likes") - Count("dislikes"),
        )
        .order_by("-rating", "-views")
    )

    # Пагинация
    paginator = Paginator(memes, 15)  # 15 мемов на страницу
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Получаем информацию о лайках пользователя
    user_likes = set()
    user_dislikes = set()
    if request.user.is_authenticated:
        user_likes = set(
            Like.objects.filter(
                user=request.user, meme__in=page_obj.object_list
            ).values_list("meme_id", flat=True)
        )

        user_dislikes = set(
            Dislike.objects.filter(
                user=request.user, meme__in=page_obj.object_list
            ).values_list("meme_id", flat=True)
        )

    context = {
        "memes": page_obj.object_list,
        "page_obj": page_obj,
        "user_likes": user_likes,
        "user_dislikes": user_dislikes,
        "title": "Топ мемов",
    }
    return render(request, "gallery/top_memes.html", context)


@login_required
def my_memes(request):
    """Мемы пользователя"""
    memes = (
        Meme.objects.filter(author=request.user)
        .annotate(
            total_likes=Count("likes"),
            total_dislikes=Count("dislikes"),
            total_comments=Count("comments"),
        )
        .order_by("-created_at")
    )

    # Подсчитываем общую статистику через агрегацию
    user_memes_stats = Meme.objects.filter(author=request.user).aggregate(
        total_likes=Count("likes"),
        total_views=Sum("views"),
        total_comments=Count("comments"),
    )

    # Пагинация
    paginator = Paginator(memes, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "memes": page_obj.object_list,
        "title": "Мои мемы",
        "total_likes": user_memes_stats["total_likes"] or 0,
        "total_views": user_memes_stats["total_views"] or 0,
        "total_comments": user_memes_stats["total_comments"] or 0,
    }
    return render(request, "gallery/my_memes.html", context)


def random_meme(request):
    """Случайный мем"""
    meme = Meme.objects.filter(is_approved=True).order_by("?").first()

    if meme:
        return redirect("gallery:meme_detail", pk=meme.pk)
    else:
        messages.info(request, "Мемы не найдены.")
        return redirect("gallery:gallery_list")
