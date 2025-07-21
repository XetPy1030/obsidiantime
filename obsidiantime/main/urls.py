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
    path("feedback/", views.feedback, name="feedback"),
    path("my-feedback/", views.my_feedback, name="my_feedback"),
    path("feedback/<int:pk>/", views.feedback_detail, name="feedback_detail"),
    path("management/feedback/", views.admin_feedback_list, name="admin_feedback_list"),
    path(
        "management/feedback/<int:pk>/",
        views.admin_feedback_detail,
        name="admin_feedback_detail",
    ),
    path(
        "management/feedback/<int:pk>/change-status/",
        views.change_feedback_status,
        name="change_feedback_status",
    ),
    path("api/errors/", views.api_errors, name="api_errors"),
]
