import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import ConsentLog, VisitEvent, Visitor
from .utils import (
    CONSENT_COOKIE,
    clean_client_data,
    get_client_ip,
    get_consent,
    get_visitor_id,
    policy_version,
    set_consent_cookies,
    truncate,
)

MAX_BODY_SIZE = 64 * 1024
MAX_EVENTS_PER_REQUEST = 50
MY_DATA_EVENTS_LIMIT = 500
EVENT_TYPES = {choice for choice, _ in VisitEvent.EVENT_TYPE_CHOICES}


def _parse_json(request):
    if len(request.body) > MAX_BODY_SIZE:
        raise ValueError("Слишком большой запрос")
    data = json.loads(request.body)
    if not isinstance(data, dict):
        raise ValueError("Ожидался JSON-объект")
    return data


def _get_visitor(request):
    visitor_id = get_visitor_id(request)
    if visitor_id is None:
        return None
    return Visitor.objects.select_related("user").filter(pk=visitor_id).first()


def _has_active_consent(request, visitor):
    return (
        visitor is not None
        and visitor.analytics_consent
        and visitor.consent_version == policy_version()
        and get_consent(request) == {"analytics": True}
    )


def _update_request_info(visitor, request):
    """Данные, которые сервер видит в самом HTTP-запросе"""
    visitor.ip_address = get_client_ip(request)
    visitor.user_agent = truncate(request.META.get("HTTP_USER_AGENT"), 1000)
    visitor.accept_language = truncate(request.META.get("HTTP_ACCEPT_LANGUAGE"), 255)
    visitor.last_seen_at = timezone.now()
    if request.user.is_authenticated:
        visitor.user = request.user


def _build_event(raw, visitor, user, ip_address):
    if not isinstance(raw, dict) or raw.get("type") not in EVENT_TYPES:
        return None
    data = raw.get("data")
    return VisitEvent(
        visitor=visitor,
        user=user,
        event_type=raw["type"],
        page_id=truncate(raw.get("page_id"), 36),
        url=truncate(raw.get("url"), 2048),
        path=truncate(raw.get("path"), 1024),
        referrer=truncate(raw.get("referrer"), 2048),
        title=truncate(raw.get("title"), 512),
        data=clean_client_data(data) if isinstance(data, dict) else {},
        ip_address=ip_address,
    )


def privacy(request):
    """Политика конфиденциальности и управление своими данными"""
    return render(request, "tracking/privacy.html")


@require_POST
def consent(request):
    """Сохраняет выбор посетителя в баннере согласия"""
    try:
        data = _parse_json(request)
    except ValueError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    analytics = data.get("analytics") is True
    visitor = _get_visitor(request)
    now = timezone.now()

    if analytics:
        with transaction.atomic():
            if visitor is None:
                visitor = Visitor(first_seen_at=now)
            _update_request_info(visitor, request)
            visitor.analytics_consent = True
            visitor.consent_version = policy_version()
            visitor.consent_updated_at = now
            visitor.save()
            ConsentLog.objects.create(
                visitor=visitor,
                action="granted",
                policy_version=policy_version(),
                ip_address=visitor.ip_address,
                user_agent=visitor.user_agent,
            )
    elif visitor is not None and visitor.analytics_consent:
        # Отзыв согласия: прекращаем сбор и удаляем всё собранное
        with transaction.atomic():
            visitor.clear_personal_data()
            visitor.analytics_consent = False
            visitor.consent_version = policy_version()
            visitor.consent_updated_at = now
            visitor.save()
            ConsentLog.objects.create(
                visitor=visitor,
                action="withdrawn",
                policy_version=policy_version(),
            )

    response = JsonResponse({"status": "ok", "consent": {"analytics": analytics}})
    set_consent_cookies(response, analytics, visitor.id if visitor else None)
    return response


@require_POST
def collect(request):
    """Принимает пачку событий и данные устройства от tracking.js"""
    visitor = _get_visitor(request)
    if not _has_active_consent(request, visitor):
        response = JsonResponse({"error": "consent_required"}, status=403)
        if get_consent(request) == {"analytics": True}:
            # Cookie говорит «согласен», а в базе согласия нет — спросим заново
            response.delete_cookie(CONSENT_COOKIE, samesite="Lax")
        return response

    try:
        data = _parse_json(request)
    except ValueError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    raw_events = data.get("events")
    if not isinstance(raw_events, list) or len(raw_events) > MAX_EVENTS_PER_REQUEST:
        return JsonResponse({"error": "invalid_events"}, status=400)

    ip_address = get_client_ip(request)
    user = request.user if request.user.is_authenticated else None
    events = [
        event
        for event in (
            _build_event(raw, visitor, user, ip_address) for raw in raw_events
        )
        if event is not None
    ]

    with transaction.atomic():
        VisitEvent.objects.bulk_create(events)
        client_info = data.get("client")
        if isinstance(client_info, dict):
            visitor.client_info = clean_client_data(client_info)
        _update_request_info(visitor, request)
        visitor.save()

    return JsonResponse({"status": "ok", "saved": len(events)})


@require_GET
def my_data(request):
    """Все данные, которые сайт хранит о текущем посетителе"""
    visitor = _get_visitor(request)
    payload = {"consent": get_consent(request), "visitor": None}

    if visitor is not None:
        events = visitor.events.all()[:MY_DATA_EVENTS_LIMIT]
        payload["visitor"] = {
            "id": visitor.id,
            "user": visitor.user.username if visitor.user else None,
            "analytics_consent": visitor.analytics_consent,
            "consent_version": visitor.consent_version,
            "consent_updated_at": visitor.consent_updated_at,
            "ip_address": visitor.ip_address,
            "user_agent": visitor.user_agent,
            "accept_language": visitor.accept_language,
            "client_info": visitor.client_info,
            "first_seen_at": visitor.first_seen_at,
            "last_seen_at": visitor.last_seen_at,
            "consent_history": [
                {
                    "action": log.get_action_display(),
                    "policy_version": log.policy_version,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at,
                }
                for log in visitor.consent_logs.all()
            ],
            "events_total": visitor.events.count(),
            "events_shown": len(events),
            "events": [
                {
                    "type": event.event_type,
                    "created_at": event.created_at,
                    "url": event.url,
                    "referrer": event.referrer,
                    "title": event.title,
                    "ip_address": event.ip_address,
                    "data": event.data,
                }
                for event in events
            ],
        }

    response = JsonResponse(
        payload, json_dumps_params={"ensure_ascii": False, "indent": 2}
    )
    if request.GET.get("download"):
        response["Content-Disposition"] = (
            'attachment; filename="obsidiantime-my-data.json"'
        )
    return response


@require_POST
def forget(request):
    """Полностью удаляет данные посетителя, включая журнал согласий"""
    visitor = _get_visitor(request)
    if visitor is not None:
        visitor.delete()

    response = JsonResponse({"status": "ok"})
    set_consent_cookies(response, analytics=False)
    return response
