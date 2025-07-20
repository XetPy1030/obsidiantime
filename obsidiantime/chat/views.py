import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import MessageForm, PollForm
from .models import Message, Poll, PollOption, PollVote


def chat_view(request):
    """Основной чат"""
    # Получаем сообщения с предзагрузкой связанных данных
    messages_queryset = (
        Message.objects.select_related("author")
        .prefetch_related(
            Prefetch(
                "poll",
                queryset=Poll.objects.prefetch_related(
                    Prefetch(
                        "options", queryset=PollOption.objects.prefetch_related("votes")
                    )
                ),
            )
        )
        .order_by("created_at")  # Изменено на хронологический порядок
    )

    # Пагинация
    paginator = Paginator(messages_queryset, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Формы для отправки сообщений
    message_form = MessageForm()
    poll_form = PollForm()

    # Получаем информацию о голосах пользователя
    user_votes = {}
    if request.user.is_authenticated:
        votes = PollVote.objects.filter(
            user=request.user, option__poll__message__in=page_obj.object_list
        ).select_related("option")
        user_votes = {vote.option_id: True for vote in votes}

    context = {
        "page_obj": page_obj,
        "chat_messages": page_obj.object_list,
        "message_form": message_form,
        "poll_form": poll_form,
        "user_votes": user_votes,
    }
    return render(request, "chat/chat.html", context)


@login_required
def send_message(request):
    """Отправка обычного сообщения"""
    if request.method == "POST":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # AJAX запрос
            try:
                data = json.loads(request.body)
                form = MessageForm(data)
                if form.is_valid():
                    message = form.save(commit=False)
                    message.author = request.user
                    message.save()
                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Сообщение отправлено!",
                            "message_id": message.id,
                        }
                    )
                else:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Ошибка в форме: " + str(form.errors),
                        }
                    )
            except json.JSONDecodeError:
                return JsonResponse(
                    {"success": False, "error": "Неверный формат данных"}
                )
        else:
            # Обычный POST запрос
            form = MessageForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.author = request.user
                message.save()
                messages.success(request, "Сообщение отправлено!")
            else:
                messages.error(request, "Ошибка при отправке сообщения.")

    return redirect("chat:chat")


@login_required
def create_poll(request):
    """Создание голосования"""
    if request.method == "POST":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # AJAX запрос
            try:
                data = json.loads(request.body)
                form = PollForm(data)
                if form.is_valid():
                    try:
                        poll = form.save(request.user)
                        return JsonResponse(
                            {
                                "success": True,
                                "message": "Голосование создано!",
                                "poll_id": poll.id,
                            }
                        )
                    except Exception as e:
                        return JsonResponse(
                            {
                                "success": False,
                                "error": f"Ошибка при создании голосования: {e}",
                            }
                        )
                else:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Ошибка в форме: " + str(form.errors),
                        }
                    )
            except json.JSONDecodeError:
                return JsonResponse(
                    {"success": False, "error": "Неверный формат данных"}
                )
        else:
            # Обычный POST запрос
            form = PollForm(request.POST)
            if form.is_valid():
                try:
                    poll = form.save(request.user)
                    messages.success(request, "Голосование создано!")
                except Exception as e:
                    messages.error(request, f"Ошибка при создании голосования: {e}")
            else:
                messages.error(request, "Ошибка в форме голосования.")

    return redirect("chat:chat")


@login_required
@require_POST
def vote_poll(request, poll_id, option_id):
    """AJAX голосование"""
    poll = get_object_or_404(Poll, id=poll_id, is_active=True)
    option = get_object_or_404(PollOption, id=option_id, poll=poll)

    # Проверяем, голосовал ли уже пользователь
    existing_votes = PollVote.objects.filter(user=request.user, option__poll=poll)

    if not poll.multiple_choice and existing_votes.exists():
        # Если не множественный выбор, удаляем предыдущий голос
        existing_votes.delete()

    # Проверяем, голосовал ли за этот вариант
    vote, created = PollVote.objects.get_or_create(user=request.user, option=option)

    if not created:
        # Если уже голосовал за этот вариант, отменяем голос
        vote.delete()
        voted = False
    else:
        voted = True

    # Возвращаем обновленную статистику
    poll_data = {"voted": voted, "total_votes": poll.total_votes, "options": []}

    for opt in poll.options.all():
        poll_data["options"].append(
            {
                "id": opt.id,
                "vote_count": opt.vote_count,
                "vote_percentage": opt.vote_percentage,
            }
        )

    return JsonResponse(poll_data)


def poll_detail(request, poll_id):
    """Детальный просмотр голосования"""
    poll = get_object_or_404(Poll, id=poll_id)

    # Получаем все голоса с пользователями
    votes_by_option = {}
    for option in poll.options.all():
        votes_by_option[option.id] = option.votes.select_related("user").all()

    # Проверяем, голосовал ли текущий пользователь
    user_votes = []
    if request.user.is_authenticated:
        user_votes = PollVote.objects.filter(
            user=request.user, option__poll=poll
        ).values_list("option_id", flat=True)

    context = {
        "poll": poll,
        "votes_by_option": votes_by_option,
        "user_votes": user_votes,
    }
    return render(request, "chat/poll_detail.html", context)


@login_required
@require_POST
def close_poll(request, poll_id):
    """Закрытие голосования (только автор или админ)"""
    poll = get_object_or_404(Poll, id=poll_id)

    # Проверяем права доступа
    if request.user == poll.message.author or request.user.is_staff:
        poll.is_active = False
        poll.save()
        messages.success(request, "Голосование закрыто.")
    else:
        messages.error(request, "У вас нет прав для закрытия этого голосования.")

    return redirect("chat:chat")


def chat_api_messages(request):
    """API для получения сообщений (для AJAX обновления)"""
    last_message_id = request.GET.get("last_id", 0)
    before_id = request.GET.get("before_id")

    # Константы
    messages_per_page = 20

    # Получаем сообщения
    if before_id:
        # Загрузка старых сообщений
        messages_queryset = (
            Message.objects.filter(id__lt=before_id)
            .select_related("author")
            .prefetch_related(
                Prefetch("poll", queryset=Poll.objects.prefetch_related("options"))
            )
            .order_by("-created_at")[:messages_per_page]
        )
        has_more = messages_queryset.count() == messages_per_page
    else:
        # Загрузка новых сообщений
        messages_queryset = (
            Message.objects.filter(id__gt=last_message_id)
            .select_related("author")
            .prefetch_related(
                Prefetch("poll", queryset=Poll.objects.prefetch_related("options"))
            )
            .order_by("created_at")[:messages_per_page]
        )
        has_more = False

    messages_data = []
    latest_message_id = last_message_id

    # Получаем голоса пользователя для опросов
    user_votes = {}
    if request.user.is_authenticated:
        poll_ids = [
            msg.poll.id
            for msg in messages_queryset
            if hasattr(msg, "poll") and msg.poll
        ]
        if poll_ids:
            votes = PollVote.objects.filter(
                user=request.user, option__poll_id__in=poll_ids
            ).values_list("option_id", flat=True)
            user_votes = set(votes)

    for msg in messages_queryset:
        if not before_id:  # Только для новых сообщений
            latest_message_id = msg.id

        message_data = {
            "id": msg.id,
            "author": msg.author.username,
            "content": msg.content,
            "created_at": msg.created_at.strftime("%H:%M"),
            "message_type": msg.message_type,
        }

        if msg.message_type == "poll" and hasattr(msg, "poll"):
            poll = msg.poll
            message_data["poll"] = {
                "id": poll.id,
                "question": poll.question,
                "is_active": poll.is_active,
                "multiple_choice": poll.multiple_choice,
                "total_votes": poll.total_votes,
                "options": [
                    {
                        "id": opt.id,
                        "text": opt.text,
                        "vote_count": opt.vote_count,
                        "vote_percentage": opt.vote_percentage,
                        "voted": opt.id in user_votes,
                    }
                    for opt in poll.options.all()
                ],
            }

        messages_data.append(message_data)

    return JsonResponse(
        {
            "messages": messages_data,
            "last_id": latest_message_id,
            "has_more": has_more,
        }
    )
