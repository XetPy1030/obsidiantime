from django.conf import settings
from django.contrib.sites.models import Site


def get_structured_data(request=None):
    """Генерирует структурированные данные для текущей страницы"""
    site = Site.objects.get_current()

    # Базовые данные сайта
    structured_data = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "ObsidianTime",
            "url": f"https://{site.domain}",
            "description": "Место для мемов, общения и веселья!",
            "inLanguage": "ru-RU",
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"https://{site.domain}/search?q={{search_term_string}}",
                "query-input": "required name=search_term_string",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "ObsidianTime",
            "url": f"https://{site.domain}",
            "logo": f"https://{site.domain}/static/images/obsidian-logo.svg",
            "description": "Место для мемов, общения и веселья!",
            "sameAs": [
                "https://vk.com/obsidiantime",
                "https://t.me/obsidiantime",
            ],
        },
    ]

    # Добавляем данные для конкретных страниц только если передан request
    if request:
        if request.path == "/":
            structured_data.append(
                {
                    "@context": "https://schema.org",
                    "@type": "WebPage",
                    "name": "Главная страница - ObsidianTime",
                    "description": "Место для мемов, общения и веселья!",
                    "url": f"https://{site.domain}",
                    "mainEntity": {
                        "@type": "VideoObject",
                        "name": "ObsidianTime - Главная страница",
                        "description": "Добро пожаловать на ObsidianTime!",
                    },
                }
            )
        elif request.path.startswith("/gallery/"):
            structured_data.append(
                {
                    "@context": "https://schema.org",
                    "@type": "ImageGallery",
                    "name": "Галерея мемов - ObsidianTime",
                    "description": "Коллекция лучших мемов",
                    "url": f"https://{site.domain}/gallery/",
                }
            )
        elif request.path.startswith("/quotes/"):
            structured_data.append(
                {
                    "@context": "https://schema.org",
                    "@type": "CreativeWork",
                    "name": "Коллекция цитат - ObsidianTime",
                    "description": "Лучшие цитаты и афоризмы",
                    "url": f"https://{site.domain}/quotes/",
                }
            )

    return structured_data


def get_seo_settings():
    """Возвращает настройки SEO из settings"""
    return {
        "seo_settings": getattr(settings, "SEO_SETTINGS", {}),
        "og_settings": getattr(settings, "OPENGRAPH_SETTINGS", {}),
        "twitter_settings": getattr(settings, "TWITTER_CARD_SETTINGS", {}),
        "schema_settings": getattr(settings, "SCHEMA_SETTINGS", {}),
        "analytics_settings": getattr(settings, "ANALYTICS_SETTINGS", {}),
        "social_settings": getattr(settings, "SOCIAL_MEDIA_SETTINGS", {}),
        "default_meta": getattr(settings, "DEFAULT_META_TAGS", {}),
    }
