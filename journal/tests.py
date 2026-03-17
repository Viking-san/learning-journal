from unicodedata import category
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Entry, Tag, Comment, EntryLog
from django.db.utils import IntegrityError
from pprint import pprint


class CategoryModelTest(TestCase):
    """Тесты для модели Category"""
    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.category = Category.objects.create(name='Test Category')

    def test_slug_auto_generation(self):
        """Проверяем что slug создаётся автоматически"""
        self.assertEqual(self.category.slug, 'test-category')

    def test_category_str(self):
        """Проверяем что __str__ возвращает имя"""
        self.assertEqual(str(self.category), 'Test Category')

    def test_category_description(self):
        """Проверяем что описание пустое по умолчанию"""
        self.assertEqual(self.category.description, '')

    def test_category_ordering(self):
        """Проверяем что ordering идет по имени"""
        Category.objects.create(name='A first')
        Category.objects.create(name='Z last')
        Category.objects.create(name='B second')

        names = list(Category.objects.values_list('name', flat=True))
        self.assertEqual(names, ['A first', 'B second', 'Test Category', 'Z last'])


class TagModelTest(TestCase):
    """Тесты для модели Tag"""
    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.tag = Tag.objects.create(name='Test Tag')

    def test_tag_ordering(self):
        """Проверяем что ordering идет по имени"""
        Tag.objects.create(name='A first')
        Tag.objects.create(name='Z last')
        Tag.objects.create(name='B second')

        names = list(Tag.objects.values_list('name', flat=True))
        self.assertEqual(names, ['A first', 'B second', 'Test Tag', 'Z last'])

    def test_created_at_auto_populated(self):
        """Проверяем что created_at заполняется автоматически"""
        self.assertIsNotNone(self.tag.created_at)

    def test_slug_auto_generation(self):
        """Проверяем что slug создаётся автоматически"""
        self.assertEqual(self.tag.slug, 'test-tag')

    def test_tag_str(self):
        """Проверяем что __str__ возвращает имя"""
        self.assertEqual(str(self.tag), 'Test Tag')


class EntryModelTest(TestCase):
    """Тесты для модели Entry"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.category = Category.objects.create(name='Test')
        self.tag_a = Tag.objects.create(name='Tag a')
        self.tag_b = Tag.objects.create(name='Tag b')

    def test_entry_str(self):
        """Проверяем что __str__ возвращает корректную запись"""
        entry = Entry.objects.create(
            title='Entry title',
            content='content',
            category=self.category
        )
        self.assertEqual(str(entry), 'Entry title')

    def test_entry_creation(self):
        """Проверяем создание записи"""
        entry = Entry.objects.create(
            title='Entry creation check',
            content='content',
            category=self.category
        )
        self.assertEqual(entry.title, 'Entry creation check')
        self.assertEqual(entry.category, self.category)
        self.assertIsNotNone(entry.created_at)
        self.assertTrue(entry.is_published)

    def test_entry_without_category(self):
        """Проверяем что Entry не создается без category"""
        with self.assertRaises(IntegrityError):
            entry = Entry.objects.create(
                title='Entry creation without category check',
                content='content'
            )

    def test_entry_ordering(self):
        """Проверяем ordering отображения записей"""
        entry_a = Entry.objects.create(
            title='Test Entry',
            content='content',
            category=self.category
        )
        entry_b = Entry.objects.create(
            title='This one must be first Entry',
            content='content',
            category=self.category
        )
        titles = list(Entry.objects.values_list('title', flat=True))
        self.assertEqual(titles, ['This one must be first Entry', 'Test Entry'])

    def test_entry_tag_manytomany(self):
        """Проверяем что к Entry можно добавить несколько Tag"""
        entry = Entry.objects.create(
            title='Test Entry',
            content='content',
            category=self.category
        )
        entry.tags.add(self.tag_a, self.tag_b)
        self.assertEqual(entry.tags.all().count(), 2)
        self.assertIn(self.tag_a, entry.tags.all())
        self.assertIn(self.tag_b, entry.tags.all())


class CommentModelTest(TestCase):
    """Тесты для модели Comment"""
    def setUp(self):
        self.category = Category.objects.create(name='Test category')
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='content',
            category=self.category
        )
        self.comment = Comment.objects.create(author_name='Anon', content='Test', entry=self.entry)

    def test_comment_ordering(self):
        """Проверяем ordering отображения Comment"""
        comment_a = Comment.objects.create(
            author_name='Second author',
            content='content',
            entry=self.entry
        )
        comment_b = Comment.objects.create(
            author_name='First author',
            content='content',
            entry=self.entry
        )
        titles = list(Comment.objects.values_list('author_name', flat=True))
        self.assertEqual(titles, ['First author', 'Second author', 'Anon'])

    def test_comment_creation(self):
        """Проверка что comment создался корректно"""
        self.assertEqual(self.comment.author_name, 'Anon')
        self.assertEqual(self.comment.content, 'Test')
        self.assertIsNotNone(self.comment.created_at)

    def test_comment_str(self):
        """Проверяем что __str__ возвращает корректную запись"""
        self.assertEqual(str(self.comment), 'Комментарий от Anon к Test Entry')

    def test_comment_entry_foreignkey(self):
        """Проверка связи comment с Entry через ForeignKey"""
        self.assertEqual(self.comment.entry, self.entry)


class EntryLogModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test category')
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='content',
            category=self.category
        )
        self.entrylog_line = EntryLog.objects.create(
            entry=self.entry, 
            action='updated', 
            entry_title='Test title', 
            changed_entry_id=1
        )

    def test_entrylog_ordering(self):
        """Проверяем что ordering идет по дате - новые записи первые"""
        EntryLog.objects.create(
            entry=self.entry, action='created', 
            entry_title='First', changed_entry_id=10
        )
        EntryLog.objects.create(
            entry=self.entry, action='updated', 
            entry_title='Second', changed_entry_id=11
        )
        logs = list(EntryLog.objects.values_list('entry_title', flat=True))
        self.assertEqual(logs[0], 'Second')
        self.assertEqual(logs[1], 'First')

    def test_entrylog_creation(self):
        """Тест проверки корректно созданного EntryLog"""
        self.assertEqual(self.entrylog_line.action, 'updated')
        self.assertEqual(self.entrylog_line.changed_entry_id, 1)
        self.assertIsNotNone(self.entrylog_line.timestamp)

    def test_entrylog_str(self):
        """Проверяем что __str__ возвращает корректную запись"""
        expected = f'{self.entrylog_line.timestamp} - Test title - updated'
        self.assertEqual(str(self.entrylog_line), expected)
        
    def test_action_field(self):
        """Проверяем что важные значения action проходят без ошибок"""
        for i, action in enumerate(['created', 'updated', 'deleted'], 1):
            entrylog_line = EntryLog.objects.create(
            entry=self.entry, 
            action=action, 
            entry_title='Test title', 
            changed_entry_id=i
            )
            self.assertEqual(entrylog_line.action, action)


class EntryListViewTest(TestCase):
    """Тесты для главной страницы"""
    def setUp(self):
        self.response = self.client.get(reverse('journal:entry_list'))
        
        self.category = Category.objects.create(name='Test')
        self.django_entry = Entry.objects.create(
            title='Django entry',
            content='text',
            category=self.category)
        self.python_entry = Entry.objects.create(
            title='Python entry',
            content='text',
            category=self.category)

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


class EntryDetailViewTest(TestCase):
    """Тесты для страницы просмотра конкретной записи"""
    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.entry = Entry.objects.create(
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
            'author_name': 'test_entry_detail_view_post_method',
            'content': 'text'
        })
        
        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))
        comment = self.entry.comments.first()
        self.assertEqual(comment.author_name, 'test_entry_detail_view_post_method')
        self.assertEqual(self.entry.comments.count(), 1)


class EntryCreateViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test')
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
        self.entry = Entry.objects.create(
            title='Test entry',
            content='text',
            category=self.category
        )
        self.response = self.client.get(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}))

    def test_entry_update_view_status(self):
        """Проверяем что форма редактирования записи доступна"""        
        self.assertEqual(self.response.status_code, 200)

    def test_entry_update_view_template(self):
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




# class EntryAPITest(APITestCase):
#     """Тесты для API"""

#     def setUp(self):
#         self.category = Category.objects.create(name='API Test')
#         self.url = reverse('entry-list')

#     def test_create_entry_via_api(self):
#         """Проверяем создание записи через API"""
#         data = {
#             'title': 'API Entry',
#             'content': 'Created via API',
#             'category_id': self.category.id
#         }
#         response = self.client.post(self.url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Entry.objects.count(), 1)
#         self.assertEqual(Entry.objects.first().title, 'API Entry')
