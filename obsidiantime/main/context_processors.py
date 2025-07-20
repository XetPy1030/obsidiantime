from .models import SocialLink


def social_links(request):
    """
    Context processor для добавления социальных ссылок во все шаблоны
    """
    return {"social_links": SocialLink.objects.filter(is_active=True)}
