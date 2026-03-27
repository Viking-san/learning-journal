from ..models import Category, Entry, EntryLog
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from django.contrib.auth.models import User


class SignalsTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test category')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='text',
            category=self.category,
            author=self.user
        )

        self.entrylog_lines = EntryLog.objects.count()

    def test_signal_creation_entrylog(self):
        """Проверяем что при создании Entry в лог попадает action=created"""
        self.assertEqual(EntryLog.objects.count(), self.entrylog_lines)

        entry = Entry.objects.create(
            title='test_signal_creation_entrylog',
            content='text',
            category=self.category
        )

        self.assertEqual(EntryLog.objects.count(), self.entrylog_lines + 1)
        log = EntryLog.objects.get(entry__title='test_signal_creation_entrylog')
        self.assertEqual(log.action, 'created')
        self.assertEqual(log.changed_entry_id, entry.pk)

    def test_signal_updating_entrylog(self):
        """Проверяем что при изменении Entry в лог попадает action=updated"""
        self.assertEqual(EntryLog.objects.count(), self.entrylog_lines)

        self.client.post(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}), {
            'title': 'test_signal_updating_entrylog',
            'content': self.entry.content,
            'category': self.category.id
        })

        self.assertEqual(EntryLog.objects.count(), self.entrylog_lines + 1)
        log = EntryLog.objects.get(entry_title='test_signal_updating_entrylog')
        self.assertEqual(log.action, 'updated')
        self.assertEqual(log.changed_entry_id, self.entry.pk)
        
    def test_signal_deleting_entrylog(self):
        """Проверяем что при удалении Entry в лог попадает action=deleted"""
        self.assertEqual(EntryLog.objects.count(), self.entrylog_lines)
        entry_id = self.entry.pk
        self.entry.delete()
        
        self.assertEqual(EntryLog.objects.count(), self.entrylog_lines + 1)
        log = EntryLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'deleted')
        self.assertEqual(log.changed_entry_id, entry_id)

    @patch('journal.signals.print')
    def test_signal_prints_log_message(self, mock_print):
        """Signal печатает сообщение при создании Entry"""
        
        user = User.objects.create_user('user', password='pass')
        self.client.login(username='user', password='pass')
        entry = Entry.objects.create(
            author=user,
            title='Test',
            content='Content',
            category=self.category
        )
        # Проверяем что print был вызван с правильным сообщением
        mock_print.assert_called_with(f'[log] {entry.title} - created')

        self.client.post(reverse('journal:entry_update', kwargs={'pk': entry.pk}), {
            'author': user,
            'title': 'test_signal_prints_log_message',
            'content': self.entry.content,
            'category': self.category.id
        })
        entry.refresh_from_db()
        mock_print.assert_called_with(f'[log] {entry.title} - updated')

        entry_title = entry.title
        entry.delete()
        mock_print.assert_called_with(f'[log] {entry_title} - deleted')

