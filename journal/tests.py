from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Entry, Tag, Comment, EntryLog
from django.db.utils import IntegrityError


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
            action='created', 
            entry_title='Test title', 
            changed_entry_id=1
        )

    def test_entrylog_creation(self):
        """Тест проверки корректно созданного EntryLog"""
        self.assertEqual(self.entrylog_line.action, 'created')
        self.assertEqual(self.entrylog_line.changed_entry_id, 1)
        self.assertIsNotNone(self.entrylog_line.timestamp)

    def test_entrylog_str(self):
        """Проверяем что __str__ возвращает корректную запись"""
        line = str(self.entrylog_line).split(' - ', 1)[1]
        self.assertEqual(line, 'Test title - created')
        
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


# class EntryListViewTest(TestCase):
#     """Тесты для главной страницы"""

#     def test_entry_list_view_status(self):
#         """Проверяем что главная страница доступна"""
#         response = self.client.get(reverse('journal:entry_list'))
#         self.assertEqual(response.status_code, 200)


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
