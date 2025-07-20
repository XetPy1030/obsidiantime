from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms

from .models import Comment, Meme


class MemeUploadForm(forms.ModelForm):
    class Meta:
        model = Meme
        fields = ["title", "description", "image"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Название мема...", "class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Описание мема (опционально)...",
                    "class": "form-control",
                }
            ),
            "image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_enctype = "multipart/form-data"
        self.helper.layout = Layout(
            Field("title"),
            Field("description"),
            Field("image"),
            Submit("submit", "Загрузить мем", css_class="btn btn-primary"),
        )

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            # Проверяем размер файла (максимум 10MB)
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Размер файла не должен превышать 10MB")

            # Проверяем тип файла
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if image.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Поддерживаемые форматы: JPEG, PNG, GIF, WebP"
                )

        return image


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Оставьте комментарий...",
                    "class": "form-control",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("content"),
            Submit(
                "submit", "Отправить комментарий", css_class="btn btn-sm btn-primary"
            ),
        )


class MemeFilterForm(forms.Form):
    SORT_CHOICES = [
        ("-created_at", "По дате (новые)"),
        ("created_at", "По дате (старые)"),
        ("-views", "По популярности"),
        ("title", "По названию"),
    ]

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Поиск мемов...", "class": "form-control"}
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
            attrs={"placeholder": "Автор...", "class": "form-control"}
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
