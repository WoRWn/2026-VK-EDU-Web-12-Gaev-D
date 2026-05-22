from django import forms
from django.db import transaction
import re
from random import randint

from .models import Question, Answer, Tag


def generate_random_hex_color():
    return f"#{randint(0, 0xFFFFFF):06X}"


class QuestionForm(forms.ModelForm):
    tags_input = forms.CharField(
        label="Теги",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'questionTags',
            'placeholder': 'Например: witcher-3, loot, story',
            'maxlength': '100'
        })
    )
    
    class Meta:
        model = Question
        fields = ["title", "text"]
        widgets = {
           'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'questionTitle',
                'placeholder': 'Например: Как победить Малению в Elden Ring?',
                'maxlength': '150',
                'required': True
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'questionText',
                'rows': '7',
                'placeholder': 'Опишите проблему подробно...',
                'maxlength': '5000',
                'required': True
            }),
        }
        
    def clean_tags_input(self):
        raw = self.cleaned_data.get("tags_input", "")
        tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
        
        pattern = re.compile(r"^[a-z0-9-]+$")
        for t in tags:
            if not pattern.match(t):
                raise forms.ValidationError(f"Тег '{t}' содержит недопустимые символы. Только латиница, цифры и дефисы.")
        
        if len(tags) > 10:
            raise forms.ValidationError("Максимум 10 тегов.")
        return tags
    
    def save(self, commit=True, author=None):
        instance = super().save(commit=False)
        instance.author = author
        if commit:
            with transaction.atomic():
                instance.save()
                for tag_name in self.cleaned_data.get("tags_input", []):
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    if created:
                        tag.color = generate_random_hex_color()
                        tag.save(update_fields=["color"])
                    instance.tags.add(tag)
        return instance


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["text"]
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '5',
                'placeholder': 'Напишите подробный ответ...',
                'required': True
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.errors.get("text"):
            existing_class = self.fields['text'].widget.attrs.get('class', '')
            self.fields['text'].widget.attrs['class'] = f"{existing_class} is-invalid".strip()
        
    def save(self, commit=True, question=None, author=None):
        instance = super().save(commit=False)
        instance.question = question
        instance.author = author
        if commit:
            instance.save()
        return instance