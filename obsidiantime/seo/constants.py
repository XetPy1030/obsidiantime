"""
Константы для SEO модуля
"""

# Статические URL для sitemap
SITEMAP_STATIC_URLS = [
    {"url": "/", "priority": 1.0, "changefreq": "daily"},
    {"url": "/gallery/", "priority": 0.8, "changefreq": "weekly"},
    {"url": "/quotes/", "priority": 0.8, "changefreq": "weekly"},
    {"url": "/chat/", "priority": 0.6, "changefreq": "daily"},
    {"url": "/about/", "priority": 0.5, "changefreq": "monthly"},
]

# Стандартные правила robots.txt
ROBOTS_DEFAULT_RULES = [
    {"user_agent": "*", "rule_type": "disallow", "path": "/admin/", "order": 1},
    {"user_agent": "*", "rule_type": "disallow", "path": "/auth/", "order": 2},
    {"user_agent": "*", "rule_type": "disallow", "path": "/api/", "order": 3},
    {"user_agent": "*", "rule_type": "disallow", "path": "/private/", "order": 4},
    {"user_agent": "*", "rule_type": "disallow", "path": "/temp/", "order": 5},
    {"user_agent": "*", "rule_type": "disallow", "path": "/cache/", "order": 6},
    {"user_agent": "*", "rule_type": "disallow", "path": "/logs/", "order": 7},
    {"user_agent": "*", "rule_type": "allow", "path": "/", "order": 8},
    {"user_agent": "*", "rule_type": "allow", "path": "/gallery/", "order": 9},
    {"user_agent": "*", "rule_type": "allow", "path": "/quotes/", "order": 10},
    {"user_agent": "*", "rule_type": "allow", "path": "/chat/", "order": 11},
    {"user_agent": "*", "rule_type": "allow", "path": "/about/", "order": 12},
    {"user_agent": "*", "rule_type": "allow", "path": "/static/", "order": 13},
    {"user_agent": "*", "rule_type": "allow", "path": "/media/", "order": 14},
]

# Настройки по умолчанию для аналитики
ANALYTICS_DEFAULT_SETTINGS = {
    "is_active": True,
    "google_analytics_id": "",
    "yandex_metrika_id": "",
    "google_search_console": "",
    "yandex_webmaster": "",
    "facebook_pixel": "",
    "vk_pixel": "",
}

# Частота изменения контента
CHANGEFREQ_CHOICES = [
    ("always", "Always"),
    ("hourly", "Hourly"),
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("yearly", "Yearly"),
    ("never", "Never"),
]

# Типы правил robots.txt
ROBOTS_RULE_TYPES = [
    ("allow", "Allow"),
    ("disallow", "Disallow"),
]

# User Agent для robots.txt
ROBOTS_USER_AGENTS = [
    ("*", "Все роботы"),
    ("Googlebot", "Google"),
    ("Yandex", "Яндекс"),
    ("Bingbot", "Bing"),
    ("Slurp", "Yahoo"),
    ("DuckDuckBot", "DuckDuckGo"),
]

# Карты для отображения
CHANGEFREQ_DISPLAY_MAP = {
    "always": "Всегда",
    "hourly": "Ежечасно",
    "daily": "Ежедневно",
    "weekly": "Еженедельно",
    "monthly": "Ежемесячно",
    "yearly": "Ежегодно",
    "never": "Никогда",
}

USER_AGENT_DISPLAY_MAP = {
    "*": "Все роботы",
    "Googlebot": "Google",
    "Yandex": "Яндекс",
    "Bingbot": "Bing",
    "Slurp": "Yahoo",
    "DuckDuckBot": "DuckDuckGo",
}

# Кеширование
SEO_CACHE_TIMEOUT = 86400  # 24 часа в секундах

# Лимиты для админки
ADMIN_LIST_LIMIT = 10
SITEMAP_DYNAMIC_LIMIT = 100  # Максимум динамических URL в sitemap
