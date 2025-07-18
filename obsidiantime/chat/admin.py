from django.contrib import admin

from .models import Message, Poll, PollOption, PollVote

# Constants
CONTENT_PREVIEW_LENGTH = 100


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2
    min_num = 2


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["author", "content_preview", "message_type", "created_at"]
    list_filter = ["message_type", "created_at", "author"]
    search_fields = ["content", "author__username"]
    readonly_fields = ["created_at", "updated_at"]

    def content_preview(self, obj):
        return (
            obj.content[:CONTENT_PREVIEW_LENGTH] + "..."
            if len(obj.content) > CONTENT_PREVIEW_LENGTH
            else obj.content
        )

    content_preview.short_description = "Содержимое"


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ["question", "is_active", "total_votes", "created_at"]
    list_filter = ["is_active", "multiple_choice", "created_at"]
    search_fields = ["question"]
    readonly_fields = ["created_at", "total_votes"]
    inlines = [PollOptionInline]

    def total_votes(self, obj):
        return obj.total_votes

    total_votes.short_description = "Всего голосов"


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ["text", "poll", "vote_count", "vote_percentage"]
    list_filter = ["poll__is_active", "created_at"]
    search_fields = ["text", "poll__question"]
    readonly_fields = ["created_at", "vote_count", "vote_percentage"]

    def vote_count(self, obj):
        return obj.vote_count

    vote_count.short_description = "Голосов"

    def vote_percentage(self, obj):
        return f"{obj.vote_percentage}%"

    vote_percentage.short_description = "Процент"


@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ["user", "option", "poll_question", "created_at"]
    list_filter = ["created_at", "option__poll"]
    search_fields = ["user__username", "option__text", "option__poll__question"]
    readonly_fields = ["created_at"]

    def poll_question(self, obj):
        return obj.option.poll.question

    poll_question.short_description = "Вопрос"
