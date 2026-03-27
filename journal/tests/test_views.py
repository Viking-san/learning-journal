from ..models import Category, Entry, Tag
from ..views import EntryListView, DraftListView
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class EntryListViewTest(TestCase):
    """Тесты для главной страницы"""
    def setUp(self):        
        self.category = Category.objects.create(name='Test')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.django_entry = Entry.objects.create(
            author=self.user,
            title='Django entry',
            content='text',
            category=self.category)
        self.python_entry = Entry.objects.create(
            author=self.user,
            title='Python entry',
            content='text',
            category=self.category)
        
        self.response = self.client.get(reverse('journal:entry_list'))

    def test_entry_list_view_status(self):
        """Проверяем что главная страница доступна"""
        self.assertEqual(self.response.status_code, 200)

    def test_entry_list_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/entry_list.html')

    def test_entry_list_view_context(self):
        """Проверяем что доступен нужный контекст"""
        self.assertIn('entries', self.response.context)
        self.assertIn('total_entries', self.response.context)
        self.assertIn('categories', self.response.context)
        self.assertIn('tags', self.response.context)

    def test_entry_list_view_filtration(self):
        """Проверяем фильтрацию в EntryListView"""
        response = self.client.get(reverse('journal:entry_list') + '?q=django')
        entries = response.context['entries']
        self.assertIn(self.django_entry, entries)
        self.assertNotIn(self.python_entry, entries)

    def test_entry_list_view_pagination(self):
        """Проверяем корректность paginate_by"""
        page_size = EntryListView.paginate_by

        for i in range(page_size + 1):
            Entry.objects.create(
                title=f'Entry {i}',
                content='text',
                category=self.category
            )

        response = self.client.get(reverse('journal:entry_list'))

        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['entries']), page_size)


class EntryDetailViewTest(TestCase):
    """Тесты для страницы просмотра конкретной записи"""
    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.entry = Entry.objects.create(
            author=self.user,
            title='Test entry',
            content='text',
            category=self.category)
        self.response = self.client.get(reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))

    def test_entry_deatil_view_status(self):
        """Проверяем что страница конкретной записи доступна"""
        self.assertEqual(self.response.status_code, 200)

    def test_entry_deatil_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/entry_detail.html')

    def test_entry_detail_view_context(self):
        """Проверяем что доступен нужный контекст"""
        self.assertIn('comments', self.response.context)
        self.assertIn('form', self.response.context)

    def test_entry_detail_view_post_method(self):
        """Проверяем что метод post отработал корректно"""
        response = self.client.post(reverse('journal:entry_detail', kwargs={'pk':self.entry.pk}), {
            'author_name': self.user,
            'content': 'test_entry_detail_view_post_method'
        })
        
        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))
        comment = self.entry.comments.first()
        self.assertEqual(comment.content, 'test_entry_detail_view_post_method')
        self.assertEqual(self.entry.comments.count(), 1)


class EntryCreateViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.response = self.client.get(reverse('journal:entry_create'))

    def test_entry_create_view_status(self):
        """Проверяем что форма создания записи доступна"""
        self.assertEqual(self.response.status_code, 200)

    def test_entry_create_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/entry_form.html')

    def test_entry_create_view_post_method(self):
        """Проверяем что метод post отработал корректно"""
        response = self.client.post(reverse('journal:entry_create'), {
            'title': 'test_entry_create_view_post_method',
            'content': 'Content',
            'category': self.category.id
        })
        
        entry = Entry.objects.get(title='test_entry_create_view_post_method')

        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': entry.pk}))
        self.assertEqual(entry.title, 'test_entry_create_view_post_method')
        self.assertEqual(Entry.objects.count(), 1)


class EntryUpdateViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.tag = Tag.objects.create(name='test tag')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.entry = Entry.objects.create(
            author=self.user,
            title='Test entry',
            content='text',
            category=self.category
        )
        self.response = self.client.get(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}))

    def test_entry_update_view_status(self):
        """Проверяем что форма редактирования записи доступна"""        
        self.assertEqual(self.response.status_code, 200)

    def test_published_entry_update_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/entry_form.html')

    def test_entry_update_view_post_method(self):
        """Проверяем что метод post отработал корректно"""
        new_title = 'Новый title'
        response = self.client.post(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}), {
            'title': new_title,
            'content': self.entry.content,
            'category': self.category.id
        })
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, new_title)
        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))


class DraftListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.category = Category.objects.create(name='Test category')
        self.response = self.client.get(reverse('journal:drafts'))

    def test_draft_list_view_status(self):
        """Проверяем что страница с черновиками доступна"""        
        self.assertEqual(self.response.status_code, 200)

    def test_unpublished_entry_update_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/draft_list.html')

    def test_entry_list_view_context(self):
        """Проверяем что доступен нужный контекст"""
        self.assertIn('total_drafts', self.response.context)

    def test_draft_list_view_filtration(self):
        """Проверяем что в DraftListView попадают только не опубликованные записи"""
        
        public_entry = Entry.objects.create(
            author=self.user,
            title='Public Entry',
            content='Text',
            category=self.category,
            is_published=True
        )
        draft_entry = Entry.objects.create(
            author=self.user,
            title='Draft Entry',
            content='Text',
            category=self.category,
            is_published=False
        )

        response = self.client.get(reverse('journal:drafts'))
        drafts_list = response.context['drafts']

        self.assertIn(draft_entry, drafts_list)
        self.assertNotIn(public_entry, drafts_list)
        self.assertEqual(drafts_list.count(), 1)

    def test_draft_list_view_pagination(self):
        """Проверяем корректность paginate_by"""
        page_size = DraftListView.paginate_by

        for i in range(page_size + 1):
            Entry.objects.create(
                author=self.user,
                title=f'Draft Entry {i}',
                content='text',
                category=self.category,
                is_published=False
            )

        response = self.client.get(reverse('journal:drafts'))

        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['drafts']), page_size)
