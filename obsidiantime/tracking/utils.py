import ipaddress
import math
import uuid

from django.conf import settings

CONSENT_COOKIE = "ot_consent"
VISITOR_COOKIE = "ot_vid"
COOKIE_MAX_AGE = 365 * 24 * 60 * 60

# Ограничения на данные, присылаемые браузером
MAX_STRING_LENGTH = 500
MAX_COLLECTION_ITEMS = 50
MAX_DEPTH = 4


def policy_version():
    return settings.TRACKING["POLICY_VERSION"]


def get_consent(request):
    """
    Возвращает выбор посетителя из cookie: {"analytics": bool}
    или None, если выбора нет или он сделан для старой версии политики.
    """
    raw = request.COOKIES.get(CONSENT_COOKIE, "")
    version, _, analytics = raw.rpartition(":")
    if version != policy_version() or analytics not in ("0", "1"):
        return None
    return {"analytics": analytics == "1"}


def set_consent_cookies(response, analytics, visitor_id=None):
    secure = settings.SESSION_COOKIE_SECURE
    response.set_cookie(
        CONSENT_COOKIE,
        f"{policy_version()}:{int(analytics)}",
        max_age=COOKIE_MAX_AGE,
        samesite="Lax",
        secure=secure,
    )
    if visitor_id:
        response.set_cookie(
            VISITOR_COOKIE,
            str(visitor_id),
            max_age=COOKIE_MAX_AGE,
            samesite="Lax",
            secure=secure,
            httponly=True,
        )
    else:
        response.delete_cookie(VISITOR_COOKIE, samesite="Lax")


def get_visitor_id(request):
    try:
        return uuid.UUID(request.COOKIES.get(VISITOR_COOKIE, ""))
    except ValueError:
        return None


def get_client_ip(request):
    """
    IP клиента с учётом обратных прокси.

    Каждый прокси дописывает адрес в конец X-Forwarded-For, поэтому клиентский
    адрес — N-й с конца, где N = количество наших прокси (TRACKING["PROXY_COUNT"]).
    Значения левее клиент может подделать, поэтому им не доверяем.
    """
    proxy_count = settings.TRACKING["PROXY_COUNT"]
    candidate = request.META.get("REMOTE_ADDR", "")
    if proxy_count > 0:
        forwarded = [
            part.strip()
            for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
            if part.strip()
        ]
        if forwarded:
            candidate = forwarded[-min(proxy_count, len(forwarded))]
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def truncate(value, length):
    return str(value or "")[:length]


def clean_client_data(value, depth=0):
    """Оставляет только JSON-примитивы и ограничивает размер вложенных данных"""
    if isinstance(value, float) and not math.isfinite(value):
        # NaN и Infinity не сохраняются в jsonb
        return None
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return value[:MAX_STRING_LENGTH]
    if depth >= MAX_DEPTH or not isinstance(value, list | dict):
        return None
    if isinstance(value, list):
        return [
            clean_client_data(item, depth + 1) for item in value[:MAX_COLLECTION_ITEMS]
        ]
    return {
        str(key)[:100]: clean_client_data(item, depth + 1)
        for key, item in list(value.items())[:MAX_COLLECTION_ITEMS]
    }
