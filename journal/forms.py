from django import forms
from .models import Entry, Comment


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['title', 'content', 'category', 'tags', 'image']
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
        }


# class CommentForm(forms.ModelForm):
#     class Meta:
#         model = Comment
#         fields = ['author_name', 'content']
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['author_name', 'content']
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Текст комментария',
                'rows': 4,
            }),
        }
        labels = {
            'author_name': 'Имя автора',
            'content': 'Комментарий',
        }