from django.urls import path

from . import views

app_name = "seo"

urlpatterns = [
    # Основные SEO файлы
    path("robots.txt", views.RobotsTxtView.as_view(), name="robots_txt"),
    path("sitemap.xml", views.SitemapView.as_view(), name="sitemap_xml"),
    path(
        "structured-data.json",
        views.StructuredDataView.as_view(),
        name="structured_data",
    ),
    # API для получения SEO мета-тегов
    path(
        "api/meta-tags/<int:content_type_id>/<int:object_id>/",
        views.seo_meta_tags,
        name="meta_tags",
    ),
    # Административная панель SEO
    path("admin/", views.SEOAdminView.as_view(), name="admin"),
    # Аналитика
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
]
