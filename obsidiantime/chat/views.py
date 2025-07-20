from collections import OrderedDict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MessageForm, PollForm
from .models import Message, Poll, PollOption, PollVote


def group_messages_by_date(messages):
    """Группировка сообщений по дням"""
    grouped = OrderedDict()
    for message in messages:
        message_date = message.created_at.date()
        if message_date not in grouped:
            grouped[message_date] = []
        grouped[message_date].append(message)
    return grouped


def format_date_readable(date_obj):
    """Форматирование даты в читаемом виде"""
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    if date_obj == today:
        return "Сегодня"
    elif date_obj == yesterday:
        return "Вчера"
    else:
        # Русские названия месяцев
        months = [
            "января",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "сентября",
            "октября",
            "ноября",
            "декабря",
        ]
        return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year}"


def create_message_data(message, user_votes):
    """Создание данных сообщения для API"""
    message_data = {
        "type": "message",
        "id": message.id,
        "author": message.author.username,
        "content": message.content,
        "created_at": message.created_at.strftime("%H:%M"),
        "message_type": message.message_type,
    }

    if message.message_type == "poll" and hasattr(message, "poll"):
        poll = message.poll
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

    return message_data


def create_date_separator_data(date_obj):
    """Создание данных разделителя даты"""
    return {
        "type": "date_separator",
        "date": date_obj.strftime("%d.%m.%Y"),
        "date_readable": format_date_readable(date_obj),
    }


def process_messages_with_dates(messages_list, user_votes, is_new_messages=False):
    """Обработка сообщений с добавлением разделителей дат"""
    messages_data = []
    current_date = None
    latest_message_id = 0

    # Сортируем правильно для отображения
    ordered_messages = messages_list
    if not is_new_messages:  # Для старых сообщений нужно изменить порядок
        ordered_messages = ordered_messages[::-1]  # Используем слайсинг

    for i, msg in enumerate(ordered_messages):
        message_date = msg.created_at.date()

        # Для новых сообщений добавляем разделитель только
        # для первого сообщения нового дня
        # Для старых сообщений - как обычно при смене даты
        should_add_separator = False

        if is_new_messages:
            # Для новых сообщений: добавляем разделитель только
            # если это первое сообщение
            # и оно не сегодняшнее (сегодняшний разделитель уже должен быть на странице)
            today = timezone.now().date()
            if i == 0 and message_date != today:
                should_add_separator = True
        # Для старых сообщений: добавляем при смене даты
        elif current_date != message_date:
            should_add_separator = True

        if should_add_separator:
            date_separator = create_date_separator_data(message_date)
            messages_data.append(date_separator)
            current_date = message_date

        # Добавляем сообщение
        message_data = create_message_data(msg, user_votes)
        messages_data.append(message_data)

        # Обновляем последний ID только для реальных сообщений
        if is_new_messages:
            latest_message_id = msg.id

    return messages_data, latest_message_id


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
        .order_by("created_at")
    )

    # Пагинация
    paginator = Paginator(messages_queryset, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Группируем сообщения по дням
    grouped_messages = group_messages_by_date(page_obj.object_list)

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

    # Получаем сегодня и вчера для шаблона
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    context = {
        "page_obj": page_obj,
        "grouped_messages": grouped_messages,
        "chat_messages": page_obj.object_list,
        "message_form": message_form,
        "poll_form": poll_form,
        "user_votes": user_votes,
        "today": today,
        "yesterday": yesterday,
    }
    return render(request, "chat/chat.html", context)


@login_required
def send_message(request):
    """Отправка обычного сообщения"""
    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        # Используем request.POST для всех случаев
        form = MessageForm(request.POST)

        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.save()

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Сообщение отправлено!",
                        "message_id": message.id,
                    }
                )
            else:
                messages.success(request, "Сообщение отправлено!")
        elif is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Ошибка в форме: " + str(form.errors),
                }
            )
        else:
            messages.error(request, "Ошибка при отправке сообщения.")

    return redirect("chat:chat")


@login_required
def create_poll(request):
    """Создание голосования"""
    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        # Используем request.POST для всех случаев
        form = PollForm(request.POST)

        if form.is_valid():
            try:
                poll = form.save(request.user)

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Голосование создано!",
                            "poll_id": poll.id,
                        }
                    )
                else:
                    messages.success(request, "Голосование создано!")
            except Exception as e:
                if is_ajax:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": f"Ошибка при создании голосования: {e}",
                        }
                    )
                else:
                    messages.error(request, f"Ошибка при создании голосования: {e}")
        elif is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Ошибка в форме: " + str(form.errors),
                }
            )
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

    # Получаем информацию о том, за какие варианты пользователь проголосовал
    user_voted_options = set(
        PollVote.objects.filter(user=request.user, option__poll=poll).values_list(
            "option_id", flat=True
        )
    )

    # Возвращаем обновленную статистику
    poll_data = {"voted": voted, "total_votes": poll.total_votes, "options": []}

    for opt in poll.options.all():
        poll_data["options"].append(
            {
                "id": opt.id,
                "vote_count": opt.vote_count,
                "vote_percentage": opt.vote_percentage,
                "user_voted": opt.id
                in user_voted_options,  # Добавляем информацию о голосе пользователя
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
    last_message_id = int(request.GET.get("last_id", 0))
    before_id = request.GET.get("before_id")

    # Константы
    messages_per_page = 20

    # Получаем базовый QuerySet
    base_queryset = Message.objects.select_related("author").prefetch_related(
        Prefetch("poll", queryset=Poll.objects.prefetch_related("options"))
    )

    # Определяем тип запроса и получаем сообщения
    if before_id:
        # Загрузка старых сообщений
        messages_queryset = base_queryset.filter(id__lt=before_id).order_by(
            "-created_at"
        )[:messages_per_page]
        has_more = messages_queryset.count() == messages_per_page
        is_new_messages = False
    else:
        # Загрузка новых сообщений
        messages_queryset = base_queryset.filter(id__gt=last_message_id).order_by(
            "created_at"
        )[:messages_per_page]
        has_more = False
        is_new_messages = True

    # Получаем голоса пользователя для опросов
    user_votes = set()
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

    # Получаем список сообщений для обработки
    messages_list = list(messages_queryset)

    # Обрабатываем сообщения с разделителями дат
    messages_data, _ = process_messages_with_dates(
        messages_list, user_votes, is_new_messages
    )

    # Правильно определяем последний ID сообщения
    if is_new_messages and messages_list:
        latest_message_id = max(msg.id for msg in messages_list)
    else:
        latest_message_id = last_message_id

    return JsonResponse(
        {
            "messages": messages_data,
            "last_id": latest_message_id,
            "has_more": has_more,
        }
    )
