import json

from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .constants import ADMIN_LIST_LIMIT, SEO_CACHE_TIMEOUT
from .decorators import seo_admin_required, seo_analytics_required
from .models import SEOGenericModel
from .services import SEOService, SitemapService
from .utils import get_structured_data


class BaseSEOView(TemplateView):
    """Базовый класс для SEO представлений"""

    def get_site(self):
        """Получает текущий сайт"""
        return SEOService.get_site()

    def get_cache_timeout(self):
        """Возвращает время кеширования в секундах"""
        return SEO_CACHE_TIMEOUT


class RobotsTxtView(BaseSEOView):
    """Представление для robots.txt"""

    template_name = "seo/robots.txt"
    content_type = "text/plain"

    @method_decorator(cache_page(SEO_CACHE_TIMEOUT))  # Кешируем на 24 часа
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        response = self.render_to_response(context)
        response["Content-Type"] = "text/plain; charset=utf-8"
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = self.get_site()
        context["site"] = site
        context["sitemap_url"] = f"https://{site.domain}/sitemap.xml"
        context["robots_rules"] = SEOService.get_active_robots_rules()
        return context


class SitemapView(BaseSEOView):
    """Представление для sitemap.xml"""

    template_name = "seo/sitemap.xml"
    content_type = "application/xml"

    @method_decorator(cache_page(SEO_CACHE_TIMEOUT))  # Кешируем на 24 часа
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        response = self.render_to_response(context)
        response["Content-Type"] = "application/xml; charset=utf-8"
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = self.get_site()
        context["urls"] = self.get_sitemap_urls()
        context["lastmod"] = timezone.now()
        return context

    def get_sitemap_urls(self):
        """Получает все URL для sitemap"""
        return SitemapService.generate_sitemap_urls()


class StructuredDataView(BaseSEOView):
    """Представление для структурированных данных"""

    template_name = "seo/structured_data.json"
    content_type = "application/ld+json"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structured_data"] = self.get_structured_data()
        return context

    def get_structured_data(self):
        """Возвращает структурированные данные в формате JSON-LD"""
        return get_structured_data()  # Без request для базовых данных


class AnalyticsView(BaseSEOView):
    """Представление для кодов аналитики"""

    template_name = "seo/analytics.html"

    @method_decorator(seo_analytics_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["analytics"] = SEOService.get_analytics()
        return context


@require_http_methods(["GET"])
def seo_meta_tags(request, content_type_id, object_id):
    """API для получения SEO мета-тегов для объекта"""
    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
        seo_obj = SEOGenericModel.objects.get(
            content_type=content_type, object_id=object_id
        )

        meta_data = get_seo_meta_data(seo_obj)

        return HttpResponse(
            json.dumps(meta_data, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
        )

    except (ContentType.DoesNotExist, SEOGenericModel.DoesNotExist) as err:
        raise Http404("SEO metadata not found") from err


def get_seo_meta_data(seo_obj):
    """Извлекает SEO мета-данные из объекта"""
    return {
        "title": seo_obj.get_meta_title(),
        "description": seo_obj.get_meta_description(),
        "keywords": seo_obj.meta_keywords,
        "canonical": seo_obj.canonical_url,
        "og_title": seo_obj.get_og_title(),
        "og_description": seo_obj.get_og_description(),
        "og_image": seo_obj.og_image.url if seo_obj.og_image else None,
        "og_type": seo_obj.og_type,
        "twitter_card": seo_obj.twitter_card,
        "twitter_title": seo_obj.get_twitter_title(),
        "twitter_description": seo_obj.get_twitter_description(),
        "twitter_image": seo_obj.twitter_image.url if seo_obj.twitter_image else None,
        "schema_markup": seo_obj.schema_markup,
        "robots_index": seo_obj.robots_index,
        "robots_follow": seo_obj.robots_follow,
    }


class SEOAdminView(BaseSEOView):
    """Административная панель для SEO"""

    template_name = "seo/admin.html"

    @method_decorator(seo_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sitemap_urls"] = SEOService.get_sitemap_urls()[:ADMIN_LIST_LIMIT]
        context["robots_rules"] = SEOService.get_active_robots_rules()[
            :ADMIN_LIST_LIMIT
        ]
        context["analytics"] = SEOService.get_analytics()
        return context
