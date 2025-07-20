from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms

from .models import Quote

# Constants
MIN_QUOTE_LENGTH = 10


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
