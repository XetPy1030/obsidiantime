from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.utils import timezone

from .constants import (
    SITEMAP_STATIC_URLS,
)
from .models import Analytics, RobotsRule, SEOGenericModel, SitemapURL


class SEOService:
    """Сервис для работы с SEO"""

    @staticmethod
    def get_site():
        """Получает текущий сайт"""
        return Site.objects.get_current()

    @staticmethod
    def get_analytics():
        """Получает настройки аналитики"""
        return Analytics.get_settings()

    @staticmethod
    def get_active_robots_rules():
        """Получает активные правила robots.txt"""
        return RobotsRule.objects.filter(is_active=True).order_by("order")

    @staticmethod
    def get_sitemap_urls():
        """Получает все URL для sitemap"""
        return SitemapURL.objects.filter(is_active=True).order_by("-priority")

    @staticmethod
    def create_seo_for_object(obj, **kwargs):
        """Создает SEO метаданные для объекта"""
        content_type = ContentType.objects.get_for_model(obj)
        seo_obj, created = SEOGenericModel.objects.get_or_create(
            content_type=content_type, object_id=obj.pk, defaults=kwargs
        )
        return seo_obj

    @staticmethod
    def get_seo_for_object(obj):
        """Получает SEO метаданные для объекта"""
        try:
            content_type = ContentType.objects.get_for_model(obj)
            return SEOGenericModel.objects.get(
                content_type=content_type, object_id=obj.pk
            )
        except SEOGenericModel.DoesNotExist:
            return None


class SitemapService:
    """Сервис для работы с sitemap"""

    @staticmethod
    def get_static_urls():
        """Возвращает статические URL для sitemap"""
        return SITEMAP_STATIC_URLS

    @staticmethod
    def generate_sitemap_urls():
        """Генерирует все URL для sitemap"""
        urls = []
        site = Site.objects.get_current()

        # Добавляем статические URL
        static_urls = SitemapService.get_static_urls()
        for url_data in static_urls:
            urls.append(
                {
                    "loc": f"https://{site.domain}{url_data['url']}",
                    "priority": url_data["priority"],
                    "changefreq": url_data["changefreq"],
                    "lastmod": timezone.now(),
                }
            )

        # Добавляем динамические URL
        sitemap_urls = SitemapURL.objects.filter(is_active=True)
        for sitemap_url in sitemap_urls:
            urls.append(
                {
                    "loc": f"https://{site.domain}{sitemap_url.url}",
                    "priority": sitemap_url.priority,
                    "changefreq": sitemap_url.changefreq,
                    "lastmod": sitemap_url.lastmod,
                }
            )

        return urls


class RobotsService:
    """Сервис для работы с robots.txt"""

    @staticmethod
    def get_robots_content():
        """Генерирует содержимое robots.txt"""
        site = Site.objects.get_current()
        rules = RobotsRule.objects.filter(is_active=True).order_by("order")

        content = f"User-agent: {site.domain}\n"

        for rule in rules:
            if rule.is_global_rule():
                content += f"{rule.get_rule_text()}\n"
            else:
                content += f"User-agent: {rule.user_agent}\n{rule.get_rule_text()}\n"

        # Добавляем стандартные правила
        content += "\n# Разрешаем индексацию основных разделов\n"
        content += (
            "Allow: /\nAllow: /gallery/\nAllow: /quotes/\n"
            "Allow: /chat/\nAllow: /about/\n"
        )
        content += "Allow: /static/\nAllow: /media/\n\n"

        content += "# Запрещаем индексацию служебных разделов\n"
        content += "Disallow: /admin/\nDisallow: /auth/\nDisallow: /api/\n"
        content += (
            "Disallow: /private/\nDisallow: /temp/\n"
            "Disallow: /cache/\nDisallow: /logs/\n\n"
        )

        content += "# Настройки для поисковых роботов\n"
        content += "Crawl-delay: 1\n\n"

        content += f"# Sitemap\nSitemap: https://{site.domain}/sitemap.xml\n\n"

        # Дополнительные настройки для разных роботов
        content += "# Googlebot\nUser-agent: Googlebot\nCrawl-delay: 1\n\n"
        content += "# Yandex\nUser-agent: Yandex\nCrawl-delay: 1\n\n"
        content += "# Bingbot\nUser-agent: Bingbot\nCrawl-delay: 1\n"

        return content


class AnalyticsService:
    """Сервис для работы с аналитикой"""

    @staticmethod
    def get_analytics_scripts():
        """Возвращает скрипты аналитики для вставки в HTML"""
        analytics = Analytics.get_settings()
        scripts = {}

        if analytics.has_google_analytics():
            scripts["google_analytics"] = {
                "id": analytics.google_analytics_id,
                "script": f"""
                <script async src="https://www.googletagmanager.com/gtag/js?id={analytics.google_analytics_id}"></script>
                <script>
                    window.dataLayer = window.dataLayer || [];
                    function gtag(){{dataLayer.push(arguments);}}
                    gtag('js', new Date());
                    gtag('config', '{analytics.google_analytics_id}');
                </script>
                """,
            }

        if analytics.has_yandex_metrika():
            scripts["yandex_metrika"] = {
                "id": analytics.yandex_metrika_id,
                "script": f"""
                <script type="text/javascript">
                    (function(m,e,t,r,i,k,a){{
                        m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
                        m[i].l=1*new Date();
                        for (var j = 0; j < document.scripts.length; j++) {{
                            if (document.scripts[j].src === r) return;
                        }}
                        k=e.createElement(t),a=e.getElementsByTagName(t)[0],
                        k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
                    }})
                    (window, document, "script", 
                     "https://mc.yandex.ru/metrika/tag.js", "ym");
                    ym({analytics.yandex_metrika_id}, "init", {{
                        clickmap:true,
                        trackLinks:true,
                        accurateTrackBounce:true
                    }});
                </script>
                <noscript><div><img src="https://mc.yandex.ru/watch/{analytics.yandex_metrika_id}" 
                    style="position:absolute; left:-9999px;" alt="" /></div></noscript>
                """,
            }

        return scripts
