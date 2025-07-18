from django.urls import path

from . import views

app_name = "gallery"

urlpatterns = [
    path("", views.gallery_list, name="gallery_list"),
    path("upload/", views.upload_meme, name="upload_meme"),
    path("meme/<int:pk>/", views.meme_detail, name="meme_detail"),
    path("meme/<int:pk>/like/", views.toggle_like, name="toggle_like"),
    path("meme/<int:pk>/dislike/", views.toggle_dislike, name="toggle_dislike"),
    path("meme/<int:pk>/comment/", views.add_comment, name="add_comment"),
    path("top/", views.top_memes, name="top_memes"),
    path("my/", views.my_memes, name="my_memes"),
    path("random/", views.random_meme, name="random_meme"),
]
