from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from obsidiantime.gallery.models import Meme
from obsidiantime.main.models import Quote
from obsidiantime.seo.constants import (
    ANALYTICS_DEFAULT_SETTINGS,
    ROBOTS_DEFAULT_RULES,
    SITEMAP_DYNAMIC_LIMIT,
)
from obsidiantime.seo.models import Analytics, RobotsRule, SitemapURL
from obsidiantime.seo.services import SitemapService


class Command(BaseCommand):
    help = "Настройка SEO для ObsidianTime"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Настройка SEO..."))

        # Настройка сайта
        self.setup_site()

        # Настройка robots.txt
        self.setup_robots()

        # Настройка sitemap
        self.setup_sitemap()

        # Настройка аналитики
        self.setup_analytics()

        self.stdout.write(self.style.SUCCESS("SEO настройка завершена!"))

    def setup_site(self):
        """Настройка сайта"""
        site, created = Site.objects.get_or_create(
            id=1, defaults={"domain": "obsidiantime.ru", "name": "ObsidianTime"}
        )
        if created:
            self.stdout.write(f"Создан сайт: {site.domain}")
        else:
            self.stdout.write(f"Сайт уже существует: {site.domain}")

    def setup_robots(self):
        """Настройка robots.txt"""
        # Удаляем старые правила
        RobotsRule.objects.all().delete()

        # Создаем новые правила
        rules = ROBOTS_DEFAULT_RULES

        for rule_data in rules:
            rule, created = RobotsRule.objects.get_or_create(
                user_agent=rule_data["user_agent"],
                rule_type=rule_data["rule_type"],
                path=rule_data["path"],
                defaults={"order": rule_data["order"], "is_active": True},
            )
            if created:
                self.stdout.write(f"Создано правило robots: {rule}")

        self.stdout.write(f"Создано {len(rules)} правил robots.txt")

    def setup_sitemap(self):
        """Настройка sitemap"""
        # Удаляем старые URL
        SitemapURL.objects.all().delete()

        # Создаем статические URL
        static_urls = SitemapService.get_static_urls()

        for url_data in static_urls:
            url, created = SitemapURL.objects.get_or_create(
                url=url_data["url"],
                defaults={
                    "priority": url_data["priority"],
                    "changefreq": url_data["changefreq"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"Добавлен URL в sitemap: {url.url}")

        # Добавляем динамические URL для мемов
        ContentType.objects.get_for_model(Meme)
        memes = Meme.objects.filter(is_approved=True)[
            :SITEMAP_DYNAMIC_LIMIT
        ]  # Ограничиваем лимитом
        for meme in memes:
            url, created = SitemapURL.objects.get_or_create(
                url=f"/gallery/meme/{meme.id}/",
                defaults={"priority": 0.7, "changefreq": "weekly", "is_active": True},
            )
            if created:
                self.stdout.write(f"Добавлен мем в sitemap: {meme.title}")

        # Добавляем динамические URL для цитат
        ContentType.objects.get_for_model(Quote)
        quotes = Quote.objects.all()[:SITEMAP_DYNAMIC_LIMIT]  # Ограничиваем лимитом
        for quote in quotes:
            url, created = SitemapURL.objects.get_or_create(
                url=f"/quotes/{quote.id}/",
                defaults={"priority": 0.7, "changefreq": "weekly", "is_active": True},
            )
            if created:
                self.stdout.write(f"Добавлена цитата в sitemap: {quote.text[:50]}...")

        self.stdout.write(f"Создано {SitemapURL.objects.count()} URL в sitemap")

    def setup_analytics(self):
        """Настройка аналитики"""
        analytics, created = Analytics.objects.get_or_create(
            pk=1, defaults=ANALYTICS_DEFAULT_SETTINGS
        )
        if created:
            self.stdout.write("Созданы настройки аналитики")
        else:
            self.stdout.write("Настройки аналитики уже существуют")
