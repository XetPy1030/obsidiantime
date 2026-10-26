import json
from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import ConsentLog, VisitEvent, Visitor
from .utils import (
    CONSENT_COOKIE,
    VISITOR_COOKIE,
    clean_client_data,
    get_client_ip,
    policy_version,
)


class TrackingTestCase(TestCase):
    def post_json(self, name, data, **extra):
        return self.client.post(
            reverse(name),
            data=json.dumps(data),
            content_type="application/json",
            **extra,
        )

    def accept(self):
        response = self.post_json("tracking:consent", {"analytics": True})
        self.assertEqual(response.status_code, 200)
        return Visitor.objects.get()

    def pageview(self, **overrides):
        event = {
            "type": "pageview",
            "page_id": "page-1",
            "url": "http://testserver/quotes/?utm_source=vk",
            "path": "/quotes/",
            "referrer": "https://vk.com/",
            "title": "Цитаты",
            "data": {"utm": {"utm_source": "vk"}},
        }
        event.update(overrides)
        return event


class ConsentTests(TrackingTestCase):
    def test_accept_creates_visitor_log_and_cookies(self):
        response = self.post_json(
            "tracking:consent",
            {"analytics": True},
            HTTP_USER_AGENT="TestBrowser/1.0",
            REMOTE_ADDR="10.0.0.1",
        )

        visitor = Visitor.objects.get()
        self.assertTrue(visitor.analytics_consent)
        self.assertEqual(visitor.consent_version, policy_version())
        self.assertEqual(visitor.user_agent, "TestBrowser/1.0")
        log = ConsentLog.objects.get()
        self.assertEqual(log.action, "granted")
        self.assertEqual(log.user_agent, "TestBrowser/1.0")
        self.assertEqual(
            response.cookies[CONSENT_COOKIE].value, f"{policy_version()}:1"
        )
        self.assertEqual(response.cookies[VISITOR_COOKIE].value, str(visitor.id))
        self.assertTrue(response.cookies[VISITOR_COOKIE]["httponly"])

    def test_decline_stores_nothing(self):
        response = self.post_json("tracking:consent", {"analytics": False})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Visitor.objects.exists())
        self.assertFalse(ConsentLog.objects.exists())
        self.assertEqual(
            response.cookies[CONSENT_COOKIE].value, f"{policy_version()}:0"
        )

    def test_withdraw_deletes_collected_data(self):
        visitor = self.accept()
        self.post_json("tracking:collect", {"events": [self.pageview()]})
        self.assertEqual(visitor.events.count(), 1)

        self.post_json("tracking:consent", {"analytics": False})

        visitor.refresh_from_db()
        self.assertFalse(visitor.analytics_consent)
        self.assertEqual(visitor.events.count(), 0)
        self.assertIsNone(visitor.ip_address)
        self.assertEqual(visitor.client_info, {})
        self.assertEqual(
            list(visitor.consent_logs.values_list("action", flat=True)),
            ["withdrawn", "granted"],
        )

    def test_invalid_json(self):
        response = self.client.post(
            reverse("tracking:consent"), data="nope", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_banner_shown_until_choice_is_made(self):
        response = self.client.get(reverse("tracking:privacy"))
        self.assertContains(response, 'id="consent-banner"')
        self.assertContains(response, '"consent": null')

        self.accept()
        response = self.client.get(reverse("tracking:privacy"))
        self.assertContains(response, '"consent": {"analytics": true}')

    def test_old_policy_version_asks_again(self):
        self.client.cookies[CONSENT_COOKIE] = "1999-01-01:1"
        response = self.client.get(reverse("tracking:privacy"))
        self.assertContains(response, '"consent": null')


class CollectTests(TrackingTestCase):
    def test_requires_consent(self):
        response = self.post_json("tracking:collect", {"events": [self.pageview()]})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "consent_required")
        self.assertFalse(VisitEvent.objects.exists())

    def test_consent_cookie_without_visitor_is_reset(self):
        self.client.cookies[CONSENT_COOKIE] = f"{policy_version()}:1"

        response = self.post_json("tracking:collect", {"events": [self.pageview()]})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.cookies[CONSENT_COOKIE].value, "")

    def test_saves_events_and_client_info(self):
        visitor = self.accept()
        user = User.objects.create_user("viewer", password="pass12345")
        self.client.force_login(user)

        response = self.post_json(
            "tracking:collect",
            {
                "events": [
                    self.pageview(),
                    {"type": "click", "page_id": "page-1", "data": {"text": "Лайк"}},
                    {"type": "unknown"},
                    "garbage",
                ],
                "client": {"screen": {"width": 1920}, "timezone": "Europe/Moscow"},
            },
            HTTP_ACCEPT_LANGUAGE="ru-RU,ru;q=0.9",
        )

        self.assertEqual(response.json(), {"status": "ok", "saved": 2})
        visitor.refresh_from_db()
        self.assertEqual(visitor.user, user)
        self.assertEqual(visitor.accept_language, "ru-RU,ru;q=0.9")
        self.assertEqual(visitor.client_info["screen"]["width"], 1920)
        pageview = visitor.events.get(event_type="pageview")
        self.assertEqual(pageview.path, "/quotes/")
        self.assertEqual(pageview.user, user)
        self.assertEqual(pageview.data["utm"]["utm_source"], "vk")

    def test_rejects_too_many_events(self):
        self.accept()
        response = self.post_json(
            "tracking:collect", {"events": [self.pageview()] * 51}
        )
        self.assertEqual(response.status_code, 400)


class MyDataAndForgetTests(TrackingTestCase):
    def test_my_data_without_visitor(self):
        response = self.client.get(reverse("tracking:my_data"))
        self.assertEqual(response.json(), {"consent": None, "visitor": None})

    def test_my_data_returns_everything_stored(self):
        visitor = self.accept()
        self.post_json("tracking:collect", {"events": [self.pageview()]})

        data = self.client.get(reverse("tracking:my_data")).json()

        self.assertEqual(data["visitor"]["id"], str(visitor.id))
        self.assertEqual(data["visitor"]["events_total"], 1)
        self.assertEqual(data["visitor"]["events"][0]["title"], "Цитаты")
        self.assertEqual(len(data["visitor"]["consent_history"]), 1)

    def test_download(self):
        self.accept()
        response = self.client.get(reverse("tracking:my_data") + "?download=1")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_forget_deletes_everything(self):
        self.accept()
        self.post_json("tracking:collect", {"events": [self.pageview()]})

        response = self.post_json("tracking:forget", {})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Visitor.objects.exists())
        self.assertFalse(VisitEvent.objects.exists())
        self.assertFalse(ConsentLog.objects.exists())
        self.assertEqual(
            response.cookies[CONSENT_COOKIE].value, f"{policy_version()}:0"
        )
        self.assertEqual(response.cookies[VISITOR_COOKIE].value, "")


class CleanupCommandTests(TrackingTestCase):
    def test_removes_old_data(self):
        visitor = self.accept()
        self.post_json("tracking:collect", {"events": [self.pageview()]})
        old = timezone.now() - timedelta(days=400)
        VisitEvent.objects.update(created_at=old)

        call_command("cleanup_tracking", stdout=StringIO())
        self.assertFalse(VisitEvent.objects.exists())
        self.assertTrue(Visitor.objects.filter(pk=visitor.pk).exists())

        Visitor.objects.update(last_seen_at=old)
        call_command("cleanup_tracking", stdout=StringIO())
        self.assertFalse(Visitor.objects.exists())


class UtilsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request(self, forwarded_for=None):
        extra = {"REMOTE_ADDR": "172.18.0.5"}
        if forwarded_for:
            extra["HTTP_X_FORWARDED_FOR"] = forwarded_for
        return self.factory.get("/", **extra)

    @override_settings(TRACKING={"PROXY_COUNT": 0, "POLICY_VERSION": "test"})
    def test_ip_without_proxy_ignores_header(self):
        self.assertEqual(get_client_ip(self.request("1.1.1.1")), "172.18.0.5")

    @override_settings(TRACKING={"PROXY_COUNT": 1, "POLICY_VERSION": "test"})
    def test_ip_takes_address_added_by_proxy(self):
        # Первый адрес подставлен клиентом, ему не доверяем
        request = self.request("6.6.6.6, 203.0.113.7")
        self.assertEqual(get_client_ip(request), "203.0.113.7")

    @override_settings(TRACKING={"PROXY_COUNT": 2, "POLICY_VERSION": "test"})
    def test_ip_behind_two_proxies(self):
        request = self.request("6.6.6.6, 203.0.113.7, 10.0.0.2")
        self.assertEqual(get_client_ip(request), "203.0.113.7")

    @override_settings(TRACKING={"PROXY_COUNT": 1, "POLICY_VERSION": "test"})
    def test_invalid_ip(self):
        self.assertIsNone(get_client_ip(self.request("not-an-ip")))

    def test_clean_client_data_limits_input(self):
        cleaned = clean_client_data(
            {
                "long": "x" * 1000,
                "nan": float("nan"),
                "list": list(range(100)),
                "deep": {"a": {"b": {"c": {"d": {"e": 1}}}}},
                "object": object(),
            }
        )
        self.assertEqual(len(cleaned["long"]), 500)
        self.assertIsNone(cleaned["nan"])
        self.assertEqual(len(cleaned["list"]), 50)
        self.assertEqual(cleaned["deep"], {"a": {"b": {"c": None}}})
        self.assertIsNone(cleaned["object"])
