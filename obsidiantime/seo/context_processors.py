from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from .models import Analytics, SEOGenericModel
from .utils import get_seo_settings, get_structured_data


def seo_context(request):
    """Контекстный процессор для SEO мета-тегов"""
    context = {}

    # Получаем настройки сайта
    site = Site.objects.get_current()

    # Базовые SEO настройки
    context.update(get_seo_settings())

    # Настройки аналитики
    try:
        analytics = Analytics.get_settings()
        context["analytics"] = analytics
    except Analytics.DoesNotExist:
        context["analytics"] = None

    # Canonical URL
    if request.path:
        context["canonical_url"] = f"https://{site.domain}{request.path}"

    # Структурированные данные
    context["structured_data"] = get_structured_data(request)

    return context


def seo_meta_tags(request, obj=None):
    """Получает SEO мета-теги для объекта"""
    if not obj:
        return {}

    try:
        content_type = ContentType.objects.get_for_model(obj)
        seo_obj = SEOGenericModel.objects.get(
            content_type=content_type, object_id=obj.pk
        )

        return {
            "meta_title": seo_obj.get_meta_title(),
            "meta_description": seo_obj.get_meta_description(),
            "meta_keywords": seo_obj.meta_keywords,
            "canonical_url": seo_obj.canonical_url,
            "og_title": seo_obj.get_og_title(),
            "og_description": seo_obj.get_og_description(),
            "og_image": seo_obj.og_image.url if seo_obj.og_image else None,
            "og_type": seo_obj.og_type,
            "twitter_card": seo_obj.twitter_card,
            "twitter_title": seo_obj.get_twitter_title(),
            "twitter_description": seo_obj.get_twitter_description(),
            "twitter_image": seo_obj.twitter_image.url
            if seo_obj.twitter_image
            else None,
            "schema_markup": seo_obj.schema_markup,
            "robots_index": seo_obj.robots_index,
            "robots_follow": seo_obj.robots_follow,
        }
    except SEOGenericModel.DoesNotExist:
        return {}
