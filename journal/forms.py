from django import forms
from .models import Entry, Comment
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm


class PasswordChangeForm(DjangoPasswordChangeForm):
    """Та же логика, что у стандартной формы Django, с Bootstrap-классами для полей."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['old_password'].label = 'Текущий пароль'
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
            'tags': forms.CheckboxSelectMultiple(),
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


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            # 'author_name': forms.TextInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': 'Ваше имя',
            # }),
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