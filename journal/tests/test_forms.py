from ..models import Category, Entry, Tag
from ..forms import EntryForm, CommentForm
from django.test import TestCase



class EntryFormTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test category')

    def test_form_is_valid(self):
        """Проверка валидности формы"""
        form_data = {
            'title': 'Test Entry',
            'content': 'text',
            'category': self.category,
            'is_published': True
        }
        form = EntryForm(data=form_data)

        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Entry.objects.count(), 1)

    def test_form_without_required_fields(self):
        """Проверка ошибки формы если забыть обязательные поля"""
        form_data = {
            'title': 'Test Entry',
            'content': 'text'
        }
        form = EntryForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_defaults(self):
        """Проверка поведения is_published default при создании через форму"""
        form_data = {
            'title': 'test_form_defaults',
            'content': 'text',
            'category': self.category,
        }
        form = EntryForm(data=form_data)

        self.assertTrue(form.is_valid())        
        form.save()
        # В модели Entry по умолчанию is_published=True,
        # но при создании через форму, если checkbox не активен, 
        # а он не активен если не передать явно, то он будет False
        self.assertFalse(Entry.objects.get(title='test_form_defaults').is_published)

    def test_form_tags(self):
        """Проверка ManyToMany при создании через форму"""
        tag = Tag.objects.create(name='Test Tag')
        form_data = {
            'title': 'test_form_tags',
            'content': 'text',
            'category': self.category,
            'tags': [tag]
        }
        form = EntryForm(data=form_data)

        self.assertTrue(form.is_valid())        
        form.save()
        entry_tags = Entry.objects.get(title='test_form_tags').tags.all()
        self.assertIn(tag, entry_tags)


class CommentFormTest(TestCase):
    def test_form_is_valid(self):
        """Проверка валидности формы"""
        form_data = {
            'author_name': 'Anon',
            'content': 'Comment text'
        }
        form = CommentForm(data=form_data)        
        self.assertTrue(form.is_valid())

    def test_form_without_required_fields(self):
        """Проверка ошибки формы если забыть обязательные поля"""
        form_data = {
            'author_name': 'Anon',
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
