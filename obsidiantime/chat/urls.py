from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_view, name="chat"),
    path("send/", views.send_message, name="send_message"),
    path("poll/create/", views.create_poll, name="create_poll"),
    path("poll/<int:poll_id>/", views.poll_detail, name="poll_detail"),
    path("poll/<int:poll_id>/vote/<int:option_id>/", views.vote_poll, name="vote_poll"),
    path("poll/<int:poll_id>/close/", views.close_poll, name="close_poll"),
    path("api/messages/", views.chat_api_messages, name="api_messages"),
]
