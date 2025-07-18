from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("quotes/", views.quotes_list, name="quotes_list"),
    path("quotes/add/", views.add_quote, name="add_quote"),
    path("quotes/<int:pk>/", views.quote_detail, name="quote_detail"),
    path("quotes/<int:pk>/like/", views.toggle_quote_like, name="toggle_quote_like"),
    path("register/", views.register, name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("about/", views.about, name="about"),
]
