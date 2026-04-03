from django import forms
from django.forms import widgets
from .models import Entry, Comment
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class ImportEntryForm(forms.Form):
    md_file = forms.FileField(
        label='Markdown файл',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.md'})
    )


class CustomUserCreationForm(UserCreationForm):
    """Расширенная форма для регистрации с email"""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['email'].label = 'Электронная почта'

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже используется')
        return email


class PasswordChangeForm(DjangoPasswordChangeForm):
    """Та же логика, что у стандартной формы Django, с Bootstrap-классами для полей."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['old_password'].label = 'Текущий пароль'
        self.fields['new_password1'].label = 'Новый пароль'
        self.fields['new_password2'].label = 'Подтверждение нового пароля'


class PasswordResetForm(DjangoPasswordResetForm):
    """Та же логика, что у стандартной формы Django, с Bootstrap-классами для полей."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['email'].label = 'Электронная почта'


class SetPasswordForm(DjangoSetPasswordForm):
    """Та же логика, что у стандартной формы Django, с Bootstrap-классами для полей."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['new_password1'].label = 'Новый пароль'
        self.fields['new_password2'].label = 'Подтверждение нового пароля'


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['title', 'content', 'category', 'tags', 'image', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок записи'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Что изучили сегодня?'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.SelectMultiple(),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_published': 'Опубликовать',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_published'].initial = True


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Текст комментария',
                'rows': 10,
            }),
        }
        labels = {
            'author_name': 'Имя автора',
            'content': 'Комментарий',
        }