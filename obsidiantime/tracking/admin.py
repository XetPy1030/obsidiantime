import json

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import ConsentLog, VisitEvent, Visitor

USER_AGENT_PREVIEW_LENGTH = 60


class ReadOnlyAdminMixin:
    """Собранные данные только просматриваются, но не редактируются"""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


def pretty_json(value):
    return format_html(
        '<pre style="white-space: pre-wrap; max-width: 900px;">{}</pre>',
        json.dumps(value, ensure_ascii=False, indent=2),
    )


class ConsentLogInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = ConsentLog
    extra = 0
    fields = ["action", "policy_version", "ip_address", "created_at"]
    readonly_fields = fields


@admin.register(Visitor)
class VisitorAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "short_id",
        "user",
        "analytics_consent",
        "ip_address",
        "user_agent_preview",
        "events_link",
        "first_seen_at",
        "last_seen_at",
    ]
    list_filter = ["analytics_consent", "consent_version", "last_seen_at"]
    search_fields = ["id", "ip_address", "user_agent", "user__username"]
    date_hierarchy = "last_seen_at"
    list_select_related = ["user"]
    inlines = [ConsentLogInline]

    fieldsets = (
        (
            "Посетитель",
            {
                "fields": ("id", "user", "first_seen_at", "last_seen_at"),
            },
        ),
        (
            "Согласие",
            {
                "fields": (
                    "analytics_consent",
                    "consent_version",
                    "consent_updated_at",
                ),
            },
        ),
        (
            "Данные запроса",
            {
                "fields": ("ip_address", "user_agent", "accept_language"),
            },
        ),
        (
            "Браузер и устройство",
            {
                "fields": ("client_info_pretty",),
            },
        ),
    )
    readonly_fields = [
        "id",
        "user",
        "first_seen_at",
        "last_seen_at",
        "analytics_consent",
        "consent_version",
        "consent_updated_at",
        "ip_address",
        "user_agent",
        "accept_language",
        "client_info_pretty",
    ]

    def short_id(self, obj):
        return str(obj.id)[:8]

    short_id.short_description = "ID"

    def user_agent_preview(self, obj):
        if len(obj.user_agent) > USER_AGENT_PREVIEW_LENGTH:
            return f"{obj.user_agent[:USER_AGENT_PREVIEW_LENGTH]}..."
        return obj.user_agent

    user_agent_preview.short_description = "User-Agent"

    def events_link(self, obj):
        url = reverse("admin:tracking_visitevent_changelist")
        return format_html(
            '<a href="{}?visitor__id__exact={}">События</a>', url, obj.id
        )

    events_link.short_description = "События"

    def client_info_pretty(self, obj):
        return pretty_json(obj.client_info)

    client_info_pretty.short_description = "Данные браузера и устройства"


@admin.register(VisitEvent)
class VisitEventAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "created_at",
        "event_type",
        "path",
        "visitor_link",
        "user",
        "ip_address",
    ]
    list_filter = ["event_type", "created_at"]
    search_fields = ["path", "url", "referrer", "ip_address", "user__username"]
    date_hierarchy = "created_at"
    list_select_related = ["visitor", "user"]
    fields = [
        "created_at",
        "event_type",
        "visitor_link",
        "user",
        "page_id",
        "url",
        "path",
        "title",
        "referrer",
        "ip_address",
        "data_pretty",
    ]
    readonly_fields = fields

    def visitor_link(self, obj):
        url = reverse("admin:tracking_visitor_change", args=[obj.visitor_id])
        return format_html('<a href="{}">{}</a>', url, str(obj.visitor_id)[:8])

    visitor_link.short_description = "Посетитель"

    def data_pretty(self, obj):
        return pretty_json(obj.data)

    data_pretty.short_description = "Данные"


@admin.register(ConsentLog)
class ConsentLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["created_at", "action", "policy_version", "visitor", "ip_address"]
    list_filter = ["action", "policy_version", "created_at"]
    search_fields = ["visitor__id", "ip_address"]
    date_hierarchy = "created_at"
    fields = [
        "created_at",
        "action",
        "policy_version",
        "visitor",
        "ip_address",
        "user_agent",
    ]
    readonly_fields = fields
