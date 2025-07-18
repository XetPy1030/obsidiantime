from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Message, Poll, PollOption


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Введите ваше сообщение...",
                    "class": "form-control",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("content"), Submit("submit", "Отправить", css_class="btn btn-primary")
        )


class PollForm(forms.ModelForm):
    option1 = forms.CharField(max_length=200, label="Вариант 1")
    option2 = forms.CharField(max_length=200, label="Вариант 2")
    option3 = forms.CharField(
        max_length=200, required=False, label="Вариант 3 (опционально)"
    )
    option4 = forms.CharField(
        max_length=200, required=False, label="Вариант 4 (опционально)"
    )

    class Meta:
        model = Poll
        fields = ["question", "multiple_choice"]
        widgets = {
            "question": forms.TextInput(
                attrs={
                    "placeholder": "Введите вопрос для голосования...",
                    "class": "form-control",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("question"),
            Field("multiple_choice"),
            Div(
                Field("option1"),
                Field("option2"),
                Field("option3"),
                Field("option4"),
                css_class="poll-options",
            ),
            Submit("submit", "Создать голосование", css_class="btn btn-success"),
        )

    def save(self, user):
        poll = super().save(commit=False)

        # Создаем сообщение для голосования
        message = Message.objects.create(
            author=user, content=f"Голосование: {poll.question}", message_type="poll"
        )
        poll.message = message
        poll.save()

        # Создаем варианты ответов
        options_data = [
            self.cleaned_data["option1"],
            self.cleaned_data["option2"],
            self.cleaned_data.get("option3"),
            self.cleaned_data.get("option4"),
        ]

        for option_text in options_data:
            if option_text and option_text.strip():
                PollOption.objects.create(poll=poll, text=option_text.strip())

        return poll


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("username"),
            Field("email"),
            Field("first_name"),
            Field("last_name"),
            Field("password1"),
            Field("password2"),
            Submit("submit", "Зарегистрироваться", css_class="btn btn-primary"),
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user
