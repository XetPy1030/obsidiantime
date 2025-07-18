from django.contrib import admin
from django.utils.html import format_html

from .models import Comment, Dislike, Like, Meme

# Constants
CONTENT_PREVIEW_LENGTH = 100


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "image_preview",
        "likes_count",
        "dislikes_count",
        "get_rating",
        "views",
        "is_approved",
        "created_at",
    ]
    list_filter = ["is_approved", "created_at", "author"]
    search_fields = ["title", "description", "author__username"]
    readonly_fields = ["created_at", "updated_at", "views", "image_preview"]
    list_editable = ["is_approved"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url,
            )
        return "Нет изображения"

    image_preview.short_description = "Превью"

    def likes_count(self, obj):
        return obj.likes_count

    likes_count.short_description = "Лайки"

    def dislikes_count(self, obj):
        return obj.dislikes_count

    dislikes_count.short_description = "Дизлайки"


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ["user", "meme", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "meme__title"]
    readonly_fields = ["created_at"]


@admin.register(Dislike)
class DislikeAdmin(admin.ModelAdmin):
    list_display = ["user", "meme", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "meme__title"]
    readonly_fields = ["created_at"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "meme", "content_preview", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["author__username", "meme__title", "content"]
    readonly_fields = ["created_at"]

    def content_preview(self, obj):
        return (
            obj.content[:CONTENT_PREVIEW_LENGTH] + "..."
            if len(obj.content) > CONTENT_PREVIEW_LENGTH
            else obj.content
        )

    content_preview.short_description = "Комментарий"
