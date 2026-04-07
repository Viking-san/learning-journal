from ..models import Category, Entry, Tag, Comment, EntryLog
from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth.models import User


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
        """Проверяем поведение description и что описание пустое по умолчанию"""
        description_text = 'Description text'
        category = Category.objects.create(name='New category', description=description_text)
        self.assertEqual(category.description, description_text)
        
        self.assertEqual(self.category.description, '')

    def test_category_ordering(self):
        """Проверяем что ordering идет по имени"""
        Category.objects.create(name='A first')
        Category.objects.create(name='Z last')
        Category.objects.create(name='B second')

        names = list(Category.objects.values_list('name', flat=True))
        self.assertEqual(
            names,
            ['A first',
            'B second',
            'General',
            'Test',
            'Test Category',
            'Z last',
            'Идея',
            'Личное',
            'Обучение',
            'Проблема',
            'Работа']
        )


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
        self.category = Category.objects.create(name='Test cat')
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

    def test_entry_category_filtering(self):
        """Проверяем фильтрацию по категориям"""
        second_category = Category.objects.create(name='second category')
        entry_a = Entry.objects.create(
            title='entry_a',
            content='content',
            category=self.category
        )
        entry_b = Entry.objects.create(
            title='entry_b',
            content='content',
            category=self.category
        )
        entry_c = Entry.objects.create(
            title='entry_c',
            content='content',
            category=second_category
        )
        entries = Entry.objects.by_category(self.category)
        self.assertIn(entry_a, entries)
        self.assertIn(entry_b, entries)
        self.assertNotIn(entry_c, entries)


class CommentModelTest(TestCase):
    """Тесты для модели Comment"""
    def setUp(self):
        self.category = Category.objects.create(name='Test category')
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='content',
            category=self.category
        )
        self.user = User.objects.create_user('test', password='pass')
        self.comment = Comment.objects.create(author_name=self.user, content='Test', entry=self.entry)

    def test_comment_ordering(self):
        """Проверяем ordering отображения Comment"""
        second_author = User.objects.create_user('Second author', password='pass')
        first_author = User.objects.create_user('First author', password='pass')

        comment_a = Comment.objects.create(
            author_name=second_author,
            content='content',
            entry=self.entry
        )
        comment_b = Comment.objects.create(
            author_name=first_author,
            content='content',
            entry=self.entry
        )
        titles = list(Comment.objects.values_list('author_name__username', flat=True))
        self.assertEqual(titles, ['First author', 'Second author', 'test'])

    def test_comment_creation(self):
        """Проверка что comment создался корректно"""
        self.assertEqual(str(self.comment.author_name), 'test')
        self.assertEqual(self.comment.content, 'Test')
        self.assertIsNotNone(self.comment.created_at)

    def test_comment_str(self):
        """Проверяем что __str__ возвращает корректную запись"""
        print(str(self.comment))
        self.assertEqual(str(self.comment), 'Комментарий от test к Test Entry')

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

