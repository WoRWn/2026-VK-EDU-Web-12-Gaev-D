from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from questions.models import Profile

User = get_user_model()

class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Логин или Email",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'loginInput',
            'placeholder': 'Введите логин или email',
            'autocomplete': 'username',
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
        identifier = cleaned_data.get("username_or_email")
        password = cleaned_data.get("password")
        
        if identifier and password:
            user = User.objects.filter(username=identifier).first()
            if not user:
                user = User.objects.filter(email=identifier).first()
            
            if user is None or not user.check_password(password):
                raise forms.ValidationError("Неверный логин/email или пароль")
            
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
        max_length=500,
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.errors.get('bio'):
            existing_class = self.fields['bio'].widget.attrs.get('class', '')
            self.fields['bio'].widget.attrs['class'] = f"{existing_class} is-invalid".strip()
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Этот логин уже занят.")
        return username
    
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
        Profile.objects.create(
            user=user,
            nickname=self.cleaned_data['nickname'],
            bio=self.cleaned_data.get('bio', ''),
            avatar=self.cleaned_data.get('avatar')
        )
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
        max_length=500,
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
                
        if self.errors.get('bio'):
            existing_class = self.fields['bio'].widget.attrs.get('class', '')
            self.fields['bio'].widget.attrs['class'] = f"{existing_class} is-invalid".strip()
                
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
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
        