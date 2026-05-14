from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from questions.models import Profile

import re
from questions.models import Answer, Question, Tag
from random import randint


User = get_user_model()

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'loginInput',
            'placeholder': 'Введите ваш логин',
            'autocomplete': 'username',
            'required': True
        })
    )
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'emailInput',
            'placeholder': 'example@mail.ru',
            'autocomplete': 'email',
            'required': True
        })
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'passwordInput',
            'placeholder': 'Введите пароль',
            'autocomplete': 'current-password',
            'required': True
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        
        if username and email and password:
            user = User.objects.filter(username=username, email=email).first()
            
            
            if user is None or not user.check_password(password):
                raise forms.ValidationError("Неверный логин, email или пароль")
            
            cleaned_data["user"] = user
        return cleaned_data
        
        
class SignUpForm(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'regLogin',
            'placeholder': 'Придумайте логин',
            'pattern': '[a-zA-Z0-9_]{3,30}',
            'required': True
        })
    )
    email = forms.EmailField(
        label="Email",
        max_length=255,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'regEmail',
            'placeholder': 'example@mail.ru',
            'required': True
        })
    )
    nickname = forms.CharField(
        label="Отображаемое имя",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'regNickname',
            'placeholder': 'Как вас будут видеть другие',
            'required': True
        })
    )
    bio = forms.CharField(
        label="О себе",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-lg',
            'id': 'regBio',
            'placeholder': 'Расскажите немного о себе...',
            'rows': 3
        })
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'regPassword',
            'placeholder': 'Минимум 8 символов',
            'required': True
        })
    )
    password2 = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'regPasswordRepeat',
            'placeholder': 'Повторите пароль',
            'required': True
        })
    )
    avatar = forms.ImageField(
        label="Аватар (опционально)",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'settingsAvatar',
            'accept': 'image/png, image/jpeg'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Этот логин уже занят.")
        return username
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get("nickname")
        if nickname and Profile.objects.filter(nickname=nickname).exists():
            raise forms.ValidationError("Этот никнейм уже занят.")
        return nickname
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже зарегистрирован.")
        return email
        
    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Файл слишком большой. Максимальный размер: 2 МБ.")
            extension = avatar.name.split(".")[-1].lower()
            if extension not in ["jpg", "jpeg", "png"]:
                raise forms.ValidationError("Недопустимый формат. Поддерживаются только JPG и PNG.")
        return avatar
    
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Пароли не совпадают.")
            
        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                for msg in e.messages:
                    self.add_error("password1", msg)
                    
        return cleaned_data
    
    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"]
        )
        try:
            Profile.objects.create(
                user=user,
                nickname=self.cleaned_data['nickname'],
                bio=self.cleaned_data.get('bio', ''),
                avatar=self.cleaned_data.get('avatar')
            )
        except Exception:
            user.delete()
        return user 
    
class ProfileForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'settingsEmail',
            'placeholder': 'mrfreeman@mail.ru',
            'required': True
        })
    )
    nickname = forms.CharField(
        label="Отображаемое имя",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'settingsNickname',
            'placeholder': 'Mr. Freeman',
            'required': True
        })
    )
    bio = forms.CharField(
        label="О себе",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-lg',
            'id': 'settingsBio',
            'placeholder': 'Расскажите немного о себе...',
            'rows': 3
        })
    )
    avatar = forms.ImageField(
        label="Аватар",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'settingsAvatar',
            'accept': 'image/png, image/jpeg'
        })
    )
    
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["email"].initial = user.email
            if hasattr(user, "profile"):
                self.fields["nickname"].initial = user.profile.nickname
                self.fields["bio"].initial = user.profile.bio
                
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Этот email уже используется.")
        return email
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Файл слишком большой. Максимальный размер: 2 МБ.")
            extension = avatar.name.split(".")[-1].lower()
            if extension not in ["jpg", "jpeg", "png"]:
                raise forms.ValidationError("Недопустимый формат. Поддерживаются только JPG и PNG.")
        return avatar
    
    def save(self):
        self.user.email = self.cleaned_data["email"]
        self.user.save()
        
        profile = self.user.profile
        profile.nickname = self.cleaned_data["nickname"]
        profile.bio = self.cleaned_data.get("bio", "")
        if self.cleaned_data.get("avatar"):
            profile.avatar = self.cleaned_data["avatar"]
        profile.save()
        
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
        if author:
            instance.author = author
        if commit:
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
        
    def save(self, commit=True, question=None, author=None):
        instance = super().save(commit=False)
        if question:
            instance.question = question
        if author:
            instance.author = author
        if commit:
            instance.save()
        return instance
    
def generate_random_hex_color():
    return f"#{randint(0, 0xFFFFFF):06X}"
        