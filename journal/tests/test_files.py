from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ..forms import ImportEntryForm, EntryForm
from ..models import Category, Entry, Tag
from django.contrib.auth.models import User
from django.urls import reverse
import frontmatter

class ExportEntryTest(TestCase):
    def setUp(self):        
        self.category = Category.objects.create(name='Test category')
        self.tag = Tag.objects.create(name='Test Tag')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.entry = Entry.objects.create(
            author=self.user,
            title = 'Test Entry',
            content = 'Test content',
            category = self.category,
        )
        self.entry.tags.add(self.tag)
        self.response = self.client.get(reverse('journal:export_entry', args=[self.entry.pk]))

    def test_correct_filename(self):
        """Проверка имени файла"""
        self.assertEqual(self.response.status_code, 200)
        self.assertIn('test-entry.md', self.response.get('Content-Disposition'))

    def test_content_in_downloaded_file(self):
        """Проверка содержимого файла"""
        content = self.response.content.decode('utf-8')
        port = frontmatter.loads(content)
        self.assertEqual(port.content, self.entry.content)
        self.assertEqual(port.metadata['title'], self.entry.title)
        self.assertIn(self.tag.name, port.metadata['tags'])


class UploadFileTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Category')
        self.tag = Tag.objects.create(name='test tag')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')

    def test_uploaded_file_with_frontmatter(self):
        """Проверка корректной загрузки файла с frontmatter"""
        md_content = b"---\ntitle: Test\ncategory: Category\ntags:\n  - test tag\n---\nContent"
        md_file = SimpleUploadedFile("test.md", md_content, content_type="text/markdown")

        self.client.post(reverse('journal:import_entry'), {'md_file': md_file})
        response = self.client.get(reverse('journal:entry_create'))
        form_data = response.context['form']

        self.assertEqual(form_data.initial['title'], 'Test')
        self.assertEqual(form_data.initial['category'], self.category)
        self.assertIn(self.tag, form_data.initial['tags'])
        self.assertEqual(form_data.initial['content'], 'Content')

    def test_uploaded_file_with_only_content(self):
        """Проверка коррекной загрузки файла с только содержимым"""
        md_content = b"Some content"
        md_file = SimpleUploadedFile("test.md", md_content, content_type="text/markdown")

        self.client.post(reverse('journal:import_entry'), {'md_file': md_file})
        response = self.client.get(reverse('journal:entry_create'))
        form_data = response.context['form']

        self.assertNotIn('title', form_data.initial)
        self.assertNotIn('category', form_data.initial)
        self.assertNotIn('tags', form_data.initial)
        self.assertEqual(form_data.initial['content'], 'Some content')

    def test_messages_displayed(self):
        """Проверка сообщений при загрузке файла с ошибками в frontmatter"""
        md_content = b"---\ntitle: Test\ncategory: Error\ntags:\n- error tag\n- test tag\n- second error tag\n---\nContent"
        md_file = SimpleUploadedFile("test.md", md_content, content_type="text/markdown")

        self.client.post(reverse('journal:import_entry'), {'md_file': md_file})
        response = self.client.get(reverse('journal:entry_create'))
        messages = list(response.wsgi_request._messages)

        self.assertEqual(len(messages), 2)
        self.assertEqual("Категория 'Error' не найдена, выберите из существующих.", str(messages[0]))
        self.assertIn("Следующие теги не найдены:", str(messages[1]))
        self.assertIn("error tag", str(messages[1]))
        self.assertIn("second error tag", str(messages[1]))
        self.assertNotIn("test tag", str(messages[1]))
