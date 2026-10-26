from django.urls import path

from . import views

app_name = "tracking"

urlpatterns = [
    path("privacy/", views.privacy, name="privacy"),
    path("api/tracking/consent/", views.consent, name="consent"),
    path("api/tracking/collect/", views.collect, name="collect"),
    path("api/tracking/my-data/", views.my_data, name="my_data"),
    path("api/tracking/forget/", views.forget, name="forget"),
]
