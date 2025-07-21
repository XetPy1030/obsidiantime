from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms

from .models import Feedback, FeedbackComment, Quote

# Constants
MIN_QUOTE_LENGTH = 10
MIN_MESSAGE_LENGTH = 10
MIN_COMMENT_LENGTH = 5


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["text", "author"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Введите текст цитаты...",
                    "class": "form-control",
                }
            ),
            "author": forms.TextInput(
                attrs={"placeholder": "Автор цитаты...", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("text"),
            Field("author"),
            Submit("submit", "Добавить цитату", css_class="btn btn-primary"),
        )

    def clean_text(self):
        text = self.cleaned_data.get("text")
        if text and len(text) < MIN_QUOTE_LENGTH:
            raise forms.ValidationError(
                f"Цитата должна содержать минимум {MIN_QUOTE_LENGTH} символов"
            )
        return text


class QuoteFilterForm(forms.Form):
    SORT_CHOICES = [
        ("-created_at", "По дате (новые)"),
        ("created_at", "По дате (старые)"),
        ("-views", "По популярности"),
        ("author", "По автору"),
    ]

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Поиск по тексту или автору...",
                "class": "form-control",
            }
        ),
    )

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial="-created_at",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    author = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Автор цитаты...", "class": "form-control"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "get"

        # Скрываем стандартные английские подписи
        for field_name in self.fields:
            self.fields[field_name].label = ""

        # Обновлённый макет с более широким полем поиска и заметной кнопкой
        self.helper.layout = Layout(
            Div(
                Field("search", wrapper_class="col-md-5"),
                Field("sort", wrapper_class="col-md-3"),
                Field("author", wrapper_class="col-md-2"),
                Submit("submit", "Фильтровать", css_class="btn btn-primary col-md-2"),
                css_class="row g-2",
            )
        )


class FeedbackForm(forms.ModelForm):
    """Форма для обратной связи"""

    class Meta:
        model = Feedback
        fields = ["name", "email", "feedback_type", "subject", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Ваше имя...",
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "your@email.com",
                    "class": "form-control",
                }
            ),
            "feedback_type": forms.Select(attrs={"class": "form-control"}),
            "subject": forms.TextInput(
                attrs={
                    "placeholder": "Краткая тема обращения...",
                    "class": "form-control",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Опишите ваше обращение подробно...",
                    "class": "form-control",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("name"),
            Field("email"),
            Field("feedback_type"),
            Field("subject"),
            Field("message"),
            Submit("submit", "Отправить обращение", css_class="btn btn-primary"),
        )

    def clean_message(self):
        message = self.cleaned_data.get("message")
        if message and len(message) < MIN_MESSAGE_LENGTH:
            raise forms.ValidationError(
                f"Сообщение должно содержать минимум {MIN_MESSAGE_LENGTH} символов"
            )
        return message


class FeedbackCommentForm(forms.ModelForm):
    """Форма для комментариев"""

    class Meta:
        model = FeedbackComment
        fields = ["comment", "is_internal"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Введите ваш комментарий...",
                    "class": "form-control",
                }
            ),
            "is_internal": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"

        # Скрываем поле внутренних комментариев для обычных пользователей
        if not self.user or not self.user.is_staff:
            self.fields.pop("is_internal")
            self.helper.layout = Layout(
                Field("comment"),
                Submit("submit", "Добавить комментарий", css_class="btn btn-primary"),
            )
        else:
            self.helper.layout = Layout(
                Field("comment"),
                Div(Field("is_internal"), css_class="form-check mb-3"),
                Submit("submit", "Добавить комментарий", css_class="btn btn-primary"),
            )

    def clean_comment(self):
        comment = self.cleaned_data.get("comment")
        if comment and len(comment.strip()) < MIN_COMMENT_LENGTH:
            raise forms.ValidationError(
                f"Комментарий должен содержать минимум {MIN_COMMENT_LENGTH} символов"
            )
        return comment
