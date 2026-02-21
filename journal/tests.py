from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Entry, Tag


class CategoryModelTest(TestCase):
    """Тесты для модели Category"""

    def test_slug_auto_generation(self):
        """Проверяем что slug создаётся автоматически"""
        category = Category.objects.create(name='Test Category')
        self.assertEqual(category.slug, 'test-category')

    def test_category_str(self):
        """Проверяем что __str__ возвращает имя"""
        category = Category.objects.create(name='Python')
        self.assertEqual(str(category), 'Python')


class EntryModelTest(TestCase):
    """Тесты для модели Entry"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.category = Category.objects.create(name='Test')

    def test_entry_creation(self):
        """Проверяем создание записи"""
        entry = Entry.objects.create(
            title='Test Entry',
            content='Test content',
            category=self.category
        )
        self.assertEqual(entry.title, 'Test Entry')
        self.assertEqual(entry.category, self.category)
        self.assertIsNotNone(entry.created_at)


class EntryListViewTest(TestCase):
    """Тесты для главной страницы"""

    def test_entry_list_view_status(self):
        """Проверяем что главная страница доступна"""
        response = self.client.get(reverse('journal:entry_list'))
        self.assertEqual(response.status_code, 200)


class EntryAPITest(APITestCase):
    """Тесты для API"""

    def setUp(self):
        self.category = Category.objects.create(name='API Test')
        self.url = reverse('entry-list')

    def test_create_entry_via_api(self):
        """Проверяем создание записи через API"""
        data = {
            'title': 'API Entry',
            'content': 'Created via API',
            'category_id': self.category.id
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Entry.objects.first().title, 'API Entry')
